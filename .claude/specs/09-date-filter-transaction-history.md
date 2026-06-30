# Spec: Date Filter in Transaction History

## Overview
This feature adds a date-range filter to the Transaction History page (`/view_transactions`), allowing logged-in users to narrow the expense list to a specific period — for example, a single month or a custom from/to range. The filter is applied via GET query parameters so results are bookmarkable and browser-navigable. No new page is introduced; the existing `view_transactions.html` template is enhanced with an inline filter form above the table.

## Depends on
- Step 03 — Add Expenses (expenses table and `add_expense` helper exist)
- Step 04 — Edit and Delete Expenses (`view_transactions` route and template exist)

## Routes
- `GET /view_transactions?from_date=YYYY-MM-DD&to_date=YYYY-MM-DD` — filtered transaction list — logged-in only

Both query parameters are optional; omitting either (or both) falls back to the current unfiltered behaviour.

## Database changes
No new tables or columns.

One new helper function added to `database/db.py`:

```python
def get_filtered_transactions(user_id, from_date=None, to_date=None):
    """Return expenses for user_id filtered by optional date bounds."""
```

The function builds a parameterised WHERE clause dynamically: if `from_date` is given, adds `date >= ?`; if `to_date` is given, adds `date <= ?`; if neither is given, returns all rows (same behaviour as `get_all_user_transactions`).

## Templates
- **Modify:** `templates/view_transactions.html`
  - Add a filter form above `.txn-card` that submits via GET to `/view_transactions`
  - Form contains two `<input type="date">` fields: `from_date` and `to_date`
  - A "Filter" submit button and a "Clear" link that navigates to `/view_transactions` with no params
  - Pre-populate the date inputs with the current filter values from the request so they persist after submission
  - Show a brief summary line (e.g. "Showing 6 transactions from 2026-06-01 to 2026-06-30") when a filter is active
  - The table and empty-state sections remain unchanged

## Files to change
- `app.py` — update `view_transactions` route to read `from_date`/`to_date` query params and call the new db helper; pass filter values back to template
- `database/db.py` — add `get_filtered_transactions` helper
- `templates/view_transactions.html` — add filter form and results summary

## Files to create
None.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — raw SQLite with `get_db()`
- Parameterised queries only — never interpolate date strings into SQL
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Filter form must use `method="GET"` — do not use POST for filtering
- Do not reuse `get_all_user_transactions`; route should call `get_filtered_transactions` for both filtered and unfiltered cases
- Validate date format in the route (`YYYY-MM-DD`) before passing to db; ignore malformed params silently (treat as absent)
- Do not add CSRF token to the GET filter form — CSRF protection is for state-changing POST requests only
- If `from_date` > `to_date`, flash a validation error and render the form without results

## Definition of done
- [ ] Visiting `/view_transactions` with no query params shows all expenses (existing behaviour unchanged)
- [ ] Visiting `/view_transactions?from_date=2026-06-01&to_date=2026-06-30` shows only June 2026 expenses
- [ ] The filter form on the page is pre-populated with the active filter values after submission
- [ ] Clicking "Clear" returns to `/view_transactions` with no filter applied and all transactions visible
- [ ] A summary line (e.g. "Showing N transactions · 2026-06-01 → 2026-06-30") appears when a filter is active and is absent when no filter is applied
- [ ] If `from_date` is after `to_date`, a flash error is shown and the table is not rendered
- [ ] Malformed date query params (e.g. `?from_date=not-a-date`) are silently ignored and treated as absent
- [ ] Filtering by a range with no matching expenses shows the empty-state message, not an error
- [ ] The feature is accessible only to logged-in users; unauthenticated access redirects to `/login`
