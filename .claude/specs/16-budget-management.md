# Spec: Budget Management

## Overview

Spendly currently only shows users what they've already spent — there's no way to say in advance "I don't want to spend more than ₹5,000 on Food this month" and see how close they are to that line. This feature adds per-category (and optional overall) monthly spending limits that the user sets and edits themselves, with live status — on track, approaching the limit, or over — recomputed from actual expense totals every time the dashboard or Budgets page loads. It turns Spendly from a rear-view mirror into something that can nudge a user before they overspend, which is the natural next step after the trend chart (Step 11) and category breakdown already on the dashboard.

For a user who has no idea what a reasonable limit even is, the budget form can also ask the AI — the same Groq integration already powering the chat assistant — to suggest a starting monthly limit per category based on that user's own spending history. Like the OCR bill-scanning feature, this is a suggestion only: it pre-fills the form for the user to accept, adjust, or ignore, and is never saved as a budget without the user explicitly submitting the form.

## Design

**Palette**
* Page / card background → `var(--paper)`, `var(--paper-card)` (same shell as Dashboard/Profile)
* On-track fill (0–79% of limit) → `var(--accent)` (the same deep ledger-green ink used for positive balances)
* Approaching limit (80–99%) → `var(--accent-2)` (terracotta caution ink — reused, not a new hue)
* Over budget (100%+) → `var(--danger)`, with `var(--danger-light)` as the row's tint background
* Unfilled portion of a gauge → `var(--border-soft)`
* Each row's category identity dot keeps its existing per-category color from `categoryTiles.ts` (Food terracotta, Bills orange, etc.) — that color means "which category," independent of the green/amber/red status color, which means "how close to the limit"

**Typography**
* "Budgets" section heading / page title → `var(--font-display)` — the same serif treatment as the "Hi, {firstName}" dashboard greeting
* Category name per row → `var(--font-body)`, 600 weight
* ₹ spent / limit figures → `var(--font-body)`, 600 weight — same numeric weight as `.db-ledger-value`
* Status captions ("84% used", "₹450 OVER") → `var(--font-body)`, uppercase, wide letter-spacing, small size — the same restrained caption treatment as the existing OAuth divider text and the password-reset "LINK DISPATCHED" stamp

**Layout**

One sentence: each budget renders as a narrow, perforated-edge "stub" that fills with ink from the bottom up like a passbook thermometer rather than a horizontal SaaS progress bar, shown as a compact row on the Dashboard and as a full editable list on a dedicated Budgets page.

Dashboard widget (compact, read-only, links to `/budgets`):
```
┌ Budgets this month ──────────────────────────────────── View all → ┐
│   ┆▓▓▓░┆       ┆▓░░░░┆        ┆▓▓▓▓▓┆        ┆▓▓▓▓▓▓┆               │
│   ┆▓▓▓░┆       ┆▓░░░░┆        ┆▓▓▓▓▓┆        ┆▓▓▓▓▓▓┆  ⟲ OVER        │
│   Food         Transport      Bills          Entertainment          │
│   84% used     40% used       100% used      ₹450 over              │
└──────────────────────────────────────────────────────────────────────┘
```

Budgets page (full list, editable):
```
┌ Set Monthly Budgets ─────────────────────────────────── [+ Add Budget] ┐
│ ┆▓▓▓░┆   Food                                              ⋮ Edit  ✕   │
│          ₹4,200 of ₹5,000 · 84% used · ₹800 left                      │
├─────────────────────────────────────────────────────────────────────── │
│ ┆▓▓▓▓▓┆  Bills                                ⟲ OVER      ⋮ Edit  ✕   │
│          ₹3,450 of ₹3,000 · ₹450 over budget                          │
├─────────────────────────────────────────────────────────────────────── │
│ ┆▓░░░░┆  Overall                                           ⋮ Edit  ✕   │
│          ₹18,600 of ₹40,000 · 47% used · ₹21,400 left                 │
└──────────────────────────────────────────────────────────────────────┘
```
Empty state (no budgets set yet): a single centered stub outline with the caption "No budgets set — add one to start tracking a limit" and the same `+ Add Budget` action, matching the restrained empty-state tone already used elsewhere (`db-empty`).

