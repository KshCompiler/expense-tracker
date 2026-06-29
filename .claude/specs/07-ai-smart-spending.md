# Spec: AI Smart Spending Suggestions

## Overview
Add a dedicated "Smart Suggestions" page that calls the Claude API server-side with the user's real financial data (current and prior month expenses, income, and per-category totals) and renders personalised, actionable spending tips. The route fetches data from the existing `expenses` and `income` tables, assembles a structured prompt, sends it to Claude, and displays the response as a clean card-based layout. This is the first AI-powered feature in Spendly and sits naturally after all core data-entry steps are complete, giving the user meaningful value derived from the data they have already entered.

## Depends on
- Step 01 (users table and session management)
- Step 02 (login — user must be authenticated to access suggestions)
- Step 03 (expenses table and `add_expense` — spending data must exist)
- Step 06 (add income — income data required for budget-vs-spend analysis)

## Routes
- `GET /suggestions` — render the Smart Suggestions page; calls Claude API and passes results to template — logged-in only

## Database changes
No database changes. The feature reads from the existing `expenses` and `income` tables using already-implemented helpers and two new read-only helpers added to `database/db.py`.

## Templates
- **Create:** `templates/suggestions.html`
  - Extends `base.html`
  - Shows a "Smart Suggestions" heading and a brief intro sentence
  - Renders each suggestion as a card (icon + heading + body text)
  - Shows a loading state message while the server fetches the response (handled server-side; page renders only after the API call returns)
  - If the API call fails, displays a friendly error message with a "Try again" link
- **Modify:** `templates/dashboard.html`
  - Add a "Get Smart Suggestions" button/link pointing to `url_for('suggestions')`

## Files to change
- `app.py` — add `/suggestions` route
- `database/db.py` — add `get_monthly_expense_summary(user_id, year_month)` and `get_monthly_income_total(user_id, year_month)` helpers
- `templates/dashboard.html` — add "Get Smart Suggestions" link
- `static/css/style.css` — add styles for `.suggestions-card`, `.suggestions-grid`, `.suggestions-error`; CSS variables only
- `requirements.txt` — add `anthropic`

## Files to create
- `templates/suggestions.html`

## New dependencies
- `anthropic` — official Anthropic Python SDK for calling the Claude API

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug (not touched by this step)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Use `url_for()` for all links — never hardcode URLs
- No JS frameworks — vanilla JS only
- The Claude API key must be read from the `ANTHROPIC_API_KEY` environment variable; never hardcode it
- Use `anthropic.Anthropic()` client with `client.messages.create()`
- Model: `claude-haiku-4-5-20251001` — fast and cost-effective for structured financial summaries
- Send a structured system prompt that instructs Claude to return exactly 4–6 numbered suggestions, each with a one-line heading and 2–3 sentence explanation, plain text only (no markdown, no bullet symbols)
- Parse Claude's plain-text response in the route and split it into individual suggestion objects `{heading, body}` before passing to the template
- If `ANTHROPIC_API_KEY` is not set or the API call raises an exception, catch it and pass `error=True` to the template — never let the exception propagate to a 500
- The `/suggestions` route must redirect to `/login` if the user is not authenticated
- Do not cache suggestions between requests — always generate fresh advice

## Definition of done
- [ ] Navigating to `/suggestions` while logged out redirects to `/login`
- [ ] Navigating to `/suggestions` while logged in shows the "Smart Suggestions" page without a 500 error
- [ ] The page displays 4–6 suggestion cards, each with a heading and explanation
- [ ] Suggestion content references the user's actual spending categories or amounts (not generic filler)
- [ ] If `ANTHROPIC_API_KEY` is missing or invalid, the page shows a friendly error message instead of a traceback
- [ ] The dashboard has a visible link/button to `/suggestions`
- [ ] No hardcoded hex colours — all colours use CSS variables
- [ ] All links use `url_for()` — no hardcoded URLs
- [ ] `anthropic` is listed in `requirements.txt`
