# KilloKart Frontend (React + Vite + Tailwind CSS + Axios)

CRM UI for the WooCRM FastAPI backend.

## Setup

```powershell
npm install
copy .env.example .env
npm run dev     # http://localhost:5173
npm run build   # production build -> dist/
```

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `VITE_API_URL` | `http://127.0.0.1:8000/api/v1` | FastAPI base URL (**note the `/api/v1` prefix**) |

Never put WooCommerce keys here — they live only in the backend `.env`.

## Pages → backend endpoints

| Page | Endpoint(s) |
|---|---|
| Dashboard | `GET /dashboard` |
| Customers | `GET /customers` (search, status, order_status) |
| Customer detail | `GET /customers/{id}`, `POST …/notes`, `POST /interactions`, `POST /followups` |
| Orders | `GET /orders` (status, search) |
| Follow-ups | `GET/POST /followups`, `PATCH /followups/{id}` |
| Integrations | `GET/POST /integrations/woocommerce/status`, `/sync` |

All pages implement loading, error + retry, and empty states, and are responsive
(grids collapse to one column on mobile).
