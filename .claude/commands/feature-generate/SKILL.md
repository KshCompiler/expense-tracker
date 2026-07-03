---
description: Create a spec file and feature branch for the next Spendly step
argument-hint: "Step number and feature name e.g. 2 registration"
allowed-tools: Read, Write, Glob, Bash(git:*)
---

You are a senior developer spinning up a new feature for the Spendly expense tracker. Always follow the rules in `CLAUDE.md`.

User input: `$ARGUMENTS`

## Step 1 — Check working directory is clean

Run `git status` and check for uncommitted, unstaged, or untracked files.

If any exist, stop immediately and tell the user to commit or stash changes before proceeding.

**DO NOT CONTINUE** until the working directory is clean.

---

## Step 2 — Parse the arguments

From `$ARGUMENTS` extract:

1. `step_number`

   * Zero-pad to 2 digits.
   * Example:

     * `2 → 02`
     * `11 → 11`

2. `feature_title`

   * Human-readable title in Title Case.
   * Examples:

     * Registration
     * Login and Logout

3. `feature_slug`

   * Git and filename safe.
   * Lowercase kebab-case.
   * Only:

     * a-z
     * 0-9
     * `-`
   * Maximum 40 characters.
   * Examples:

     * registration
     * login-logout

4. `branch_name`
   Format:

   ```
   feature/<feature_slug>
   ```

   Example:

   ```
   feature/registration
   ```

If these cannot be inferred from `$ARGUMENTS`, ask the user for clarification before proceeding.

---


## Step 3 — Check branch name

Run:

```
git branch
```

If the desired branch already exists, append a number:

```
feature/registration-01
feature/registration-02
...
```

---

## Step 4 — Update main

Run:

```bash
git checkout main
git pull origin main
```

---

## Step 5 — Create feature branch

Run:

```bash
git checkout -b <branch_name>
```

---

## Step 6 — Research the codebase

Read these files before writing the spec:

* `CLAUDE.md`
* `backend/app/main.py`, `backend/app/models.py`, `backend/app/schemas.py`
* Every file inside `.claude/specs/`
* The `frontend/src/pages/` and `frontend/src/components/` files most relevant to this feature, plus `frontend/src/index.css` for existing design tokens

Use them to:

* Understand the roadmap.
* Follow existing conventions (FastAPI + SQLAlchemy + Pydantic backend, React + TypeScript frontend — see `CLAUDE.md` for the full architecture; this is not a Flask/Jinja app).
* Avoid duplicate specs.
* Verify the current database schema.

Check `CLAUDE.md` and `.claude/specs/` to confirm the requested step is **not already completed**.

If it is already marked complete:

* Warn the user.
* Stop immediately.

---

## Step 7 — Write the spec

Generate a spec document with **this exact structure**.

---

# Spec: <feature_title>

## Overview

One paragraph describing what this feature does and why it exists at this stage of the Spendly roadmap.

## Design

Required whenever this feature adds or changes any UI (skip only if the feature is purely backend/data with no frontend changes — write `No UI changes.` instead).

**The bar is: would a real user notice and like this, unprompted?** A good product is one that attracts and holds people — not one that merely works. Never write a Design section that a bored engineer would produce by default (a generic card grid, a plain progress bar, an unstyled table dump). Always invoke the `frontend-design` skill's own planning process to produce this section — do not freehand it — and hold its output to its own anti-genericness bar: no cookie-cutter SaaS-dashboard filler, no numbered 01/02/03 markers unless the content is genuinely sequential, no decoration that doesn't serve this specific feature's content.

Format as:

* **Palette** — named colors mapped to existing CSS variables (e.g. `Primary accent → var(--accent)`). Do not introduce new hex values; reuse tokens already defined in `frontend/src/index.css`.
* **Typography** — role → font mapping, reusing `var(--font-display)` / `var(--font-body)` per role (display heading, body text, captions/data).
* **Layout** — a one-sentence layout concept plus a small ASCII wireframe of the new/changed UI.
* **Signature** — the one deliberate, memorable detail this feature's UI should be remembered by, consistent with Spendly's existing ledger/passbook aesthetic (serif display headings, hairline borders, green/terracotta accents). This must be specific to what this feature actually does, not a generic flourish — if you can picture the same "signature" applying unchanged to a different feature, it isn't specific enough yet.

Before finalizing this section, self-check it against the anti-defaults in the `frontend-design` skill (warm-cream-serif, near-black-neon-accent, broadsheet-hairline are defaults, not choices, when applied regardless of subject) and revise anything that reads as the generic answer rather than a decision made for this feature.

