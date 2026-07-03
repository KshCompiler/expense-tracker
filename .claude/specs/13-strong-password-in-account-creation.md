# Spec: Strong Password in Account Creation

## Overview

Registration currently only enforces a minimum password length of 8 characters (`backend/app/schemas.py:15-18`), with no requirement for character variety, and the register form (`frontend/src/pages/Register.tsx`) gives no feedback beyond a static "Min. 8 characters" placeholder. This feature raises the password policy on account creation to require a mix of character classes (upper, lower, digit, special) in addition to length, enforced server-side as the single source of truth, and adds a live strength meter/checklist to the register form so users get real-time feedback while typing instead of finding out only after submitting. It also adds a "Suggest a strong password" action, similar to a browser password manager, that generates a random password satisfying every rule and fills it in for the user.

## Design

- **Palette** — Strength states map to existing tokens: weak → `var(--danger)` / `var(--danger-light)`, medium → `var(--accent-2)` / `var(--accent-2-light)` (terracotta), strong → `var(--accent)` / `var(--accent-light)` (green). Neutral/empty state uses `var(--border)` on `var(--paper-warm)`. No new hex values.
- **Typography** — Checklist items and the strength label use `var(--font-body)` at caption size (matching existing `.auth-subtitle`/hint text weight), not `var(--font-display)` — this is a functional UI element, not a heading.
- **Layout** — A thin segmented strength bar sits directly under the password input, with a small checklist of the four requirements beneath it that live-toggles a checkmark/muted state per keystroke; confirm-password field and submit button are unaffected.

  ```
  Password
  ┌─────────────────────────────────────┐
  │ ••••••••••                           │
  └─────────────────────────────────────┘
  [██████████░░░░░░░░░░]  Medium

  ✓ At least 8 characters
  ✓ One uppercase letter
  ○ One number
  ○ One special character (!@#$...)

  Suggest a strong password ↻
  ```
- **Signature** — The segmented strength bar fills left-to-right like a passbook ledger stamp progressing across a line, using the same hairline-border/card aesthetic as the rest of the auth card rather than a generic rounded progress pill.
- **Suggest action** — A small text-link-style button (`var(--accent)`, no heavy button chrome) under the checklist, so it reads as a helpful aside rather than competing with the primary "Create account" submit button.

## Depends on

- 01 — create account backend (registration route, password hashing, `users` table)

## Routes

No new routes. `POST /api/auth/register` is unchanged in shape — only the password validation rule tightens.

## Database changes

No database changes.

## Templates

Not applicable — this codebase has no Jinja templates (`app.py`/`base.html` predate the FastAPI + React migration in commit `142651f`). The equivalent UI work is a React component change; see **Files to change / Files to create** below.

## Files to change

- `backend/app/constants.py` — add the password-policy character-class regexes (or a small policy check) alongside the existing `EMAIL_REGEX`.
- `backend/app/schemas.py` — replace `_check_password_length` / the `Password` annotated type with a stronger `_check_password_strength` validator; keep it as the single `Password` type reused by `RegisterRequest` so the rule lives in one place.
- `frontend/src/pages/Register.tsx` — wire the password field's `onChange` into the new strength meter component, keep submit blocked (or just rely on the backend's 422 message) until requirements are met, and add the "Suggest a strong password" action that fills both the password and confirm-password fields.
- `frontend/src/index.css` — add the strength-meter styles (segmented bar, checklist rows, suggest-password link) using existing CSS variables, following the same section this file already uses for `.auth-*` rules.

## Files to create

- `frontend/src/components/PasswordStrengthMeter.tsx` — reusable component taking the current password string, computing which of the 4 rules pass, and rendering the bar + checklist. Reusable later if a "change password" feature is added.
- `frontend/src/utils/generatePassword.ts` — exports `generateStrongPassword()`, producing a random password that satisfies every rule in `PasswordStrengthMeter`'s policy (length + all 4 character classes), reusable by both Register and any future password-change feature.

