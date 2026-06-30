# Spec: UX Polish — Search & Pagination on Transaction History

## Overview
Two UX improvements to the Transaction History page (`/view_transactions`):
1. A keyword search bar at the top of the filter toolbar so users can filter by description text.
2. Server-side pagination (20 rows per page) with prev/next links that preserve all active filter params.

Search and date filter live in the same `<form>` card: search row on top, date range row below, one Apply button for both.

## Depends on
- Step 09 — Date Filter in Transaction History (filter toolbar and `get_filtered_transactions` exist)

## Routes
- `GET /view_transactions?q=<text>&from_date=YYYY-MM-DD&to_date=YYYY-MM-DD&page=N`

All params are optional. Omitting any falls back to the current behaviour for that param.

## Database changes
No new tables or columns.

Modify `get_filtered_transactions` in `database/db.py`:
- Add optional `q` param: when present, append `AND LOWER(description) LIKE ?`
- Add `limit` and `offset` params for pagination
- Add a companion `count_filtered_transactions(user_id, from_date, to_date, q)` that returns the total row count (same WHERE clause, no LIMIT/OFFSET) for computing page count

## Templates
- **Modify:** `templates/view_transactions.html`
  - Add a `.toolbar-search-row` above `.toolbar-top` inside the existing form: full-width search input with a magnifier icon
  - Pre-populate search input with current `q` value
  - Active-filter bar shows search term and/or date range when either is active
  - Add a `.txn-pagination` block below `.txn-card` with prev/next links and "Page X of Y · N results"
  - Pagination links carry forward `from_date`, `to_date`, and `q`
  - Hide pagination block when total results ≤ 20

## Files to change
- `database/db.py` — update `get_filtered_transactions`; add `count_filtered_transactions`
- `app.py` — update `view_transactions` to read `q` and `page`; compute pagination metadata; pass to template
- `templates/view_transactions.html` — search row in toolbar; pagination block below table

## Files to create
None.

## New dependencies
None.

## Rules for implementation
- No SQLAlchemy or ORMs — raw SQLite with `get_db()`
- Parameterised queries only
- Use CSS variables — never hardcode hex values
- Filter form uses `method="GET"`
- `q` is stripped; empty string treated as absent
- Page numbers are 1-indexed in the URL; convert to 0-based offset in Python
- Clamp incoming `page` to valid range (1..total_pages) silently
- Do not add CSRF token to the GET filter form

## Definition of done
- [ ] Search input appears above the date filter in the same form card
- [ ] Searching `?q=groceries` shows only rows whose description contains "groceries" (case-insensitive)
- [ ] Search and date range can be combined: `?q=lunch&from_date=2026-06-01&to_date=2026-06-30`
- [ ] Search input is pre-populated with active query after submission
- [ ] Active-filter bar shows search term and/or date range when either is set
- [ ] Clearing the filter removes both `q` and date params
- [ ] With > 20 results, pagination controls appear below the table
- [ ] Prev/next links preserve `from_date`, `to_date`, and `q`
- [ ] Page param out of range is clamped silently (no 404)
- [ ] With ≤ 20 results total, no pagination controls are shown
- [ ] "Page X of Y · N results" summary is correct for all combinations
