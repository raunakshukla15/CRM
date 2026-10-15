# KilloKart — Deploy Guide (Netlify + Render + WooCommerce)

Target architecture:

```
WooCommerce store ──REST API──▶ Render API (FastAPI + MySQL) ◀──Axios── Netlify site (React)
                    ──webhooks─▶  https://killokart-api.onrender.com      https://killokart.netlify.app
```

**Do Render first, Netlify second, WooCommerce keys any time before the live sync.**
The site works without WooCommerce (demo mode), but live data needs the keys.

---

## What you must provide (your checklist)

| # | Item | Where you get it | Where it goes |
|---|---|---|---|
| 1 | WooCommerce store URL, e.g. `https://your-shop.com` (+ WP admin login) | Your WordPress host | Render env `WC_STORE_URL` |
| 2 | REST API **Consumer key** (`ck_…`) + **Consumer secret** (`cs_…`), Read permissions | WP Admin → WooCommerce → Settings → Advanced → REST API → Add key | Render env `WC_CONSUMER_KEY` / `WC_CONSUMER_SECRET` |
| 3 | Webhook secret (any random 32+ char string) | Generate one (Render can auto-generate) | Render env `WC_WEBHOOK_SECRET` **and** pasted into each WooCommerce webhook |
| 4 | A Render account (+ payment for Starter if you want no sleep) | render.com | Blueprint deploy |
| 5 | A Netlify account | netlify.com | Site deploy |
| 6 | (Optional) Custom domain + SMTP credentials for real emails | Registrar / Gmail / SendGrid | Netlify domain settings / Render SMTP vars |

Push this `Killowatt/` folder to a GitHub repo first — both Render and Netlify deploy from git.

---

## Step 1 — Deploy backend + database on Render (10 min)

1. Render Dashboard → **New → Blueprint** → connect your repo → it will detect `render.yaml`.
2. It creates two services:
   - `killokart-mysql` (private MySQL 8.0 with a 10 GB persistent disk), and
   - `killokart-api` (Docker web service — auto-runs `alembic upgrade head`, then uvicorn).
3. After the first deploy, open `killokart-mysql` → **Environment** → copy the generated
   `MYSQL_PASSWORD`, then open `killokart-api` → **Environment** and put it into `DATABASE_URL`:
   `mysql+pymysql://killokart:<PASSWORD>@killokart-mysql:3306/killokart` → **Save** (redeploys).
4. Verify: `https://<your-api>.onrender.com/health` → `{"status":"ok"}` and
   `/ready` → `{"status":"ready","db":"up"}`.
5. ⚠️ Free-tier services **sleep after inactivity** (first request takes ~60 s).
   For a real store use the **Starter** plan on the API service.

If the MySQL private service gives you trouble, alternative: create the database on
Railway/Aiven/PlanetScale and just set `DATABASE_URL` on the API service to that host.

---

## Step 2 — Connect WooCommerce REST API (5 min, needs WP admin)

1. WP Admin → **WooCommerce → Settings → Advanced → REST API → Add key**
   - User: an Administrator or Shop manager account
   - Permissions: **Read** (Read/Write only if you later want write-back)
   - Copy `ck_…` and `cs_…` **now** — the secret is shown once.
2. Render → `killokart-api` → **Environment** → set:
   - `WC_STORE_URL=https://your-shop.com` (no trailing slash, must be https for live)
   - `WC_CONSUMER_KEY=ck_…`, `WC_CONSUMER_SECRET=cs_…` → **Save** (redeploys).
3. Open the KilloKart site → **Integrations** → status should now say **Live store**.
   Click **Sync now (live)** → customers + orders import (idempotent, no duplicates).
   - `401` → wrong key/secret. `404` → wrong URL or WooCommerce/REST disabled.
   - Pretty permalinks must be enabled in WordPress for `/wp-json/` to work.

## Step 3 — Point WooCommerce webhooks at Render (real-time updates)

WP Admin → **WooCommerce → Settings → Advanced → Webhooks → Add webhook** (×4):

| Name | Topic | Delivery URL | Secret |
|---|---|---|---|
| KilloKart – customer created | Customer created | `https://<your-api>.onrender.com/api/v1/webhooks/woocommerce` | your `WC_WEBHOOK_SECRET` |
| KilloKart – customer updated | Customer updated | same | same |
| KilloKart – order created | Order created | same | same |
| KilloKart – order updated | Order updated | same | same |

Place a test order → it appears in KilloKart within seconds. Delivery failures show
under each webhook's **Logs** in WooCommerce.

---

## Step 4 — Deploy frontend on Netlify (5 min)

1. Netlify → **Add new site → Import from git** → same repo.
   Build settings are pre-filled from `netlify.toml` (base `woocrm-frontend`,
   command `npm run build`, publish `woocrm-frontend/dist`).
2. **Site settings → Environment variables** → add:
   - `VITE_API_URL=https://<your-api>.onrender.com/api/v1`
   (Vite bakes this in at build time — changing it requires **Trigger deploy**.)
3. Back in Render → `killokart-api` → set `BACKEND_CORS_ORIGINS` to include your site:
   `["https://<your-site>.netlify.app"]` → Save.
4. Open the site: Dashboard should show your real store numbers.

---

## Recommended order (TL;DR)

1. ✅ Code is ready (this repo).
2. **You:** create REST API keys in WooCommerce (2 min).
3. **Render:** Blueprint deploy → fix `DATABASE_URL` password → health check green.
4. **Render env:** paste `WC_STORE_URL` + keys → KilloKart Integrations → Sync now (live).
5. **WooCommerce:** create the 4 webhooks → test order.
6. **Netlify:** deploy frontend with `VITE_API_URL` → add site URL to `BACKEND_CORS_ORIGINS`.
7. Verify: Dashboard numbers = store numbers; new order arrives in real time.

## What I still need from you to finish this

- Your **store URL** and the **`ck_…`/`cs_…` keys** (or confirm you'll add them yourself in Render).
- Whether you want the Render **free tier** (sleeps) or **Starter** (always on).
- Your **Netlify site name** once created (to lock down CORS).
- Optional: SMTP credentials if you want real welcome/order emails instead of log-only mode.
