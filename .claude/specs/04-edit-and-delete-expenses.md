# Spec: Edit and Delete Expenses

## Overview
Enable users to modify or remove individual expense records from the transaction history. The backend routes (`/expenses/<id>/edit` GET/POST and `/expenses/<id>/delete` POST) and all required DB helpers (`get_expense_by_id`, `update_expense`, `delete_expense_helper`) are already fully implemented in `app.py` and `database/db.py`. This step creates the missing `edit_expense.html` template and adds Edit/Delete action controls to the existing `view_transactions.html`, completing the CRUD loop for the expenses feature.

## Depends on
- Step 01 — Create Account Backend (`users` table, session infrastructure)
- Step 02 — Login Page (`/login`, `/dashboard`, `base.html` with nav)
- Step 03 — Add Expenses (`/expenses/add`, `/view_transactions`, `expenses` table, `add_expense.html`, `view_transactions.html`)

## Routes
All routes already exist in `app.py` — **no new route code is required**:

- `GET  /expenses/<int:id>/edit`  — Render the pre-filled edit form for an expense — logged-in
- `POST /expenses/<int:id>/edit`  — Validate and persist the updated expense, redirect to `/view_transactions` on success — logged-in
- `POST /expenses/<int:id>/delete` — Delete the expense, redirect to `/view_transactions` — logged-in

## Database changes
No database changes. `get_expense_by_id`, `update_expense`, and `delete_expense_helper` already exist in `database/db.py`.

## Templates
- **Create:** `templates/edit_expense.html` — form extending `base.html`; pre-filled with the existing expense values passed as `expense`; fields: Amount (number, step 0.01, required, value=`expense['amount']`), Category (select with same fixed options as add form, pre-selected to `expense['category']`), Date (date input, required, value=`expense['date']`), Description (optional textarea, value=`expense['description']`); POST action to `url_for('edit_expense', id=expense['id'])`; Cancel link back to `url_for('view_transactions')`; display flash messages via `base.html`
- **Modify:** `templates/view_transactions.html` — add an "Actions" column header to the table `<thead>`; in each `<tbody>` row add a cell with an Edit link (`url_for('edit_expense', id=txn['id'])`) and a Delete button inside a `<form method="POST" action="{{ url_for('delete_expense', id=txn['id']) }}">` with a confirmation prompt via the `onsubmit` attribute; hide the Actions column on mobile with the same responsive media query pattern already present

## Files to change
- `templates/view_transactions.html` — add Actions column with Edit link and Delete form per row

## Files to create
- `templates/edit_expense.html`

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
- Form field `name` attributes in `edit_expense.html` must match exactly what the route reads: `amount`, `category`, `date`, `description`
- Delete must use a POST form, never a plain `<a>` link — GET requests must not mutate data
- Add a JavaScript `confirm()` dialog to the delete form's `onsubmit` so the user acknowledges the action before it fires
- No JS frameworks — vanilla only
- Category options must match those used across the app: Food, Transport, Bills, Health, Entertainment, Shopping, Other
- The edit form must pre-select the correct category option using Jinja2 `selected` attribute comparison
- On mobile, hide the Actions column the same way description is currently hidden in `view_transactions.html`

## Definition of done
- [ ] Navigating to `http://localhost:5001/view_transactions` while logged in shows an "Actions" column with Edit and Delete controls on every row
- [ ] Clicking Edit opens `/expenses/<id>/edit` and the form is pre-filled with the expense's existing amount, category, date, and description
- [ ] Submitting the edit form with valid data updates the expense, flashes "Expense updated successfully!", and redirects to `/view_transactions`
- [ ] Submitting the edit form with a missing required field (amount, category, or date) re-renders the form with an error flash message
- [ ] Submitting with a non-numeric or zero/negative amount shows an error flash message
- [ ] Clicking Delete triggers a JavaScript confirmation dialog before submitting
- [ ] Confirming deletion removes the expense, flashes "Expense deleted successfully!", and redirects to `/view_transactions`
- [ ] Cancelling the JS confirm dialog does not delete the expense
- [ ] Visiting `/expenses/<id>/edit` for an expense belonging to another user redirects to `/view_transactions` with a permission error flash
- [ ] Visiting `/expenses/<id>/edit` while logged out redirects to `/login`
- [ ] Sending a POST to `/expenses/<id>/delete` while logged out redirects to `/login`
- [ ] No hardcoded hex colours in any modified or created template
