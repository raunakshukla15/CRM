# KilloKart — WooCommerce Customer Relationship Management

Full-stack CRM: **React + Vite + Tailwind** frontend, **FastAPI** backend, **MySQL** database,
live **WooCommerce REST API** sync with honest **demo mode** (sample data) when no store is connected.

> Deploying to production? See **[DEPLOY.md](./DEPLOY.md)** (Netlify + Render + WooCommerce).

```
Killowatt/
├── woocommerce_crm_backend/   FastAPI + SQLAlchemy + Alembic + MySQL
└── woocrm-frontend/           React 18 + Vite 5 + Tailwind CSS + Axios
```

## Prerequisites

- Python 3.12+ (`python --version`), Node.js 18+ (`node --version`)
- Local MySQL running (this guide uses `root` / `root`; adjust as needed)

## 1. Backend setup

```powershell
cd woocommerce_crm_backend
pip install -r requirements.txt
copy .env.example .env   # then check DATABASE_URL + secrets inside
```

`.env` for local MySQL (already configured in your copy):

```ini
DATABASE_URL=mysql+pymysql://root:root@127.0.0.1:3306/woocommerce_crm
BACKEND_CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173"]
```

Create DB + migrate + run (use `python -m` — plain `uvicorn`/`alembic` may not be on PATH):

```powershell
python -m alembic upgrade head
python -m uvicorn app.main:app --port 8000
```

API docs: http://127.0.0.1:8000/docs · Health: `/health` · DB readiness: `/ready`

## 2. Frontend setup

```powershell
cd ..\woocrm-frontend
npm install
copy .env.example .env   # VITE_API_URL=http://127.0.0.1:8000/api/v1
npm run dev              # http://localhost:5173
```

## 3. First run (demo mode, no store needed)

1. Open http://localhost:5173 → **Integrations** → click **Load demo data**
   (8 customers, 12 orders, interactions, follow-ups — honestly labelled `mode: "demo"`).
2. **Dashboard** shows real DB stats (customers, orders, revenue, pending, overdue/upcoming).
3. **Customers** → search/filter → open a profile → log an **interaction**, **add a note**,
   create a **follow-up**; everything persists in MySQL.
4. **Follow-ups** → filter overdue/upcoming → **Mark completed** / Reopen.
5. **Orders** → filter by status / search WooCommerce order ID.

## 4. Going live — WooCommerce REST API

1. WordPress Admin → **WooCommerce → Settings → Advanced → REST API → Add key**
   (User = admin/shop-manager, Permissions = **Read**).
2. Copy the **Consumer key** (`ck_…`) and **Consumer secret** (`cs_…`).
3. In `woocommerce_crm_backend/.env` set:
   ```ini
   WC_STORE_URL=https://your-store.com
   WC_CONSUMER_KEY=ck_xxxxxxxxxxxxxxxx
   WC_CONSUMER_SECRET=cs_xxxxxxxxxxxxxxxx
   ```
4. Restart the API, then **Integrations → Sync now (live)**.
   - Uses `GET {store}/wp-json/wc/v3/customers` + `/orders` with Basic auth + pagination.
   - Upserts by WooCommerce ID (no duplicates), refreshes spend/VIP, stores last-sync time.
   - Only a masked `key_hint` is ever returned — secrets never reach the frontend.
   - 401/404/network errors surface as clear messages; nothing is faked in demo mode.

Webhook ingestion (`POST /api/v1/webhooks/woocommerce`, HMAC `X-WC-Webhook-Signature`)
still works as before — see `woocommerce_crm_backend/README.md`.

## 5. API map (all under `/api/v1`)

| Method | Path | Notes |
|---|---|---|
| GET | `/dashboard` | Real DB stats + recent orders/activity |
| GET/POST | `/customers` | Search, `status`, `min_spend`, `order_status`; 409 on dup email |
| GET/PUT | `/customers/{id}` | Detail incl. orders, notes, interactions, follow-ups |
| POST/GET | `/customers/{id}/notes` | Manual admin notes |
| GET/POST | `/interactions` | Filter `customer_id`, `interaction_type` |
| GET/POST | `/followups` | Filter `all/pending/overdue/upcoming/completed/cancelled` |
| PATCH | `/followups/{id}` | `{"status": "completed"}` etc. |
| GET | `/orders` | Filter `customer_id`, `status`, `search` (WC order ID) |
| GET/POST | `/integrations/woocommerce/status`, `/sync` | Never returns secrets |

## 6. Troubleshooting

- `'uvicorn' is not recognized` → use `python -m uvicorn …` / `python -m alembic …`
- `401 Invalid webhook signature` → `WC_WEBHOOK_SECRET` mismatch (check trailing spaces)
- `LookupError … enum` (fixed) → models use `values_callable`; if you see it, pull latest code
- Port `8000` serving stale routes → a previous server is still running; stop it and restart
- Frontend `ERR_NETWORK` → backend not running or `VITE_API_URL` wrong
