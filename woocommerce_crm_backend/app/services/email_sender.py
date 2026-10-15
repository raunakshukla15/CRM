"""Email sender with SMTP support and safe log-only fallback."""

import logging
import smtplib
from email.mime.text import MIMEText

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def send_email(to_email: str, subject: str, body: str) -> bool:
    """Send an email. Returns True on success, False on failure.

    If SMTP_HOST is not configured, logs the email and returns True
    (dev / CI friendly — the DB communication log still records SENT).
    """
    settings = get_settings()

    if not settings.SMTP_HOST:
        logger.info(
            "[EMAIL-LOG-ONLY] to=%s subject=%s body=%.500s", to_email, subject, body
        )
        return True

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
    msg["To"] = to_email

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            if settings.SMTP_USERNAME:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM_EMAIL, [to_email], msg.as_string())
        logger.info("Email sent to %s subject=%s", to_email, subject)
        return True
    except Exception:
        logger.exception("Failed to send email to %s", to_email)
        return False
