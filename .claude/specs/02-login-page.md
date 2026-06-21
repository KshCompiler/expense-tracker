# Spec: Login Page

## Overview
Implement the login page template so that registered users can authenticate with their email and password. The backend route (`/login` GET/POST) and session management are already wired up in `app.py`; this step delivers the missing `templates/login.html` that the route expects. On success the user is placed in a session and redirected to `/dashboard`. On failure a flash error is displayed and the form is re-rendered.

## Depends on
- Step 01 — Create Account Backend (users table, `create_user`, `get_user_by_email` must exist in `database/db.py`)

## Routes
The following routes already exist in `app.py` — **no new route code is required**:

- `GET  /login`  — Render the login form — public
- `POST /login`  — Validate credentials, set session, redirect to `/dashboard` on success — public
- `GET  /logout` — Clear session, flash info message, redirect to `/` — logged-in

## Database changes
No database changes.

## Templates
- **Create:** `templates/login.html` — login form that extends `base.html`, displays email + password fields, and renders flash messages already injected by `base.html`
- **Create:** `templates/dashboard.html` — extends `base.html`; layout: welcome banner (greeting + date/time + Add Expense button), 4 stat cards (expenses, income, balance, transaction count) with coloured left-border accents, then a two-column main section: left = Spending by Category bar chart (real `categories` data), right = Recent Transactions compact list with category badges. All styles scoped in a `{% block head %}` `<style>` block; no Quick Actions panel.
- **Modify:** None

## Files to change
- None (backend is complete)

## Files to create
- `templates/login.html`
- `templates/dashboard.html` (stub — summary cards + spending-by-category bar chart + recent transactions; no quick-actions panel)

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only (already satisfied; no new DB queries in this step)
- Passwords hashed with werkzeug (already satisfied in `app.py`)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Never hardcode URLs in templates — always use `url_for()`
- Flash messages are already rendered by `base.html`; do not duplicate flash rendering in the template
- The form `action` must POST to `url_for('login')`
- Input names must match exactly what the route reads: `email`, `password`
- Include a link to `url_for('register')` for users who don't have an account yet
- No JS frameworks — vanilla only

## Definition of done
- [ ] Navigating to `http://localhost:5001/login` renders a login form without a 500 error
- [ ] Submitting the form with a valid email + password (e.g. `demo@spendly.com` / `demo123`) logs the user in and redirects to `/dashboard` without a 500 error
- [ ] Submitting with wrong credentials re-renders the login page with an error flash message visible
- [ ] Submitting with empty fields shows an error flash message
- [ ] The "Sign in" link in the navbar points to the login page (already set in `base.html`)
- [ ] A "Create account" / register link is present on the login page and navigates to `/register`
- [ ] After logging in and visiting `/logout`, the session is cleared and the user is redirected to the landing page with an info flash message
- [ ] Page title block reads "Sign In — Spendly" (or similar)
- [ ] No hardcoded hex colours in the template or any new CSS added for this step
