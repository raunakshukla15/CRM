# WooCommerce CRM Backend (FastAPI + MySQL)

Production-grade CRM backend that ingests WooCommerce webhooks
(`customer.created/updated`, `order.created/updated`), maintains customer
aggregates + VIP promotion, sends automated emails, and exposes management REST APIs.

## 1. Quickstart (local, SQLite-free — needs MySQL)

```bash
cd woocommerce_crm_backend
python -m venv .venv && .venv/Scripts/activate   # Windows
pip install -r requirements.txt

copy .env.example .env   # then edit WC_WEBHOOK_SECRET + DATABASE_URL
# Example local DATABASE_URL:
# DATABASE_URL=mysql+pymysql://crm_user:change_me_strong_password@127.0.0.1:3306/woocommerce_crm

# Create DB (once):
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS woocommerce_crm CHARACTER SET utf8mb4; \
  CREATE USER IF NOT EXISTS 'crm_user'@'%' IDENTIFIED BY 'change_me_strong_password'; \
  GRANT ALL ON woocommerce_crm.* TO 'crm_user'@'%'; FLUSH PRIVILEGES;"

alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Health checks: `GET http://127.0.0.1:8000/health`, `GET /ready` (DB ping).
Interactive docs: `http://127.0.0.1:8000/docs`.

## 2. Local testing with ngrok (mock payloads)

Terminal 1 — API:

```bash
uvicorn app.main:app --port 8000
```

Terminal 2 — public URL:

```bash
ngrok http 8000
# -> https://<subdomain>.ngrok-free.app
```

Terminal 3 — fire signed webhooks (full flow: customer → order → completed → VIP):

```bash
# .env WEBHOOK_SKIP_SIGNATURE must be false (default) — script signs requests.
python scripts/test_webhooks.py --base-url http://127.0.0.1:8000 --secret <WC_WEBHOOK_SECRET>
# Or against the ngrok URL (this is the URL you put into WooCommerce):
python scripts/test_webhooks.py --base-url https://<subdomain>.ngrok-free.app --secret <WC_WEBHOOK_SECRET>

# Single event:
python scripts/test_webhooks.py --base-url http://127.0.0.1:8000 --secret <secret> \
  --topic order.updated --payload scripts/mock_payloads/order_updated_completed.json
```

Expected results:

| Step | Effect |
|---|---|
| `customer.created` | New `customers` row + `WELCOME_EMAIL` row in `communication_logs` |
| `order.created` (processing) | New `orders` row, `total_spend`/`lifetime_orders` recalculated |
| `order.updated` → `completed` | Status flips + `ORDER_COMPLETED_EMAIL` logged |
| second completed order ($250) | `total_spend` = 570.00 → `customer_status` auto-promotes to `VIP` |

Verify:

```bash
curl "http://127.0.0.1:8000/api/v1/customers?search=jane"
curl "http://127.0.0.1:8000/api/v1/customers/1"
curl "http://127.0.0.1:8000/api/v1/orders?status=completed"
curl -X POST http://127.0.0.1:8000/api/v1/customers/1/notes \
  -H "Content-Type: application/json" -d '{"note":"Called, wants invoice.","created_by":"admin"}'
```

Idempotency: re-sending the same payload updates (never duplicates) — keyed on
`woocommerce_customer_id` / `woocommerce_order_id` unique constraints.

## 3. Production deployment (Docker Compose + Nginx + Certbot SSL)

Prereqs: Ubuntu 22.04+ VM, DNS `A` record `crm.example.com -> <server IP>`, ports 80/443 open.

```bash
scp -r woocommerce_crm_backend user@server:/opt/
ssh user@server && cd /opt/woocommerce_crm_backend
cp .env.example .env   # fill REAL secrets + SMTP creds
sed -i 's/crm.example.com/<your-domain>/g' nginx.conf docker-compose.yml 2>/dev/null || true
# edit nginx.conf server_name + ssl_certificate paths to your domain
docker compose up -d --build db
docker compose up -d --build api     # runs `alembic upgrade head` automatically
docker compose up -d nginx certbot
```