**Signature**

A hand-stamped ink seal reading "OVER" — rotated roughly −8°, set in `var(--danger)`, same stamp-glyph language as the ◈ folio seal on the dashboard and the "LINK DISPATCHED" reset-password stamp — appears next to any stub the moment its spend crosses 100% of its limit. The gauge itself is a perforated ledger stub filling bottom-up like rising ink, not a rounded horizontal bar, so a row of budgets reads like flipping to the limits page of an actual passbook rather than a generic dashboard widget.

Self-check: this reuses the app's existing tokens and its established stamp/seal visual language rather than introducing a new palette or a stock progress-bar-and-card-grid pattern — the stub/thermometer shape and the ink-stamp overage marker are specific to a passbook's own vocabulary, not a flourish that would apply unchanged to some other feature.

## Depends on

Step 03 (Add Expenses — category totals this feature reads), Step 11 (Spending Trend Chart — same dashboard folio this feature's widget sits alongside).

## Routes

* `GET /api/budgets` — list the current user's budgets with live computed status (spent this month, percent used, remaining, over/warning/ok) — Logged-in
* `POST /api/budgets` — create a budget for a category (or the special `"Overall"` pseudo-category) with a monthly limit; rejects a duplicate category for the same user — Logged-in
* `PUT /api/budgets/{budget_id}` — update an existing budget's monthly limit — Logged-in (must own the budget)
* `DELETE /api/budgets/{budget_id}` — remove a budget — Logged-in (must own the budget)
* `GET /api/budgets/suggest/{category}` — returns an AI-suggested monthly limit and a one-line rationale for `category`, based on the user's last 3 months of spending in it — Logged-in

## Database changes

New table `budgets` (SQLAlchemy model in `backend/app/models.py`):
* `id` (PK)
* `user_id` — FK to `users.id`, `ondelete="CASCADE"`, not null
* `category` — string, not null — one of `VALID_CATEGORIES` or the literal `"Overall"` (a whole-month cap across all categories, not tied to one)
* `monthly_limit` — Float, not null, must be > 0 (validated in the Pydantic schema, same pattern as `PositiveAmount`)
* `created_at`, `updated_at` — server-default timestamps, same pattern as `User`
* Unique constraint on `(user_id, category)` — one standing budget per category (or one `"Overall"` budget) per user; editing an existing category's limit is a `PUT`, not a second `POST`

This is purely additive (new table only), so no existing data needs to be dropped — `expense_tracker.db` does not need to be deleted for this change.

## Frontend components

### Create

* `frontend/src/pages/Budgets.tsx` — full budget management page: list of budget rows with stub gauges, add/edit/delete
* `frontend/src/pages/Budgets.css` — page-specific styles, following the same per-page CSS file pattern as `Dashboard.css`
* `frontend/src/components/BudgetStubGauge.tsx` — the shared stub-gauge visual (bottom-up ink fill + the rotated "OVER" stamp when applicable), used by both the Dashboard widget and the Budgets page
* `frontend/src/components/BudgetForm.tsx` — inline/modal form for creating or editing one budget (category picker reusing `CategoryTilePicker`/`EXPENSE_CATEGORY_TILES` plus an "Overall" option, and a ₹ monthly-limit amount input); includes a "✦ Suggest a limit" affordance next to the amount input that calls `GET /api/budgets/suggest/{category}` and pre-fills the input with the suggested value plus its rationale as helper text — never auto-submitted

### Modify

* `frontend/src/pages/Dashboard.tsx` — add a compact "Budgets this month" row of `BudgetStubGauge`s (reading `data.budgets` from the extended dashboard response) with a "View all →" link to `/budgets`
* `frontend/src/pages/AddExpense.tsx` — after a successful `POST /expenses`, fetch the updated budget status for the submitted category and show a `warning`/`error` toast via the existing `ToastContext` if the save pushed that category to ≥80% or over its limit; no toast if there's no budget set for that category
* `frontend/src/components/Navbar.tsx` — add a "Budgets" link next to "Dashboard" in the signed-in `nav-links`

## Files to change

* `backend/app/models.py` — add `Budget`
* `backend/app/constants.py` — add `BUDGET_WARNING_THRESHOLD = 0.8` and `BUDGET_CATEGORIES = VALID_CATEGORIES | {"Overall"}`
* `backend/app/schemas.py` — add `BudgetIn` (category, monthly_limit), `BudgetOut`, `BudgetStatus` (category, monthly_limit, spent, percent_used, remaining, status); extend `DashboardOut` with `budgets: list[BudgetStatus]`
* `backend/app/crud.py` — add `get_user_budgets`, `get_budget_by_id`, `create_budget`, `update_budget`, `delete_budget`, and `compute_budget_statuses(db, user_id)` (joins each budget against `get_expenses_by_category`/`get_user_expenses_this_month` totals already used by the dashboard), plus `get_category_spend_history(db, user_id, category, months=3)` reused by the AI suggestion route
* `backend/app/routers/dashboard.py` — call `compute_budget_statuses` and include it in the `DashboardOut` response
* `backend/app/schemas.py` — also add `BudgetSuggestionOut` (`suggested_limit`, `rationale`)
* `frontend/src/types/index.ts` — also add a `BudgetSuggestion` type
* `backend/app/main.py` — `app.include_router(budgets.router)`
* `frontend/src/App.tsx` — wire a `/budgets` route inside `<ProtectedRoute>`
* `frontend/src/types/index.ts` — add `Budget`, `BudgetStatus` types
* `frontend/src/index.css` — add `.budget-stub`, `.budget-stub-track`, `.budget-stub-fill`, `.budget-row`, `.budget-stamp-over` and related styles per the Design section
* `frontend/src/pages/Dashboard.tsx`, `frontend/src/pages/AddExpense.tsx`, `frontend/src/components/Navbar.tsx` — as above

## Files to create

* `backend/app/routers/budgets.py` — the four routes above
* `backend/tests/test_budgets.py` — covers create/list/update/delete, duplicate-category rejection, ownership checks, and status computation (ok/warning/over thresholds)
* `frontend/src/pages/Budgets.tsx`
* `frontend/src/pages/Budgets.css`
* `frontend/src/components/BudgetStubGauge.tsx`
* `frontend/src/components/BudgetForm.tsx`

## New dependencies

No new dependencies.

## Rules for implementation

Claude **must always** follow these rules:

### Backend

* SQLAlchemy ORM + Pydantic schemas — never raw SQL string-formatting.
* Every route declares a Pydantic `response_model` — never return a raw dict.
* DB access belongs in `backend/app/crud.py`, never inline in routers.
* `category` on `BudgetIn` must validate against `BUDGET_CATEGORIES` (existing categories plus `"Overall"`), reusing the same `AfterValidator` pattern as `Category` in `schemas.py` rather than a new ad hoc check.
* `monthly_limit` must reuse the existing `PositiveAmount` annotated type — never accept zero or negative limits.
* Every budget route must verify the budget belongs to `current_user` before returning/mutating it (same ownership-check pattern as `_get_owned_expense` in `routers/expenses.py`) — return 404, not 403, for a budget owned by another user, to avoid leaking existence.
* Creating a budget for a category the user already has one for must fail with a clear 400 message ("You already have a budget for this category — edit it instead.") rather than silently creating a duplicate row.
* "Real-time" status means recomputed from live expense totals on every read (dashboard load, Budgets page load) — do not introduce websockets, polling, or any new async infrastructure for this; this app's routes are synchronous by design.
* Reuse `get_expenses_by_category` and `get_user_expenses_this_month` rather than writing new duplicate aggregate queries for the per-category and "Overall" cases respectively.
* The AI suggestion follows the same trust boundary as OCR bill-scanning: re-validate the model's suggested number server-side (must be positive and within a sane multiple of the user's actual historical spend for that category) before returning it, and never treat it as anything more than a value that pre-fills the frontend form.
* Reuse the existing Groq/OpenAI client setup and `llama-3.1-8b-instant` model already used in `chat.py` — don't introduce a second client configuration for this.
* If `GROQ_API_KEY` isn't configured, `GET /api/budgets/suggest/{category}` must return a clear, handled error rather than crash — creating and editing a budget must work normally without it, since the suggestion is optional.

