"""WooCommerce webhook entrypoint — HMAC verified, idempotent ingestion."""

import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.services.crm_service import upsert_customer_from_webhook, upsert_order_from_webhook
from app.services.security import verify_signature

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["webhooks"])

CUSTOMER_TOPICS = {"customer.created", "customer.updated"}
ORDER_TOPICS = {"order.created", "order.updated"}


@router.post("/woocommerce", status_code=200)
async def woocommerce_webhook(
    request: Request,
    db: Session = Depends(get_db),
    signature: str | None = Header(default=None, alias="X-WC-Webhook-Signature"),
    topic: str | None = Header(default=None, alias="X-WC-Webhook-Topic"),
    source: str | None = Header(default=None, alias="X-WC-Webhook-Source"),
):
    settings = get_settings()
    raw_body = await request.body()

    # --- Security: HMAC-SHA256 verification ---
    if not settings.WEBHOOK_SKIP_SIGNATURE:
        if not verify_signature(raw_body, settings.WC_WEBHOOK_SECRET, signature):
            logger.warning("Rejected webhook: bad signature (source=%s topic=%s)", source, topic)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature",
            )
    elif not signature:
        logger.debug("WEBHOOK_SKIP_SIGNATURE=true — accepting unsigned webhook for local test")

    # --- Parse JSON ---
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Webhook payload must be a JSON object")

    # WooCommerce may send topic in header or in body arg; normalize
    event = (topic or payload.get("topic") or "").strip().lower()
    logger.info("Webhook received: topic=%s source=%s", event, source)

    try:
        if event in CUSTOMER_TOPICS:
            customer, created = upsert_customer_from_webhook(db, payload)
            db.commit()
            return {
                "ok": True,
                "event": event,
                "customer_id": customer.id,
                "created": created,
            }
        elif event in ORDER_TOPICS:
            order, customer, order_created, became_completed = upsert_order_from_webhook(
                db, payload
            )
            db.commit()
            return {
                "ok": True,
                "event": event,
                "order_id": order.id,
                "woocommerce_order_id": order.woocommerce_order_id,
                "customer_id": customer.id,
                "created": order_created,
                "order_completed_email_sent": became_completed,
            }
        else:
            logger.warning("Ignoring unsupported webhook topic: %r", event)
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported webhook topic: {event!r}. "
                f"Supported: {sorted(CUSTOMER_TOPICS | ORDER_TOPICS)}",
            )
    except HTTPException:
        db.rollback()
        raise
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception:
        db.rollback()
        logger.exception("Webhook processing failed")
        raise HTTPException(status_code=500, detail="Webhook processing failed")
