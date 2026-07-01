# Spec: Spending Trend Chart

## Overview
Adds a "Spending Trend — Last 6 Months" chart to the dashboard so users can see how their total monthly spending has moved over time, not just the current month's category breakdown. The chart is a lightweight inline SVG bar chart rendered server-side from a new aggregation query — no charting library or JS framework is introduced, keeping with the project's vanilla-frontend constraint. It sits alongside the existing "Spending by Category" and "Recent Transactions" cards on `/dashboard`.

## Depends on
- Step 03 — Add Expenses (`expenses` table, `add_expense` helper)
- Step 04 — Edit and Delete Expenses (dashboard route pattern already established)
- Existing `dashboard` route and `dashboard.html` template

## Routes
No new routes. The chart data is fetched and rendered as part of the existing `GET /dashboard` route (logged-in only).

## Database changes
No new tables or columns.

One new helper function added to `database/db.py`:

```python
def get_monthly_expense_totals(user_id, months=6):
    """Return [{'year_month': 'YYYY-MM', 'label': 'Mon', 'total': float}, ...]
    for the last `months` calendar months (oldest first, current month last).
    Months with no expenses return total 0.0 — the series has no gaps.
    """
```

Implementation notes:
- Build the list of the last 6 `YYYY-MM` keys in Python (like the existing `month_date` helper in `seed_db`), then run a single parameterised query:
  `SELECT strftime('%Y-%m', date) AS ym, SUM(amount) AS total FROM expenses WHERE user_id = ? AND date >= ? GROUP BY ym`
  using the earliest month's first day as the lower bound.
- Merge query results into the 6-month scaffold in Python so missing months come back as `0.0` instead of being omitted.
- `label` is the short month name (e.g. "Feb") for axis display, derived with `datetime.strptime(ym, "%Y-%m").strftime("%b")`.

## Templates
- **Modify:** `templates/dashboard.html`
  - Add a new full-width `.db-trend-card` section below the existing `.db-main` two-column grid.
  - Header row: title "Spending Trend" + subtitle "Last 6 months".
  - Body: inline `<svg>` bar chart plotting the 6 monthly totals — one rounded `<rect>` bar per month, a baseline axis line, and month labels (`label`) below the chart under each bar.
  - Empty state (all totals zero, e.g. brand-new account): show `.db-empty` message "Not enough spending history yet." instead of the chart.
  - Chart must be built with plain SVG + Jinja loops (no `<canvas>`, no chart JS library).

## Files to change
- `database/db.py` — add `get_monthly_expense_totals`
- `app.py` — in the `dashboard` route, call `get_monthly_expense_totals(user_id)` and pass `monthly_trend` to the template
- `templates/dashboard.html` — add the trend chart card and its styles

## Files to create
None.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — raw SQLite with `get_db()`
- Parameterised queries only — never interpolate the date bound into SQL
- Use CSS variables for all chart colours (bar fill, baseline, text) — never hardcode hex values
- Compute each bar's SVG `x`, `y`, `width`, `height` in Python (in the route or a small template helper) so the template only loops over ready-made bar rects — avoid complex arithmetic inline in Jinja
- Chart must scale proportionally to the max value in the series; if all totals are 0, render the empty state instead of a flat/degenerate chart
- The card must remain visually consistent with `.db-chart-card` styling already used for "Spending by Category" (same border, radius, padding, header pattern)
- The chart SVG must use a `viewBox` so it scales responsively on mobile without JS

## Definition of done
- [ ] Dashboard shows a "Spending Trend — Last 6 months" card below the category/recent-transactions row
- [ ] Chart plots exactly 6 months of data, oldest on the left, current month on the right
- [ ] Months with zero expenses still appear on the chart as a 0 point (no gaps in the line)
- [ ] Month labels (e.g. "Feb", "Mar" … current month) appear along the x-axis in order
- [ ] Chart line/area scales correctly regardless of whether totals are in the hundreds or tens of thousands
- [ ] On a brand-new account with no expense history at all, the empty state message is shown instead of a broken/flat chart
- [ ] No hardcoded hex colours — all chart colours use CSS variables
- [ ] Chart is responsive and remains readable at mobile width (≤ 480px) and desktop width (≥ 1024px)
- [ ] No new pip packages or JS libraries were added to render the chart
