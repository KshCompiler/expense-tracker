# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Spendly is a FastAPI (backend) + React (frontend) expense tracker.

## Development Commands

### Backend setup
1. Create a virtual environment (if not already present):
   ```bash
   cd backend
   python -m venv venv
   ```
2. Activate it:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` at the repo root and set `GROQ_API_KEY` and `SECRET_KEY`.

### Frontend setup
```bash
cd frontend
npm install
```

### Running the application
Run both processes concurrently, in separate terminals:
```bash
# Terminal 1 - backend (port 5001)
cd backend
venv\Scripts\activate   # or: source venv/bin/activate
uvicorn app.main:app --reload --port 5001

# Terminal 2 - frontend (Vite dev server, port 5173)
cd frontend
npm run dev
```
The Vite dev server proxies `/api/*` requests to `http://localhost:5001` (see `frontend/vite.config.ts`), so the app is used at **http://localhost:5173**. Swagger/OpenAPI docs for the backend are at `http://localhost:5001/docs`.

### Testing
- Backend: `cd backend && pytest` (40+ tests covering auth, expenses/income CRUD, dashboard, transactions filtering, OCR field-validation with a mocked LLM, and chat).
- Frontend: no test suite yet — verify changes via `npm run dev` and the browser, and `npx tsc --noEmit` for type errors.

### Agents
- Use the built-in Plan agent to build implementation plans for non-trivial work.
- Use a built-in subagent (e.g. Explore) to read files/investigate the codebase rather than reading everything in the main context.
- Use the relevant built-in agent type for a given task where one fits (e.g. test-runner, test-case-writer) rather than doing it ad hoc.

### Database management
- Tables are created automatically on backend startup via `Base.metadata.create_all()` in `backend/app/main.py`'s lifespan handler, followed by `crud.seed_db()` which seeds a demo user (`demo@spendly.com` / `demo123`) if the `users` table is empty.
- The SQLite database file is `expense_tracker.db` in the repo root (shared file path resolved in `backend/app/config.py`).
- To reset: stop the backend, delete `expense_tracker.db`, restart — it will be recreated and reseeded.

## Project Structure

```
expense-tracker/
├── backend/                    # FastAPI application
│   ├── app/
│   │   ├── main.py             # FastAPI app, CORS, request-size limit, router includes, lifespan (create tables + seed)
│   │   ├── config.py           # Settings (pydantic-settings): SECRET_KEY, GROQ_API_KEY, DB path, CORS origins, cookie flags
│   │   ├── database.py         # SQLAlchemy engine/session, PRAGMA foreign_keys=ON on connect
│   │   ├── models.py           # SQLAlchemy models: User, Expense, Income
│   │   ├── schemas.py          # Pydantic request/response schemas
│   │   ├── security.py         # Password hashing (Werkzeug scrypt) + JWT cookie auth
│   │   ├── deps.py             # get_db / get_current_user FastAPI dependencies
│   │   ├── crud.py             # All DB access/query logic
│   │   ├── validation.py       # Shared expense/income field-validation
│   │   ├── constants.py        # VALID_CATEGORIES, VALID_INCOME_SOURCES, OCR limits, request-body size cap
│   │   └── routers/            # auth, dashboard, expenses, income, transactions, ocr, profile, chat
│   ├── tests/                  # pytest suite (fresh throwaway SQLite DB per test session, mocked Groq/OpenAI client for OCR/chat tests)
│   ├── requirements.txt
│   └── .env.example
├── frontend/                   # React + TypeScript + Vite application
│   ├── vite.config.ts          # Dev server + /api proxy to localhost:5001
│   └── src/
│       ├── api/client.ts       # Central fetch wrapper (credentials: 'include', JSON, ApiError)
│       ├── context/            # AuthContext (current user via /api/auth/me), ToastContext
│       ├── components/         # Navbar, ProtectedRoute, ToastContainer, CategoryTilePicker, BillUploadDropzone, TrendChart
│       ├── pages/               # One component per route, each with its own .css where needed
│       ├── types/index.ts      # Shared TS types mirroring backend Pydantic schemas
│       └── index.css           # Global design tokens + shared component styles
├── expense_tracker.db          # SQLite database (generated)
└── .env                        # GROQ_API_KEY, SECRET_KEY, etc. (gitignored)
```

## Architecture Overview

- **Backend**: FastAPI, routers per feature area under `backend/app/routers/`, SQLAlchemy models + Pydantic schemas, sync engine (no async DB driver — routes are plain `def`, not `async def`, except the OCR routes which do async file reads).
- **Auth**: JWT access token in an **httpOnly, SameSite=Strict** cookie, set on `POST /api/auth/login`, cleared on `POST /api/auth/logout`. `get_current_user` (in `deps.py`) is a shared FastAPI dependency injected into every protected route — there is no per-route copy-pasted auth check.
- **CSRF**: Not needed and not implemented — `SameSite=Strict` on the auth cookie blocks cross-site requests from ever carrying it. Do not reintroduce a CSRF token scheme without reconsidering the auth model as a whole.
- **Password hashing**: Werkzeug's `generate_password_hash`/`check_password_hash` (scrypt) — a plain pip package, usable outside Flask.
- **Database**: SQLite (`users`, `expenses`, `income` tables). FK enforcement is manual — SQLite foreign keys are off by default; `backend/app/database.py` registers a `PRAGMA foreign_keys = ON` on every new connection via a SQLAlchemy `connect` event.
- **OCR bill-scanning**: `POST /api/expenses/extract-bill` and `/api/income/extract-bill` accept an `UploadFile`, validate size/magic-bytes server-side (never trusting `Content-Type`), call Groq's vision model via the `openai` package, and **re-validate every field the model returns** before sending it back — the model's output only pre-fills the frontend form and is never trusted or auto-saved.
- **Dashboard data**: The backend returns raw numbers only (`monthly_trend: [{year_month, label, total}]` etc.) — there is no server-side chart/SVG generation. `frontend/src/components/TrendChart.tsx` (Recharts) renders it client-side.
- **Frontend routing**: `react-router-dom`, pages under `frontend/src/pages/`, `ProtectedRoute` wraps anything requiring auth (redirects to `/login` if `AuthContext` has no user).
- **Frontend state/data-fetching**: Plain `fetch` via `api/client.ts` + React state/Context — no TanStack Query or Redux. This app is small enough that the extra layer isn't worth it; don't add one without a clear need.
- **Ports**: Backend runs on **port 5001** — don't change this. The Vite dev server runs on its default (5173) and proxies `/api/*` to the backend — if you change one port, update the other (`vite.config.ts` proxy target / CORS origins in backend config).

## Common Tasks

- **Adding a new backend endpoint**: Add a router function in the relevant `backend/app/routers/*.py` file (or a new router, included in `main.py`), a Pydantic schema in `schemas.py` if needed, and a `crud.py` function for any DB access. Always declare a `response_model=` — never return a raw dict.
- **Adding a new frontend page**: Add a component under `frontend/src/pages/`, wire it into `App.tsx`'s `<Routes>` (wrap in `<ProtectedRoute>` if it needs auth), and call the backend through `api/client.ts` — never hardcode a `fetch('/api/...')` call outside that module.
- **Modifying the database schema**: Add/edit the SQLAlchemy model in `backend/app/models.py`. There's no migration tool wired up (tutorial-scale app) — for schema changes beyond additive columns, delete `expense_tracker.db` and let it be recreated/reseeded.
- **Shared category/source tiles**: Category and income-source options (with icon/color) live in `frontend/src/components/categoryTiles.ts` — update there, not per-page, if you add/remove a category.

## Notes

- All database operations use parameterized queries / the SQLAlchemy ORM — never string-format SQL.
- Toasts are the single feedback mechanism on the frontend (`ToastContext` + `ToastContainer`).
- When deploying to production: set a real `SECRET_KEY` env var (not the `dev-...` default), set `COOKIE_SECURE=true` (requires HTTPS), and set `CORS_ORIGINS` to the real frontend origin(s).

## Warnings and things to avoid

- Never return a raw dict from a FastAPI route — always declare and use a Pydantic `response_model`.
- Never hardcode API URLs in React components — always go through `frontend/src/api/client.ts`.
- Never put DB logic in router functions — it belongs in `backend/app/crud.py`.
- Never install new packages mid-feature without flagging it — keep `backend/requirements.txt` and `frontend/package.json` in sync with what's actually used.
- Don't reintroduce a JS framework's competing state-management library (Redux, MobX, etc.) or a data-fetching library (TanStack Query, SWR) without a clear need — see "Frontend state/data-fetching" above.
- FK enforcement is manual — SQLite foreign keys are off by default; any new raw connection must run `PRAGMA foreign_keys = ON` (already handled centrally in `backend/app/database.py` for the SQLAlchemy engine).
- The backend runs on port 5001, not FastAPI/uvicorn's implicit default — don't change this without updating the frontend proxy config too.
- CSRF is handled via `SameSite=Strict` httpOnly cookies, not per-form tokens — do not reintroduce a hand-rolled CSRF token scheme without reconsidering the auth model as a whole.
- Don't weaken the OCR route's server-side re-validation of model output (amount > 0, category/source exact-match, date format, description length cap) — the model's output is never trusted as final.
