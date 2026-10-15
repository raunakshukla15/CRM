"""Local webhook tester — signs mock payloads and POSTs them to the API.

Usage (from repo root):
    python scripts/test_webhooks.py --base-url http://127.0.0.1:8000 --secret <WC_WEBHOOK_SECRET>
    python scripts/test_webhooks.py --topic order.created --payload scripts/mock_payloads/order_created.json

With ngrok:
    1. uvicorn app.main:app --port 8000
    2. ngrok http 8000   ->  https://<sub>.ngrok-free.app
    3. python scripts/test_webhooks.py --base-url https://<sub>.ngrok-free.app --secret <secret>
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import sys
from pathlib import Path

try:
    import httpx
except ImportError:
    print("httpx is required: pip install -r requirements.txt", file=sys.stderr)
    raise SystemExit(1)

MOCK_DIR = Path(__file__).parent / "mock_payloads"

DEFAULT_FLOW: list[tuple[str, str]] = [
    ("customer.created", "customer_created.json"),
    ("customer.updated", "customer_updated.json"),
    ("order.created", "order_created.json"),
    ("order.updated", "order_updated_completed.json"),
    ("order.created", "order_vip_trigger.json"),  # pushes total to 570 -> VIP
]


def sign(raw: bytes, secret: str) -> str:
    return base64.b64encode(hmac.new(secret.encode(), raw, hashlib.sha256).digest()).decode()


def post_topic(base_url: str, topic: str, payload_file: Path, secret: str) -> None:
    raw = payload_file.read_bytes()
    # Re-serialize to canonical bytes actually sent
    body = json.loads(raw)
    canonical = json.dumps(body).encode()
    headers = {
        "Content-Type": "application/json",
        "X-WC-Webhook-Topic": topic,
        "X-WC-Webhook-Signature": sign(canonical, secret),
        "X-WC-Webhook-Source": "local-mock-script",
    }
    url = base_url.rstrip("/") + "/api/v1/webhooks/woocommerce"
    print(f"\n>>> {topic}  {payload_file.name} -> {url}")
    resp = httpx.post(url, content=canonical, headers=headers, timeout=15)
    print(f"<<< {resp.status_code} {resp.text[:1000]}")
    resp.raise_for_status()


def main() -> None:
    parser = argparse.ArgumentParser(description="Test WooCommerce webhooks locally")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--secret", default="change_me_webhook_secret_min_32_chars")
    parser.add_argument("--topic", default=None, help="Single topic to send")
    parser.add_argument("--payload", default=None, help="Payload JSON file for single send")
    parser.add_argument("--list", action="store_true", help="Verify management APIs after ingest")
    args = parser.parse_args()

    if args.topic and args.payload:
        post_topic(args.base_url, args.topic, Path(args.payload), args.secret)
    else:
        for topic, filename in DEFAULT_FLOW:
            post_topic(args.base_url, topic, MOCK_DIR / filename, args.secret)

    if args.list or True:
        for path in ("/api/v1/customers?search=jane", "/api/v1/orders?status=completed"):
            url = args.base_url.rstrip("/") + path
            r = httpx.get(url, timeout=15)
            print(f"\n>>> GET {path}\n<<< {r.status_code} {r.text[:1500]}")


if __name__ == "__main__":
    main()
