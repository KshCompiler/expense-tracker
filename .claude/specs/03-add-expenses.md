# Spec: Add Expenses

## Overview
Deliver the UI for logging a new expense and viewing all past transactions. The backend routes (`/expenses/add` GET/POST and `/view_transactions` GET), all DB helpers (`add_expense`, `get_all_user_transactions`), and the `expenses` table are already fully implemented in `app.py` and `database/db.py`. This step creates the two missing templates that make those routes renderable, completing the core expense-entry loop for Spendly.

## Depends on
- Step 01 — Create Account Backend (`users` table, session infrastructure)
- Step 02 — Login Page (`/login`, `/dashboard`, `base.html` with nav)

## Routes
All routes already exist in `app.py` — **no new route code is required**:

- `GET  /expenses/add`  — Render the add-expense form — logged-in
- `POST /expenses/add`  — Validate and persist a new expense, redirect to `/dashboard` on success — logged-in
- `GET  /view_transactions` — Render full transaction history for the logged-in user — logged-in

## Database changes
No database changes. The `expenses` table (`id`, `user_id`, `amount`, `category`, `date`, `description`, `created_at`) already exists and is seeded with demo data.

## Templates
- **Create:** `templates/add_expense.html` — form extending `base.html`; fields: Amount (number, step 0.01, required), Category (select with fixed options: Food, Transport, Bills, Health, Entertainment, Shopping, Other), Date (date input defaulting to today, required), Description (optional textarea); POST to `url_for('add_expense')`; display flash messages via `base.html`
- **Create:** `templates/view_transactions.html` — table extending `base.html`; columns: Date, Category (with a badge/chip styled by category), Description, Amount; rows from `transactions` variable passed by the route; empty-state message when no transactions exist; link to `url_for('add_expense')` to encourage first entry

## Files to change
- None (backend is complete)

## Files to create
- `templates/add_expense.html`
- `templates/view_transactions.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only (already satisfied; no new DB queries in this step)
- Passwords hashed with werkzeug (not applicable here)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Never hardcode URLs in templates — always use `url_for()`
- Flash messages are already rendered by `base.html`; do not duplicate flash rendering
- Form input `name` attributes must match exactly what the route reads: `amount`, `category`, `date`, `description`
- No JS frameworks — vanilla only
- Category options in the select must match the categories used in seed data and dashboard chart: Food, Transport, Bills, Health, Entertainment, Shopping, Other

## Definition of done
- [ ] Navigating to `http://localhost:5001/expenses/add` while logged in renders a form without a 500 error
- [ ] Submitting the form with valid data (e.g. amount=50, category=Food, date=today) creates the expense, flashes "Expense added successfully!", and redirects to `/dashboard`
- [ ] Submitting the form with a missing required field (amount, category, or date) re-renders the form with an error flash message
- [ ] Submitting with a non-numeric or zero/negative amount shows an error flash message
- [ ] Visiting `/expenses/add` while logged out redirects to `/login` with an error flash
- [ ] Navigating to `http://localhost:5001/view_transactions` while logged in shows a table of all expenses without a 500 error
- [ ] The newly added expense appears in the transactions list
- [ ] When there are no transactions, an empty-state message is shown instead of an empty table
- [ ] Visiting `/view_transactions` while logged out redirects to `/login`
- [ ] No hardcoded hex colours in either template
