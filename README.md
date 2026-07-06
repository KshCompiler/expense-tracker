# Smart Expense Tracker

A FastAPI + React expense tracker with AI-assisted bill scanning and spending insights.

## Features

- **Expense & income tracking** — add, edit, and delete expenses and income entries with categorized tiles (Food, Transport, Bills, Health, Entertainment, Shopping, Other for expenses; Salary, Freelance, Business, Investment, Gift, Other for income)
- **Dashboard** — monthly totals, category breakdowns, and a spending trend chart
- **Budget management** — set monthly spending limits per category (or an overall limit), with live on-track/warning/over status and threshold alerts as expenses are logged; an AI-suggested starting limit (based on the user's own recent spending trend, with one-off spikes like a large one-time purchase excluded) can pre-fill the form
- **Transaction history** — search, filter, and paginate past transactions
- **AI bill scanning (OCR)** — upload a photo of a receipt and have a vision model pre-fill the expense/income form; every extracted field is re-validated server-side before it can be saved
- **AI chat suggestions** — context-aware spending questions and answers powered by Groq
- **Authentication** — email/password login with JWT httpOnly cookies, password reset via email, and optional Google/Microsoft OAuth sign-in
- **Profile management** — view account details and update settings

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, SQLite, Pydantic, JWT auth (httpOnly cookies), Werkzeug (password hashing), Groq via the OpenAI SDK for OCR and chat
- **Frontend**: React, TypeScript, Vite, React Router, Recharts

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+

### Backend setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

Copy `.env.example` to `.env` at the repo root and set `GROQ_API_KEY` and `SECRET_KEY`.

### Frontend setup
```bash
cd frontend
npm install
```

### Running the app
Run both in separate terminals:

```bash
# Terminal 1 - backend (port 5001)
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload --port 5001

# Terminal 2 - frontend (port 5173)
cd frontend
npm run dev
```

Open **http://localhost:5173**. The Vite dev server proxies `/api/*` to the backend. API docs are served at `http://localhost:5001/docs`.

A demo account is seeded automatically on first run: `demo@spendly.com` / `demo123`.

### Testing
- Backend: `cd backend && pytest`
- Frontend: `cd frontend && npx tsc --noEmit` (no test suite yet — verify UI changes via `npm run dev`)

## Project Structure

```
expense-tracker/
├── backend/
│   └── app/
│       ├── main.py           # FastAPI app, CORS, router includes, startup (create tables + seed)
│       ├── config.py         # Settings: SECRET_KEY, GROQ_API_KEY, DB path, CORS, cookie flags, OAuth
│       ├── database.py       # SQLAlchemy engine/session
│       ├── models.py         # User, Expense, Income
│       ├── schemas.py        # Pydantic request/response schemas
│       ├── security.py       # Password hashing + JWT cookie auth
│       ├── crud.py           # All DB access
│       ├── validation.py     # Shared expense/income field validation
│       └── routers/          # auth, dashboard, expenses, income, budgets, transactions, ocr, profile, chat
├── frontend/
│   └── src/
│       ├── api/client.ts     # Central fetch wrapper
│       ├── context/          # AuthContext, ToastContext
│       ├── components/       # Navbar, ProtectedRoute, CategoryTilePicker, BudgetStubGauge, BudgetForm, BillUploadDropzone, TrendChart, ...
│       └── pages/             # One component per route (Dashboard, Budgets, AddExpense, ...)
├── expense_tracker.db        # SQLite database (generated on first run)
└── .env                       # GROQ_API_KEY, SECRET_KEY, etc. (gitignored)
```

## Deployment Notes

- Set a real `SECRET_KEY`, `COOKIE_SECURE=true` (requires HTTPS), and `CORS_ORIGINS` to your real frontend origin(s) in production.
- If frontend and backend are deployed on different domains (e.g. Vercel + Railway), set `COOKIE_SAMESITE=none` on the backend (paired with `COOKIE_SECURE=true`) and `VITE_API_URL` to the backend's URL on the frontend.

See `.claude/CLAUDE.md` for full architecture details and development guidelines.
