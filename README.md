# KilloKart — Customer Relationship Management (multi-user, authenticated)

Full-stack CRM: **React + Vite + Tailwind** frontend, **FastAPI** backend, **MySQL** database.
Accounts are first-class: bcrypt passwords, **server-side sessions in MySQL**
(HTTP-only cookie), per-user data isolation, audit logging, password reset, and
permanent account deletion. WooCommerce sync/webhooks exist but are **on hold**
(demo mode available per user).

```
Killowatt/
├── backend/    FastAPI + SQLAlchemy + Alembic + MySQL (port 8000)
└── frontend/   React 18 + Vite 5 + Tailwind CSS + Axios (port 5173)
```

## Prerequisites

- Python 3.12+ (`python --version`), Node.js 18+ (`node --version`)
- Local MySQL on `localhost:3306`, user `root`, password `root`

## 1. Backend setup

```powershell
cd backend
pip install -r requirements.txt
copy .env.example .env   # then check DATABASE_URL + secrets inside
```

Local `.env` database (per spec — never commit `.env`):

```ini
DATABASE_URL=mysql+pymysql://root:root@127.0.0.1:3306/crm_system
```

Create DB + migrate + run (use `python -m` — plain `uvicorn`/`alembic` may not be on PATH):

```powershell
python -m alembic upgrade head   # 0001 → 0004 (users, sessions, ownership…)
python -m uvicorn app.main:app --port 8000
```

API docs: http://127.0.0.1:8000/docs · Health: `/health` · DB readiness: `/ready`

## 2. Frontend setup

```powershell
cd ..\frontend
npm install
copy .env.example .env   # VITE_API_URL=http://localhost:8000/api/v1
npm run dev              # then open http://localhost:5173 (NOT 127.0.0.1 — see below)
```

> **Use `localhost` everywhere.** The login session lives in a `SameSite=Lax`
> cookie, which browsers only send when the site and the API share the same host.
> Open **http://localhost:5173** with `VITE_API_URL=http://localhost:8000/api/v1`
> (already the default). If you change `.env`, restart `npm run dev` — Vite reads
> it once at startup. Opening `http://127.0.0.1:5173` will log you in and then
> fail every data request with “Not authenticated”.

## 3. First run

1. Open http://localhost:5173 → **Create an account** (min 8 chars, letter + number).
2. Add your first **customer**, then an **order** — every record you see is data
   you entered yourself; there is no sample or imported data anywhere.
3. **Dashboard** — your real numbers, date filters, revenue chart.
4. **Customers** → profile → log **communications**, **notes**, **follow-ups**; **Orders** → create with line items (totals computed server-side), change status, expand for history; **Activity** shows the audit trail; **Settings** → profile, password, delete account.

## 4. Auth & security design (summary)

- Passwords: **bcrypt** (`$2b$`), strength rule, generic login errors, per-IP rate limits.
- Sessions: 48-byte random token, **SHA-256 hash only in MySQL** (`sessions` table with
  created/last-activity/expires/revoked timestamps), HTTP-only cookie (`kk_session`;
  `Secure + SameSite=None` in production, `Lax` on localhost), 30-day expiry + 7-day
  inactivity timeout, Origin-check CSRF middleware on mutations.
- Isolation: `owner_id` on customers, orders, interactions, followups, notes, comm logs;
  every query scoped to the session user (cross-user access → `404`).
- Deletion policy: one transaction removes the account, sessions, and all owned CRM rows;
  a single anonymized `account.deleted` audit row (email domain only) is retained.
- Password reset: hashed single-use 1-hour tokens, emailed via SMTP when configured
  (`FRONTEND_URL/reset-password?token=…`).

## 5. API map (all under `/api/v1`, auth cookie required except webhooks/health)

| Method | Path | Notes |
|---|---|---|
| POST | `/auth/register`, `/auth/login`, `/auth/logout` | Rate-limited; sets/clears cookie |
| GET/PUT | `/auth/me` | Session restore / profile update |
| POST | `/auth/change-password`, `/auth/forgot-password`, `/auth/reset-password` | Revokes other/all sessions |
| DELETE | `/auth/account` | Password re-auth; cascade + tombstone |
| GET | `/dashboard` | Per-user stats, `date_from/to`, `orders_by_day` chart data |
| GET/POST/PUT/DELETE | `/customers…` | Search, `status`, `order_status`, `sort`, pagination |
| GET/POST/PATCH/DELETE | `/orders…` | Backend totals, status history |
| GET/POST/PATCH/DELETE | `/interactions` | call/email/meeting/note + status/schedule |
| GET/POST/PATCH/DELETE | `/followups` | overdue/upcoming filters, `is_overdue` |
| GET | `/activity` | Read-only audit trail |

## 6. Tests executed (73/73 passing, live MySQL + running server)

Register/validation/409s · bcrypt hash verification · login + generic 401s · cookie
persistence · session expiry/inactivity · logout revocation · password change (revokes
others) · forgot/reset incl. token hashing · delete-account cascade + tombstone ·
customer/order/communication/follow-up/note CRUD · backend totals + status history ·
activity entries · dashboard-vs-DB math · **user A/B isolation (404s everywhere)** ·
422/401/404 handling · 12-table schema check · `vite build`.

## 7. Troubleshooting

- `'uvicorn' is not recognized` → use `python -m uvicorn …` / `python -m alembic …`
- Port `8000` serving stale routes → a previous server is still running; stop it and restart
- Frontend `ERR_NETWORK` → backend not running or `VITE_API_URL` wrong
- “Not authenticated” on every page after logging in → you opened
  `http://127.0.0.1:5173` instead of `http://localhost:5173` (or changed `.env`
  without restarting `npm run dev`)
- `401 Invalid webhook signature` → `WC_WEBHOOK_SECRET` mismatch (WooCommerce on hold)
