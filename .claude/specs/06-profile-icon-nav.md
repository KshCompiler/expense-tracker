# Spec: Profile Icon Navigation

## Overview
Replace the plain "Sign out" text link in the navbar with a circular profile avatar that shows the user's initial. Clicking the avatar opens a profile panel (anchored below the avatar) that displays the user's full name, email address, and a "Sign out" button. No separate profile page is needed — all identity info lives in this panel. This gives authenticated users their details at a glance and a clean way to log out without a dedicated page navigation.

## Depends on
- Step 01 (user registration / database — `full_name` stored in `users` table)
- Step 02 (login and session management — `session['user_full_name']` set on login)
- Step 05 (navbar already hides sign-in options when logged in)

## Routes
No new routes. The existing `/profile` route in `app.py` is not used by this feature — the panel is rendered inline in `base.html` using session data, so no extra server round-trip is needed.

## Database changes
No database changes.

## Templates
- **Modify:** `templates/base.html`
  - Replace the `<a href="{{ url_for('logout') }}" class="nav-cta">Sign out</a>` link with an avatar + panel widget
  - Avatar is a `<button class="nav-avatar">` displaying `session['user_full_name'][0] | upper`
  - Clicking it toggles a profile panel (`<div class="nav-profile-panel">`) anchored below the avatar
  - Panel contents (all rendered from session data, no extra route needed):
    - Large avatar circle with the user's initial (same initial as the nav button)
    - Full name (`session['user_full_name']`)
    - Email (`session['user_email']`)
    - "Sign out" button linking to `url_for('logout')`
  - Panel closes when clicking outside or pressing Escape

## Files to change
- `templates/base.html` — replace "Sign out" link with avatar button + inline profile panel
- `static/css/style.css` — add styles for `.nav-avatar`, `.nav-profile-panel`, open/close state; CSS variables only
- `static/js/main.js` — toggle panel on avatar click, close on outside click and Escape key

## Files to create
None.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only (not touched by this step)
- Passwords hashed with werkzeug (not touched by this step)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Use `url_for()` for all links — never hardcode URLs
- No JS frameworks — vanilla JS only
- No emojis in the UI
- The avatar initial must be derived from `session['user_full_name']` using Jinja2 (`session['user_full_name'][0] | upper`)
- The panel must close on Escape key and on click outside
- Do not remove the "Dashboard" nav link — it stays alongside the new avatar
- All user data in the panel comes from the session — do not make a DB call or add a new route

## Definition of done
- [ ] When logged in, the navbar shows a circular avatar with the user's initial instead of a "Sign out" text link
- [ ] Clicking the avatar opens a panel showing the user's full name, email, and a "Sign out" button
- [ ] Clicking outside the panel closes it
- [ ] Pressing Escape closes the panel
- [ ] "Sign out" in the panel logs the user out and redirects to the landing page
- [ ] When logged out, the navbar is unchanged (still shows "Sign in" and "Get started")
- [ ] No hardcoded hex colours — all colours use CSS variables
- [ ] All links use `url_for()` — no hardcoded URLs
