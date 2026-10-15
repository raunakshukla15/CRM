# KilloKart Frontend (React + Vite + Tailwind CSS + Axios)

CRM UI for the KilloKart FastAPI backend. Every record shown is real data you
entered yourself — there is no sample, demo, or imported data anywhere in the app.

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
| `VITE_API_URL` | `http://localhost:8000/api/v1` | FastAPI base URL (**note the `/api/v1` prefix**; keep host `localhost` to match the site origin, otherwise the session cookie is blocked) |

Keep secrets out of frontend code — the API URL above is the only backend setting needed here.

## Pages → backend endpoints

| Page | Endpoint(s) |
|---|---|
| Dashboard | `GET /dashboard` |
| Customers | `GET /customers` (search, status, order_status) |
| Customer detail | `GET /customers/{id}`, `POST …/notes`, `POST /interactions`, `POST /followups` |
| Orders | `GET /orders` (status, search) |
| Communications | `GET/POST/PATCH/DELETE /interactions` |
| Follow-ups | `GET/POST/PATCH/DELETE /followups` |
| Activity | `GET /activity` |
| Settings | `GET/PUT /auth/me`, password + delete-account endpoints |

All pages implement loading, error + retry, and empty states, and are responsive
(grids collapse to one column on mobile).