## New dependencies

No new dependencies.

## Rules for implementation

Claude **must always** follow these rules:

### Backend

- Use the existing SQLAlchemy ORM + Pydantic pattern already established in this codebase (`backend/app/models.py`, `backend/app/schemas.py`) — do not write raw SQL or introduce a second validation path.
- Password hashing stays exactly as-is: Werkzeug's `generate_password_hash`/`check_password_hash` (scrypt) in `backend/app/security.py` — this feature only changes what's *accepted* pre-hash, never the hashing itself.
- The new strength rule belongs in `backend/app/schemas.py`'s `Password` annotated type (reusing the `AfterValidator` pattern already used for `_check_password_length`/`_check_email`) so both `RegisterRequest` and any future password-change endpoint share one definition.
- Treat the backend rule as the source of truth — the frontend meter is UX guidance only, never trusted for enforcement. Never weaken or bypass server-side re-validation to make the UI simpler.
- Raise a clear, specific Pydantic `ValueError` message (matching the existing style, e.g. `"Password must be at least 8 characters long!"`) so the frontend can surface it via the existing `ApiError` flow with no new error-handling plumbing.

### Frontend

- **Invoke the built-in `frontend-design` skill before writing the `PasswordStrengthMeter` component, the suggest-password action, or their CSS** — use it to refine the Design section above.
- Use CSS variables only (`var(--accent)`, `var(--accent-2)`, `var(--danger)`, etc.) — never hardcode hex values.
- `PasswordStrengthMeter` is a plain, reusable React component (props in, JSX out) — no new state-management or data-fetching library; it only ever computes from the password string it's given.
- Keep the existing `frontend/src/api/client.ts` as the only place `POST /api/auth/register` is called — no direct `fetch` in the component.
- Every requirement check in the checklist must update live as the user types (controlled input, no debounce needed at this scale).
- `generateStrongPassword()` must use `window.crypto.getRandomValues` (Web Crypto API), never `Math.random()` — a suggested password is a security-sensitive value and must not be predictable.

### Layout & Responsiveness

- The strength meter and checklist must remain legible and correctly spaced on mobile widths (this auth card is already capped at `var(--auth-width)` — reuse that constraint, don't widen the card).
- No layout shift/jank when the meter/checklist mounts — reserve their vertical space so the confirm-password field and button don't jump as the user types.

### User Experience

- Checklist items should read as plain, encouraging requirement text ("At least 8 characters", not "ERROR: too short"), consistent with this app's existing toast/error tone.
- Don't block typing or paste into the password field; only the submit action (or the existing server-side 422) enforces the rule.
- If the user pastes a password that already satisfies every rule, the meter should immediately show "Strong" with no extra interaction needed.
- Clicking "Suggest a strong password" fills both the password and confirm-password fields with the same generated value (mirroring how browser password managers behave), immediately showing "Strong" with no extra retyping required.

## Definition of done

- [ ] Registering with a password shorter than 8 characters is rejected (as today).
- [ ] Registering with a password that is 8+ characters but lacks an uppercase letter, a digit, or a special character is rejected with a clear message.
- [ ] Registering with a password satisfying length + all character-class rules succeeds and logs the user in, same as before.
- [ ] The register form's password field shows a live strength bar (weak/medium/strong) and a 4-item checklist that updates on every keystroke.
- [ ] The checklist and bar use only existing CSS variables — no new hex colors introduced.
- [ ] The auth card layout does not shift/jump oddly when the meter appears as the user starts typing.
- [ ] Existing registration tests (`backend/tests/`) still pass, plus new tests covering the rejected-weak-password and accepted-strong-password cases.
- [ ] `npx tsc --noEmit` passes with no new type errors.
- [ ] Clicking "Suggest a strong password" fills the password and confirm-password fields with an identical, randomly generated password that satisfies every rule (shows "Strong" immediately).
- [ ] The generated password uses `window.crypto.getRandomValues`, not `Math.random()`.
