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
## Step 2.5 — Rename the Claude session

Immediately after successfully parsing the feature information, rename the current Claude session before performing any Git operations or writing the spec.

Use the following format for the session title:

```
Spendly – <feature_title>
```

Examples:

* Spendly – Registration
* Spendly – Login
* Spendly – Login and Logout
* Spendly – Dashboard
* Spendly – Expense Management

This step must be performed automatically every time this skill is activated.

If the environment does not support automatically renaming the current Claude session, inform the user that the session could not be renamed and continue with the remaining steps without failing the workflow.

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
* `app.py`
* `database/db.py`
* Every file inside `.claude/specs/`

Use them to:

* Understand the roadmap.
* Follow existing conventions.
* Avoid duplicate specs.
* Verify the current database schema.

Check `CLAUDE.md` to confirm the requested step is **not already completed**.

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

Required whenever this feature adds or changes any UI (skip only if the feature is purely backend/data with no template changes — write `No UI changes.` instead).

Produce this using the same planning process as the `frontend-design` skill, formatted as:

* **Palette** — named colors mapped to existing CSS variables (e.g. `Primary accent → var(--accent)`). Do not introduce new hex values; reuse tokens already defined in `static/css/style.css`.
* **Typography** — role → font mapping, reusing `var(--font-display)` / `var(--font-body)` per role (display heading, body text, captions/data).
* **Layout** — a one-sentence layout concept plus a small ASCII wireframe of the new/changed UI.
* **Signature** — the one deliberate, memorable detail this feature's UI should be remembered by, consistent with Spendly's existing ledger/passbook aesthetic (serif display headings, hairline borders, green/terracotta accents).

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

Verify against `database/db.py`.

Describe:

* New tables
* New columns
* Constraints
* Indexes

If none:

```
No database changes.
```

## Templates

### Create

List every new template.

### Modify

List every existing template and explain the required changes.

## Files to change

Every existing file that must be modified.

## Files to create

Every new file required.

## New dependencies

List any required pip packages.

If none:

```
No new dependencies.
```

## Rules for implementation

Claude **must always** follow these rules:

### Backend

* No SQLAlchemy or any ORM.
* Use SQLite with parameterised queries only.
* Passwords must always be hashed using `werkzeug.security`.
* Reuse existing helper functions whenever possible.
* Keep code modular and maintainable.

### Frontend

* **Whenever implementation of this spec is requested and it touches any template or UI, always invoke the built-in `frontend-design` skill before writing template/CSS code.** This applies every time — not just once per spec. Use it to fill in and refine the Design section above and to guide the actual markup/CSS.
* All templates must extend `base.html`.
* Use CSS variables only. Never hardcode hex color values.
* Build every page as production-ready, not as a prototype.
* Follow modern SaaS dashboard design principles inspired by products like Stripe, Notion, GitHub, Vercel, and Linear.
* Every page must have a clean, attractive, responsive, and professional UI.
* Maintain consistent spacing, typography, colors, border radius, shadows, and component styling throughout the application.
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
> Note: when implementation touches any UI, the `frontend-design` skill will be invoked automatically before templates/CSS are written.

Do **not** print the full spec in chat unless explicitly asked.