### 3a. Issue SSL (Let's Encrypt, one-time)

```bash
DOMAIN=crm.example.com
EMAIL=admin@example.com
docker compose run --rm certbot certonly --webroot -w /var/www/certbot \
  -d $DOMAIN --email $EMAIL --agree-tos --no-eff-email
docker compose restart nginx
curl -s https://$DOMAIN/health
```

Renewal runs automatically via the `certbot` service loop (`certbot renew` every 12h).
Certificates persist in `./certbot/conf`.

### 3b. Useful ops commands

```bash
docker compose ps
docker compose logs -f api nginx db
docker compose exec api alembic upgrade head
docker compose exec db mysql -u root -p -e "SHOW TABLES;" woocommerce_crm
```

## 4. Configure webhooks in WordPress / WooCommerce Admin

1. WordPress Admin → **WooCommerce → Settings → Advanced → Webhooks → Add webhook**.
2. Create **four** webhooks (repeat per topic):

   | Field | Value |
   |---|---|
   | Name | `CRM - Customer Created` (etc.) |
   | Status | Active |
   | Topic | `Customer created` / `Customer updated` / `Order created` / `Order updated` |
   | Delivery URL | `https://crm.example.com/api/v1/webhooks/woocommerce` (or ngrok URL for testing) |
   | Secret | paste the **same** value as `WC_WEBHOOK_SECRET` in `.env` (min 32 chars) |
   | API Version | WP REST API v3 |

3. Click **Save** → WooCommerce fires a ping; check `docker compose logs -f api` for
   `Webhook received: topic=...`. A non-2xx/signature error shows in
   WooCommerce → **Logs** (each webhook row shows recent delivery attempts).
4. HMAC note: WooCommerce signs the raw JSON body with your secret (base64 HMAC-SHA256)
   in header `X-WC-Webhook-Signature`. This backend rejects mismatches with `401`.
   If you rotate the secret, update **both** `.env` and all four WooCommerce webhooks.
5. Troubleshooting:
   - `401 Invalid webhook signature` → secret mismatch (trailing spaces are the #1 cause).
   - `400 Unsupported webhook topic` → only the 4 topics above are handled; action/scheduled webhooks are ignored by design.
   - `422 ...` → payload missing email/id (e.g. deleted customer); check API logs.

## 5. API reference

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/webhooks/woocommerce` | WooCommerce ingestion (HMAC) |
| `GET` | `/api/v1/customers?page=&page_size=&status=&min_spend=&search=` | List/filter customers |
| `GET` | `/api/v1/customers/{id}` | Profile + orders + comms + notes |
| `POST` | `/api/v1/customers/{id}/notes` | Add admin note `{"note","created_by"}` |
| `GET` | `/api/v1/customers/{id}/notes` | List notes (extra) |
| `GET` | `/api/v1/orders?page=&page_size=&customer_id=&status=` | List orders |
| `GET` | `/health`, `/ready` | Liveness / DB readiness |

## 6. Project structure

```
app/main.py                 FastAPI factory, /health, /ready, router wiring
app/api/webhooks.py         HMAC gate + topic dispatch
app/api/customers.py        list/detail/notes
app/api/orders.py           list w/ filters
app/core/config.py          Pydantic Settings (.env)
app/core/database.py        SQLAlchemy engine + get_db
app/models/                 customers / orders / communication_logs / customer_notes
app/services/security.py    HMAC-SHA256 helpers
app/services/crm_service.py idempotent upserts, aggregates, VIP rule
app/services/email_sender.py SMTP + log-only fallback
alembic/versions/0001_initial.py
scripts/mock_payloads/*.json + scripts/test_webhooks.py
docker-compose.yml / Dockerfile / nginx.conf
```

## 7. Security notes

- Never commit `.env`; rotate `WC_WEBHOOK_SECRET`, MySQL passwords, SMTP creds per env.
- Nginx terminates TLS; FastAPI only listens on the internal `crm_net` network.
- `WEBHOOK_SKIP_SIGNATURE` must stay `false` in production.
