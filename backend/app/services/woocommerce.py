"""WooCommerce REST API client + sync logic (server-side only).

Uses the official WooCommerce REST API v3:
  GET {store_url}/wp-json/wc/v3/customers
  GET {store_url}/wp-json/wc/v3/orders
with HTTP Basic auth (consumer_key:consumer_secret).

Secrets never leave the backend — status endpoints only return a masked hint.
"""

import logging
from datetime import datetime
from decimal import Decimal

import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.sync_state import SyncState
from app.services.crm_service import (
    recalc_customer_aggregates,
    upsert_customer_from_webhook,
    upsert_order_from_webhook,
)

logger = logging.getLogger(__name__)

PER_PAGE = 100
MAX_PAGES = 10


class WooCommerceError(Exception):
    pass


def is_configured() -> bool:
    s = get_settings()
    return bool(s.WC_STORE_URL and s.WC_CONSUMER_KEY and s.WC_CONSUMER_SECRET)


def key_hint() -> str | None:
    s = get_settings()
    if not s.WC_CONSUMER_KEY:
        return None
    key = s.WC_CONSUMER_KEY
    return f"{key[:4]}…{key[-4:]}" if len(key) > 8 else "****"


def derive_payment_status(wc_status: str) -> str:
    s = (wc_status or "").lower()
    if s in ("completed", "processing"):
        return "paid"
    if s in ("on-hold", "pending"):
        return "pending"
    if s == "refunded":
        return "refunded"
    if s in ("cancelled", "failed"):
        return "failed"
    return "pending"


def derive_fulfillment_status(wc_status: str) -> str:
    s = (wc_status or "").lower()
    if s == "completed":
        return "fulfilled"
    if s == "processing":
        return "partial"
    if s in ("cancelled", "refunded", "failed"):
        return "cancelled"
    return "unfulfilled"


def _client() -> httpx.Client:
    s = get_settings()
    base = s.WC_STORE_URL.rstrip("/")
    if not base.startswith(("http://", "https://")):
        raise WooCommerceError("WC_STORE_URL must start with http:// or https://")
    try:
        return httpx.Client(
            base_url=f"{base}/wp-json/wc/v3",
            auth=(s.WC_CONSUMER_KEY, s.WC_CONSUMER_SECRET),
            timeout=20.0,
        )
    except Exception as exc:
        raise WooCommerceError(f"Could not create API client: {exc}") from exc


def _fetch_all(client: httpx.Client, resource: str) -> list[dict]:
    """Paginate through a WC REST collection (caps at MAX_PAGES)."""
    items: list[dict] = []
    for page in range(1, MAX_PAGES + 1):
        try:
            resp = client.get(resource, params={"per_page": PER_PAGE, "page": page})
        except httpx.ConnectError as exc:
            raise WooCommerceError(f"Cannot reach store: {exc}") from exc
        except httpx.TimeoutException as exc:
            raise WooCommerceError(f"Store request timed out: {exc}") from exc
        except httpx.HTTPError as exc:
            raise WooCommerceError(f"Network error talking to store: {exc}") from exc
        if resp.status_code == 401:
            raise WooCommerceError("Invalid WooCommerce credentials (401). Check key/secret.")
        if resp.status_code == 404:
            raise WooCommerceError(
                "WooCommerce API not found (404). Is WooCommerce active and is the URL correct?"
            )
        if resp.status_code >= 400:
            raise WooCommerceError(f"Store API error {resp.status_code}: {resp.text[:300]}")
        try:
            batch = resp.json()
        except ValueError as exc:
            raise WooCommerceError("Store returned non-JSON response") from exc
        if not isinstance(batch, list) or not batch:
            break
        items.extend(batch)
        total_pages = int(resp.headers.get("X-WP-TotalPages", "1") or "1")
        if page >= total_pages:
            break
    return items


def map_order_for_crm(wc_order: dict) -> dict:
    """Normalize a WC REST order into the webhook-shaped payload our upsert expects."""
    payload = dict(wc_order)
    payload["status"] = str(wc_order.get("status") or "pending")
    # WC REST uses strings for totals; upsert coerces to Decimal already.
    return payload


def _claim(owner_id: int | None, row) -> bool:
    """Assign an ownerless synced row to the syncing user. Never touch others' rows."""
    if owner_id is not None and getattr(row, "owner_id", None) is None:
        row.owner_id = owner_id
        return True
    return owner_id is None or getattr(row, "owner_id", None) == owner_id


def sync_store(db: Session, owner_id: int | None = None) -> dict:
    """Pull customers + orders from the live store. Raises WooCommerceError on failure."""
    if not is_configured():
        raise WooCommerceError("WooCommerce credentials are not configured (demo mode).")

    customers_synced = 0
    orders_synced = 0
    with _client() as client:
        wc_customers = _fetch_all(client, "customers")
        for wc in wc_customers:
            try:
                customer, _ = upsert_customer_from_webhook(db, wc)
                if _claim(owner_id, customer):
                    customers_synced += 1
            except ValueError:
                logger.warning("Skipping customer without email/id: %s", wc.get("id"))
        db.flush()

        wc_orders = _fetch_all(client, "orders")
        for wc in wc_orders:
            try:
                order, customer, _, _ = upsert_order_from_webhook(db, map_order_for_crm(wc))
                if not _claim(owner_id, order):
                    continue  # belongs to another user — do not touch
                _claim(owner_id, customer)
                # Enrich derived payment/fulfillment status from WC status
                order.payment_status = derive_payment_status(order.status)
                order.fulfillment_status = derive_fulfillment_status(order.status)
                recalc_customer_aggregates(db, customer)
                orders_synced += 1
            except ValueError:
                logger.warning("Skipping order without customer info: %s", wc.get("id"))
        db.flush()

    # Backfill derived statuses for older rows missing them
    from sqlalchemy import select
    from app.models.order import Order

    for order in db.scalars(select(Order)).all():
        if not getattr(order, "payment_status", None):
            order.payment_status = derive_payment_status(order.status)
        if not getattr(order, "fulfillment_status", None):
            order.fulfillment_status = derive_fulfillment_status(order.status)

    _record_sync(db, mode="live", customers=customers_synced, orders=orders_synced,
                 message=f"Live sync OK: {customers_synced} customers, {orders_synced} orders")
    db.commit()
    return {
        "mode": "live",
        "customers_synced": customers_synced,
        "orders_synced": orders_synced,
    }


def _record_sync(
    db: Session, mode: str, customers: int, orders: int, message: str
) -> SyncState:
    state = db.get(SyncState, 1)
    if state is None:
        state = SyncState(id=1)
        db.add(state)
    state.last_sync_at = datetime.utcnow()
    state.mode = mode
    state.customers_synced = customers
    state.orders_synced = orders
    state.message = message
    db.flush()
    return state


def get_sync_state(db: Session) -> SyncState | None:
    return db.get(SyncState, 1)
