# Spec: Forget Password

## Overview

Spendly currently has no recovery path for a user who forgets their password — the only options are remembering it or asking someone to reset the seeded demo account by hand. This feature adds a self-service "Forgot password?" flow from the Login page: the user requests a reset by email, receives a real email (sent over SMTP) containing a link with a signed, short-lived JWT token, and lands on a Reset Password page that lets them set a new password before signing in again.

## Design

**Palette**
* Card / page background → `var(--paper)`, `var(--paper-card)` (same warm ledger paper as Login/Register — this flow is part of the same auth system, not a new one)
* Primary ink / headings → `var(--ink)`
* "Dispatched" stamp ink → `var(--accent)` (deep ledger green), ring accent → `var(--accent-2)` (terracotta)
* "Void" stamp ink (expired/used token) → `var(--danger)`
* Hairline borders / perforation → `var(--border)`

**Typography**
* Display heading ("Reset your password", "Check your inbox") → `var(--font-display)`
* Body copy, form labels, helper text → `var(--font-body)`
* Stamp text ("LINK DISPATCHED" / "VOID") → `var(--font-body)`, bold, uppercase, wide letter-spacing — set in ink color, not a decorative font, so no new font is introduced for a one-off effect

**Layout**

One sentence: reuse the existing `.auth-section` / `.auth-container` / `.auth-card` shell from Login/Register so the new pages read as the same system, and spend the one new visual idea entirely on the post-submit state rather than restructuring the page.

Forgot Password page (before submit):
```
┌───────────────────────────────┐
│      Reset your password       │
│  Enter your email and we'll    │
│  send you a reset link         │
│                                 │
│  ┌───────────────────────────┐ │
│  │ Email address             │ │
│  │ [______________________]  │ │
│  │                            │ │
│  │   [   Send reset link  ]  │ │
│  └───────────────────────────┘ │
│                                 │
│      ← Back to sign in          │
└───────────────────────────────┘
```

Forgot Password page (after submit — the "dispatch chit" replaces the form):
```
┌───────────────────────────────┐
│  ┆┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┆   │  ← dashed perforated edge, like a tear-off bank slip
│  ┆                          ┆  │
│  ┆     [LINK DISPATCHED]    ┆  │  ← angled ink-stamp badge, double-ring border, ~-6° rotation
│  ┆                          ┆  │
│  ┆  If an account exists    ┆  │
│  ┆  for that email, a reset ┆  │
│  ┆  link is on its way.     ┆  │
│  ┆  It expires in 30 min.   ┆  │
│  ┆                          ┆  │
│  └┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┘   │
└───────────────────────────────┘
```

Reset Password page (valid token) reuses the Register page's password field pattern exactly: show/hide toggle, `PasswordStrengthMeter`, "Suggest a strong password" — same component, same rules, no divergence.

Reset Password page (invalid/expired/already-used token) — instead of a plain error banner, the same stamp motif reappears in its "void" state: a large diagonal `VOID` ink-stamp watermark in `var(--danger)` over a disabled, greyed-out form, echoing a cancelled cheque:
```
┌───────────────────────────────┐
│   ╲                      ╲    │
│    ╲     V O I D          ╲   │  ← diagonal red watermark stamp
│     ╲                      ╲  │
│  This reset link has expired  │
│  or was already used.         │
│                                │
│   [   Request a new link   ]  │
└───────────────────────────────┘
```

**Signature**

The ink-stamp / dispatch-chit motif: submitting the request form doesn't pop a toast or spinner, it tears away to reveal a perforated paper chit stamped "LINK DISPATCHED" in ledger green/terracotta — the same physical ritual as a bank stamping a requisition slip. The *exact same* stamp device reappears later in a second state — a red diagonal "VOID" watermark — when a reset link is expired or reused, echoing a cancelled cheque. One motif, two states, both drawn directly from the passbook/ledger world this app already lives in; neither would make sense bolted onto an unrelated feature. On submit, the stamp animates in with a quick scale+rotate "thump" (~180ms); this is skipped under `prefers-reduced-motion`.

## Depends on

Step 02 (Login page) and Step 13 (strong password policy — the new password on the Reset Password page is validated by the same `Password` schema type and rendered with the existing `PasswordStrengthMeter`).

## Routes

* `POST /api/auth/forgot-password` — accepts an email, always returns the same generic success message (never reveals whether the account exists), and — only if a matching account exists — emails a signed reset link via SMTP — Public
* `POST /api/auth/reset-password` — accepts a reset token + new password + confirmation, validates the token (purpose, expiry, single-use), and updates the account's password hash — Public

## Database changes

No database changes. The reset token is a signed, self-contained JWT (`backend/app/security.py`) — no new table or columns. Single-use invalidation is achieved without storage: the token embeds a short hash derived from the user's *current* `password_hash` at issue time; once the password actually changes, that embedded hash no longer matches the stored one, so the same link can't be replayed. This keeps the "no migration tool" architecture intact (see `CLAUDE.md`).

## Frontend components

### Create

* `frontend/src/pages/ForgotPassword.tsx` — email-entry form; on success, swaps the card body for the "dispatch chit" success state described above
* `frontend/src/pages/ResetPassword.tsx` — reads `?token=` from the URL, renders the new-password form (reusing `PasswordStrengthMeter` + `generateStrongPassword`) on submit; renders the "VOID" stamp state if the backend rejects the token as invalid/expired

### Modify

* `frontend/src/pages/Login.tsx` — add a "Forgot password?" link near the password field, routing to `/forgot-password`