### Frontend

* **Whenever implementation of this spec is requested and it touches any component or UI, always invoke the built-in `frontend-design` skill before writing component/CSS code.**
* `BudgetStubGauge.tsx` is a shared component under `frontend/src/components/` — the Dashboard widget and the Budgets page both use it, not copies of the same markup.
* Use CSS variables only (from `frontend/src/index.css`). Never hardcode hex color values — including for the on-track/warning/over states, which map to `var(--accent)` / `var(--accent-2)` / `var(--danger)` respectively.
* Never hardcode an API path in a component — always go through `api/client.ts`.
* Toasts are the only feedback mechanism for the budget-crossed-threshold alert — do not add a new notification/banner system for this.
* Every page must remain clean, distinctive, responsive, and consistent with Spendly's existing ledger/passbook aesthetic.

### Layout & Responsiveness

* The Dashboard's budget row must wrap sensibly on narrow viewports (stubs stack or scroll horizontally) rather than overflowing or shrinking illegibly.
* The Budgets page list must stay readable and well-spaced whether the user has zero, a handful, or up to eight budgets (one per category plus "Overall").
* Forms (add/edit budget) must have clear spacing, alignment, and validation messages, matching `AddExpense`'s existing form conventions.

### User Experience

* Deleting a budget should ask for confirmation before the DELETE request fires (a confirmation dialog, not an instant destructive action).
* The category picker in `BudgetForm` must exclude categories the user already has a budget for (plus "Overall" once that's taken), so duplicate-creation errors are prevented in the UI rather than only caught server-side.
* Editing a budget pre-fills the form with its current category and limit; the category becomes read-only while editing (a budget's category doesn't change — only its limit does).
* An empty Budgets list shows a clear, inviting empty state with a direct "+ Add Budget" call to action, not a blank page.

## Definition of done

* [ ] `cd backend && pytest` passes, including new `test_budgets.py` covering: create, list with computed status, update, delete, duplicate-category rejection, cross-user ownership rejection, and correct `ok`/`warning`/`over` status at the 0%, 80%, and 100%+ thresholds.
* [ ] `npx tsc --noEmit` passes in `frontend/`.
* [ ] Setting a Food budget of ₹5,000, then adding Food expenses totaling ₹4,200, shows the Food stub at 84% ("warning" coloring) on both the Dashboard widget and the Budgets page.
* [ ] Pushing a category's spend past 100% of its limit shows the rotated "OVER" ink-stamp on its stub, and adding the expense that crossed the line shows an over-budget toast.
* [ ] Setting an "Overall" budget correctly sums all categories' spend for the month, independent of any per-category budgets also set.
* [ ] Editing a budget's limit on the Budgets page immediately updates its stub's fill percentage and status.
* [ ] Deleting a budget asks for confirmation, then removes its stub from both the Dashboard and Budgets page.
* [ ] The Budgets page renders a clear empty state when the user has no budgets set, with a working "+ Add Budget" action.
* [ ] The Budgets page and Dashboard widget both work responsively on desktop, tablet, and mobile viewport widths.
* [ ] Clicking "Suggest a limit" for a category with expense history pre-fills the monthly-limit input with an AI-suggested value and a one-line rationale, without saving anything until the user submits the form.
* [ ] Without `GROQ_API_KEY` configured, "Suggest a limit" fails gracefully with a clear message, and the rest of the budget form still works normally.
