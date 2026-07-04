# Spec: Google and LinkedIn Login

## Overview

Spendly currently only supports email/password authentication. This feature adds "Continue with Google" and "Continue with LinkedIn" as alternate ways to register and sign in from the existing Login and Register pages, using standard OAuth 2.0 / OpenID Connect authorization-code flows. A user who authenticates this way never sets a Spendly password — their identity is verified by the provider instead — but if their verified provider email matches an existing local account, they're signed into that same account rather than getting a duplicate.

## Design

**Palette**
* Card / page background → `var(--paper)`, `var(--paper-card)` (unchanged — same shell as Login/Register)
* Divider rule + provider row borders (idle) → `var(--border)`
* Google row → each provider now uses its own official brand colors rather than Spendly's palette (see note below), since the request is for immediately recognizable provider buttons, not ledger-tinted rows
* Google button → white/`var(--paper-card)` background, neutral grey border, official multi-color "G" mark, dark grey label text
* LinkedIn button → LinkedIn blue (`#0A66C2`) background, white "in" mark and label text, darker blue (`#004182`) on hover
* Divider caption text → `var(--ink-muted)`

**Typography**
* Divider caption ("OR VERIFY WITH") → `var(--font-body)`, uppercase, wide letter-spacing, small size — the same restrained ledger-caption treatment as the "LINK DISPATCHED" stamp text from the forgot-password flow, not a new decorative font
* Provider row label ("Continue with Google" / "Continue with LinkedIn") → `var(--font-body)`, medium weight
* No `var(--font-display)` usage here — this is a utility control, not a heading

**Layout**

One sentence: below the existing password-login form, a single hairline "endorsement line" divider gives way to two full-width, stacked ledger-entry rows (not side-by-side pill buttons) — each an OAuth "seal" box + provider name + a quiet trailing arrow — so the OAuth options read as two more lines in the same passbook rather than a bolted-on social-login widget.

```
┌───────────────────────────────┐
│      [   Sign in    ]          │
│                                 │
│   ┄┄┄┄┄  OR VERIFY WITH  ┄┄┄┄┄  │  ← hairline rule + small-caps caption
│                                 │
│  ┌───┐                         │
│  │ G │  Continue with Google →│  ← white button, grey border, real multi-color G logo
│  └───┘                         │
│  ┌───┐                         │
│  │in │  Continue with LinkedIn→│  ← solid LinkedIn-blue button, white "in" mark
│  └───┘                         │
└───────────────────────────────┘
```

Same treatment appears on Register.tsx below its "Create account" button.

**Signature**