## Files to change

* `backend/app/config.py` — add SMTP settings (`smtp_host`, `smtp_port`, `smtp_username`, `smtp_password`, `smtp_from_email`, `smtp_use_tls`), `frontend_base_url` (used to build the reset link), `password_reset_token_expire_minutes`
* `backend/app/security.py` — add `create_password_reset_token(user_id, password_hash)` and `decode_password_reset_token(token)` (JWT with a distinct `purpose` claim so these tokens can never be reused as session access tokens)
* `backend/app/schemas.py` — add `ForgotPasswordRequest`, `ResetPasswordRequest` (mirrors `RegisterRequest`'s password-match validator), `MessageOut`
* `backend/app/crud.py` — add `update_user_password(db, user, new_password_hash)`
* `backend/app/routers/auth.py` — add the two new routes described above
* `backend/.env.example` — document the new SMTP settings and `FRONTEND_BASE_URL`
* `frontend/src/App.tsx` — wire `/forgot-password` and `/reset-password` as public routes (not wrapped in `ProtectedRoute`)
* `frontend/src/pages/Login.tsx` — add the "Forgot password?" link
* `frontend/src/index.css` — add styles for the dispatch-chit / stamp states (perforated border, angled stamp badge, void watermark), reusing existing color/spacing tokens only

## Files to create

* `backend/app/email.py` — `send_password_reset_email(to_email, reset_link)`, sends over SMTP via the stdlib `smtplib`/`email.message` (no new pip dependency)
* `backend/tests/test_forgot_password.py` — covers request/reset flow with SMTP mocked
* `frontend/src/pages/ForgotPassword.tsx`
* `frontend/src/pages/ResetPassword.tsx`

## New dependencies

No new dependencies. SMTP sending uses Python's standard library (`smtplib`, `email.message.EmailMessage`) — the same "reuse before adding" principle already followed for password hashing (Werkzeug) and JWTs (`pyjwt`).

## Rules for implementation

Claude **must always** follow these rules:

### Backend

* SQLAlchemy ORM + Pydantic schemas — never raw SQL string-formatting.
* Passwords must always be hashed using Werkzeug's `generate_password_hash`/`check_password_hash` (see `backend/app/security.py`) — this applies to the new password set via reset, exactly as it does at registration.
* Every route declares a Pydantic `response_model` — never return a raw dict.
* DB access belongs in `backend/app/crud.py`, never inline in routers.
* `POST /api/auth/forgot-password` must return the exact same response (status + message) whether or not the email matches an account, and must not let an SMTP send failure change that response or leak into an error the client can distinguish — this prevents user enumeration. Log SMTP failures server-side only.
* The reset JWT must carry a `purpose` claim (e.g. `"password_reset"`) distinct from the session access token, a short expiry (`password_reset_token_expire_minutes`, default 30), and the derived password-hash checksum described above for single-use invalidation. `decode_access_token` and `decode_password_reset_token` must never accept each other's tokens.
* Reuse existing helper functions whenever possible (e.g. `hash_password`, the `Password` schema type, `Email` schema type).
* Keep code modular and maintainable.

### Frontend

* **Whenever implementation of this spec is requested and it touches any component or UI, always invoke the built-in `frontend-design` skill before writing component/CSS code.** This applies every time.
* Build React function components under `frontend/src/pages/`. New pages get wired into `App.tsx`'s `<Routes>` as public routes.
* Use CSS variables only (from `frontend/src/index.css`). Never hardcode hex color values.
* Reuse `PasswordStrengthMeter` and `generateStrongPassword` on the Reset Password page rather than re-implementing password-strength UI.
* Every page must have a clean, distinctive, responsive, professional UI consistent with Spendly's ledger/passbook aesthetic.
* Respect `prefers-reduced-motion` for the stamp animation.

### Layout & Responsiveness

* Both new pages must remain visually appealing and usable on desktop, tablet, and mobile, following the same `.auth-*` responsive behavior already established by Login/Register.
* Forms must have proper spacing, alignment, and clear validation messages.

### User Experience

* Loading state on both forms while the request is in flight (disable submit button, matching existing `submitting` pattern from Login/Register).
* Success/error messaging via the existing patterns (`auth-error` banner for genuine errors like a network failure; the stamp states for the two expected outcomes of each flow).
* The "VOID" state must offer a clear next action: a button back to `/forgot-password` to request a fresh link.

## Definition of done

* [ ] From `/login`, clicking "Forgot password?" navigates to `/forgot-password`.
* [ ] Submitting a registered email on `/forgot-password` shows the "LINK DISPATCHED" stamp state and (with SMTP configured) sends a real email containing a link to `/reset-password?token=...`.
* [ ] Submitting an unregistered email on `/forgot-password` shows the exact same "LINK DISPATCHED" state and response — no way to distinguish account existence from the UI or network response.
* [ ] Opening the emailed link loads `/reset-password` with the token pre-filled from the URL, and the password field shows the strength meter and "suggest a strong password" option.
* [ ] Setting a new password that meets the strength policy succeeds, and the user can then log in at `/login` with the new password (and the old password no longer works).
* [ ] Re-using the same reset link a second time (or waiting past the 30-minute expiry) shows the "VOID" state instead of resetting the password again.
* [ ] `cd backend && pytest` passes, including new tests for the forgot-password/reset-password flow with SMTP mocked.
* [ ] `npx tsc --noEmit` passes in `frontend/`.