## Depends on

Which previous steps this feature requires.

## Routes

List every new route.

Format:

* `METHOD /path` — description — access level

Access level:

* Public
* Logged-in

If none:

```
No new routes.
```

## Database changes

Verify against `backend/app/models.py` (SQLAlchemy models) — this app uses SQLAlchemy, not raw SQL.

Describe:

* New tables
* New columns
* Constraints
* Indexes

If none:

```
No database changes.
```

## Frontend components

### Create

List every new React component/page file (`frontend/src/pages/` or `frontend/src/components/`).

### Modify

List every existing component/page that needs changes and explain what changes.

## Files to change

Every existing file that must be modified (backend and frontend).

## Files to create

Every new file required (backend and frontend).

## New dependencies

List any required backend (`backend/requirements.txt`) or frontend (`frontend/package.json`) packages.

If none:

```
No new dependencies.
```

## Rules for implementation

Claude **must always** follow these rules:

### Backend

* SQLAlchemy ORM + Pydantic schemas — never raw SQL string-formatting (parameterised queries are handled by the ORM already).
* Passwords must always be hashed using Werkzeug's `generate_password_hash`/`check_password_hash` (see `backend/app/security.py`).
* Every route declares a Pydantic `response_model` — never return a raw dict.
* DB access belongs in `backend/app/crud.py`, never inline in routers.
* Reuse existing helper functions whenever possible.
* Keep code modular and maintainable.

### Frontend

* **Never settle for the first, most obvious layout.** Boring is a failure mode here, not a safe default — a spec that ships a plain form/table/card grid with no point of view is the thing to avoid, not the thing to fall back on when unsure. If the Design section above wouldn't make someone stop and look twice, redo it before moving on to markup.
* **Whenever implementation of this spec is requested and it touches any component or UI, always invoke the built-in `frontend-design` skill before writing component/CSS code.** This applies every time — not just once per spec, and not only when the user asks for it. Use it to fill in and refine the Design section above and to guide the actual markup/CSS.
* Build React function components under `frontend/src/pages/` (routes) or `frontend/src/components/` (reusable pieces) — this is a React + TypeScript app, not server-rendered templates. New pages get wired into `App.tsx`'s `<Routes>`.
* Use CSS variables only (from `frontend/src/index.css`). Never hardcode hex color values.
* Build every page as production-ready, not as a prototype.
* Every page must have a clean, distinctive, responsive, professional UI that a real user would find inviting to use — attractiveness is a requirement, not a nice-to-have.
* Maintain consistent spacing, typography, colors, border radius, shadows, and component styling throughout the application, matching Spendly's existing ledger/passbook aesthetic rather than introducing a new unrelated look.
* Use reusable UI components whenever possible.

### Layout & Responsiveness

* Every page must remain visually appealing regardless of how much content is displayed.
* Design layouts to scale for future growth.
* Assume pages may eventually contain hundreds or thousands of records.
* Never place large amounts of content directly onto the page without proper structure.
* Use responsive containers, cards, grids, sections, and spacing.
* Tables must be responsive and support scrolling or pagination where appropriate.
* Long lists should remain readable and well-organized.
* Forms should have proper spacing and alignment.
* Ensure all pages work well on desktop, tablet, and mobile devices.

### User Experience

* Use modern UI patterns where appropriate:

  * Cards
  * Dashboards
  * Search bars
  * Filters
  * Pagination
  * Empty states
  * Loading states
  * Confirmation dialogs
  * Success/error notifications
  * Responsive tables
  * Well-designed forms
* Forms should include clear validation messages.
* Avoid cluttered interfaces.
* Prioritize readability, accessibility, and usability.
* If a page displays data, design it so future additions do not require redesigning the layout.
* Every new page should feel polished and production-ready.

## Definition of done

Provide a checklist where every item can be verified by running the application.

---

## Step 8 — Save the spec

Save the generated spec to:

```
.claude/specs/<step_number>-<feature_slug>.md
```

---

## Step 9 — Report

Print **only** this summary:

```
Branch:    <branch_name>
Spec file: .claude/specs/<step_number>-<feature_slug>.md
Title:     <feature_title>
```

Then print:

> Review the spec at `.claude/specs/<step_number>-<feature_slug>.md` then enter Plan Mode with Shift+Tab twice to begin implementation.
> Note: when implementation touches any UI, the `frontend-design` skill will be invoked automatically before component/CSS code is written.

Do **not** print the full spec in chat unless explicitly asked.