Reversed from the original ink-seal concept at the user's explicit request: recognizability of each provider's own brand now matters more than matching Spendly's ledger palette for this one control. Google and LinkedIn's official button colors/marks are used as-is (per each provider's own brand guidelines) rather than being restyled into Spendly's green/terracotta accents. Layout (full-width stacked rows, divider, spacing, `var(--radius-sm)` corners) is unchanged from the original design — only the fill/border/icon coloring of the two rows changed.

## Depends on

Step 02 (Login page) and Step 13 (strong password policy — unaffected for OAuth users, since they never set a Spendly password through this flow).

## Routes

* `GET /api/auth/{provider}/login` — `provider` is `google` or `linkedin` (404 for anything else); sets a short-lived, httponly `oauth_state` cookie and redirects (302) to the provider's authorization URL — Public
* `GET /api/auth/{provider}/callback` — verifies `state`, exchanges the authorization `code` for a token, fetches the provider's userinfo endpoint, resolves/creates the local user, sets the same session cookie `POST /api/auth/login` sets, and redirects (302) to the frontend home page (or to `/login?oauth_error=...` on any failure) — Public

These two routes return `RedirectResponse` directly rather than a JSON body, so they're exempt from `response_model` (there is no payload to model — the same category of exception FastAPI itself uses for `/api/health`).

## Database changes

* New table `oauth_accounts` (SQLAlchemy model in `backend/app/models.py`):
  * `id` (PK)
  * `user_id` — FK to `users.id`, `ondelete="CASCADE"`, not null
  * `provider` — string, not null (`"google"` or `"linkedin"`)
  * `provider_user_id` — string, not null (the provider's stable subject/`sub` claim)
  * `created_at` — server-default timestamp
  * Unique constraint on `(provider, provider_user_id)` — one provider identity maps to exactly one Spendly user
  * A single user can have rows for both providers (multi-provider linking), plus still have a password
* `users.password_hash` becomes nullable — an OAuth-only user (registered exclusively via Google/LinkedIn) has no password until/unless they later use the existing "Forgot password" flow to set one (that flow already works unmodified: it just assigns a `password_hash`, regardless of whether one existed before)
* This is not a purely additive change (an existing column's nullability changes), so per `CLAUDE.md`, delete `expense_tracker.db` and let it be recreated/reseeded rather than migrating in place

## Frontend components

### Create

* `frontend/src/components/OAuthButtons.tsx` — the two provider rows described above (shared by Login and Register so the markup/styling isn't duplicated); renders plain `<a>` elements (full-page navigation, not a `fetch` call, since the OAuth flow is redirect-based) pointing at the backend's `/api/auth/{provider}/login`

### Modify

* `frontend/src/pages/Login.tsx` — render `<OAuthButtons />` below the sign-in form; read an `oauth_error` query param (via `useSearchParams`) and surface it in the existing `auth-error` banner
* `frontend/src/pages/Register.tsx` — render `<OAuthButtons />` below the create-account form

## Files to change

* `backend/app/config.py` — add `google_client_id`, `google_client_secret`, `linkedin_client_id`, `linkedin_client_secret` (all `str | None = None`), and `backend_base_url: str = "http://localhost:5001"` (used to build the fixed `redirect_uri` sent to each provider; strips trailing slash like `frontend_base_url` already does)
* `backend/app/models.py` — add `OAuthAccount`, make `User.password_hash` nullable
* `backend/app/crud.py` — add `get_oauth_account`, `link_oauth_account`, `create_oauth_user`, `get_or_create_oauth_user` (the lookup → link-by-verified-email → create fallback described under Rules)
* `backend/app/routers/auth.py` — add the two routes above; guard the existing password `login()` route against `user.password_hash is None` (an OAuth-only user attempting a password login must get the same generic "Invalid email or password!" response, not a crash)
* `backend/.env.example` — document the four new OAuth credential vars and `BACKEND_BASE_URL`, with a note that each provider's console must have the exact callback URL registered
* `frontend/src/api/client.ts` — export a small `getOAuthUrl(provider)` helper (`${API_BASE_URL}/api/auth/${provider}/login`) so `OAuthButtons.tsx` never hardcodes an API path outside this module
* `frontend/src/index.css` — add `.auth-divider`, `.oauth-buttons`, `.oauth-row`, `.oauth-seal` styles per the Design section
* `frontend/src/pages/Login.tsx`, `frontend/src/pages/Register.tsx` — as above

## Files to create

* `backend/app/oauth.py` — per-provider config (authorize/token/userinfo URLs, scope) and the shared helpers: `build_authorize_url(provider, state)`, `exchange_code_for_token(provider, code)`, `fetch_userinfo(provider, access_token)` (normalizes both providers' responses to `{sub, email, email_verified, name}`)
* `frontend/src/components/OAuthButtons.tsx`
* `backend/tests/test_oauth_login.py` — covers the flow with the provider HTTP calls mocked (same pattern as the mocked Groq client in the OCR/chat tests)

## New dependencies

No new dependencies. `httpx` is already in `backend/requirements.txt` (currently a test-only import); this feature adds a runtime import of it in `backend/app/oauth.py` to call the providers' token/userinfo endpoints — flagging the change in role even though the package itself is already present.

## Rules for implementation

Claude **must always** follow these rules:

### Backend

* SQLAlchemy ORM + Pydantic schemas — never raw SQL string-formatting.
* Every route declares a Pydantic `response_model`, except the two OAuth redirect routes, which return `RedirectResponse` directly (no JSON body to model).
* DB access belongs in `backend/app/crud.py`, never inline in routers.
* `provider` must be validated against an explicit allowlist (`{"google", "linkedin"}`) in both routes — return 404 for anything else. This is also what keeps the flow from being usable as an open redirect: the *final* redirect destination after a successful callback is always `settings.frontend_base_url`, a fixed server-side setting — never a client-supplied value.
* The `state` param must be a high-entropy random value (`secrets.token_urlsafe`), stored in a short-lived httponly cookie before redirecting to the provider, and the callback must reject (redirect to `/login?oauth_error=...`) if the returned `state` doesn't match the cookie. Delete the cookie in the callback regardless of outcome.
* `get_or_create_oauth_user` resolution order: (1) existing `oauth_accounts` row for `(provider, sub)` → return its user; (2) else, if the provider confirms `email_verified`, look up a user by email → if found, create a new `oauth_accounts` row linking this provider to that existing user (supports one account signing in via password *and* one or more providers); (3) else, if `email_verified` is false and there's no existing `(provider, sub)` match, reject with a clear error rather than creating/linking an account off an unverified email; (4) else create a brand-new `User` (`password_hash=None`) plus the `oauth_accounts` row.
* Never accept a provider's token/userinfo response as authorization by itself for an *existing* account without the email-verification check in step (2) above — this is what prevents account takeover via a spoofed unverified email.
* If a provider's client id/secret isn't configured, `GET /api/auth/{provider}/login` must redirect to `/login?oauth_error=...` with a clear message instead of raising an unhandled error.
* Reuse existing helpers wherever possible (`create_access_token`, `COOKIE_NAME`, the cookie-setting logic already in `login()`).
* Keep code modular and maintainable.

### Frontend

* **Whenever implementation of this spec is requested and it touches any component or UI, always invoke the built-in `frontend-design` skill before writing component/CSS code.**
* `OAuthButtons.tsx` is a shared component under `frontend/src/components/` — Login and Register both use it, not copies of the same markup.
* Use CSS variables only (from `frontend/src/index.css`). Never hardcode hex color values.
  (Exception: the Google/LinkedIn button colors and logo marks are fixed by each provider's own brand guidelines, not part of Spendly's design system, so those specific hex values are hardcoded in `.oauth-row--google`/`.oauth-row--linkedin` rather than mapped to app tokens.)
* Never hardcode an API path in a component — go through the new `getOAuthUrl` helper in `api/client.ts`.
* Every page must remain clean, distinctive, responsive, and consistent with Spendly's ledger/passbook aesthetic — the OAuth buttons are the one deliberate exception, using each provider's official brand colors so they're instantly recognizable.

### Layout & Responsiveness

* The OAuth rows must remain full-width and stacked (not side-by-side) at every viewport size down to mobile, matching the existing `.auth-card` responsive behavior.
* Maintain the existing spacing rhythm between the form, the divider, and the two rows.

### User Experience

* Clicking a provider row navigates the full page (not a fetch/XHR) since the browser must follow the provider's own login/consent screens.
* An `oauth_error` query param on `/login` renders in the existing `auth-error` banner with a plain-language message (e.g. "Google sign-in isn't available right now. Please try again or sign in with your password.") — never a raw provider error string.
* A brand-new OAuth signup and an existing-account OAuth login both land the user on `/` already signed in, same as a successful password login.

## Definition of done

* [ ] `cd backend && pytest` passes, including new `test_oauth_login.py` covering: configured/unconfigured provider on `/login`, state-mismatch rejection on `/callback`, new-user creation, existing-verified-email linking, unverified-email rejection, and linking a second provider to an already-linked user.
* [ ] `npx tsc --noEmit` passes in `frontend/`.
* [ ] With Google OAuth credentials set in `.env` and the app running, clicking "Continue with Google" on `/login` redirects to Google's consent screen, and completing it lands back on `/` signed in.
* [ ] The same works for "Continue with LinkedIn" on `/login`.
* [ ] Both provider rows also appear and work from `/register`.
* [ ] Signing in via Google with an email that already has a local password-based account signs into that same existing account (not a duplicate) — verified by checking the account's expense/income history is the same one.
* [ ] Attempting a password login on an account that was created purely via OAuth (no password ever set) shows the normal "Invalid email or password!" message rather than a server error.
* [ ] Without any OAuth credentials configured, clicking a provider row shows a clear error banner on `/login` instead of a crash or blank page.
