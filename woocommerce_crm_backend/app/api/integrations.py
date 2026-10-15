import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.schemas.dashboard import WooStatusResponse, WooSyncResponse
from app.services.seed import seed_demo_data
from app.services.woocommerce import (
    WooCommerceError,
    get_sync_state,
    is_configured,
    key_hint,
    sync_store,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/integrations/woocommerce", tags=["integrations"])


@router.get("/status", response_model=WooStatusResponse)
def woo_status(db: Session = Depends(get_db)):
    settings = get_settings()
    state = get_sync_state(db)
    configured = is_configured()
    return {
        # Never return secrets — only a masked hint + configured flag.
        "configured": configured,
        "mode": "live" if configured else "demo",
        "store_url": settings.WC_STORE_URL or None,
        "key_hint": key_hint(),
        "last_sync_at": state.last_sync_at if state else None,
        "customers_synced": state.customers_synced if state else 0,
        "orders_synced": state.orders_synced if state else 0,
        "message": state.message if state else None,
    }


@router.post("/sync", response_model=WooSyncResponse)
def woo_sync(db: Session = Depends(get_db)):
    from datetime import datetime

    if is_configured():
        try:
            result = sync_store(db)
        except WooCommerceError as exc:
            logger.warning("Live sync failed: %s", exc)
            return {
                "ok": False,
                "mode": "live",
                "customers_synced": 0,
                "orders_synced": 0,
                "message": str(exc),
                "last_sync_at": None,
            }
        state = get_sync_state(db)
        return {
            "ok": True,
            "mode": "live",
            "customers_synced": result["customers_synced"],
            "orders_synced": result["orders_synced"],
            "message": f"Live sync complete: {result['customers_synced']} customers, "
            f"{result['orders_synced']} orders.",
            "last_sync_at": state.last_sync_at if state else datetime.utcnow(),
        }
    else:
        # Demo mode: load realistic sample data, honestly labelled as demo.
        result = seed_demo_data(db)
        state = get_sync_state(db)
        return {
            "ok": True,
            "mode": "demo",
            "customers_synced": result.get("customers_synced", 0),
            "orders_synced": result.get("orders_synced", 0),
            "message": result.get("message", "Demo data loaded."),
            "last_sync_at": state.last_sync_at if state else datetime.utcnow(),
        }
