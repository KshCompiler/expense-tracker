# Spec: Redirect Logged-In Users and Refresh Landing Page

## Overview
When a user is already authenticated, the Spendly landing page (`/`) should not be shown at all — they are redirected straight to their dashboard. This removes the awkward state where a logged-in user sees marketing sign-in buttons. Separately, the landing page itself (shown only to guests) receives a visual refresh: improved hero section, richer feature cards, and a more polished CTA — making a stronger first impression for new visitors.

## Depends on
- Step 01 (user registration / database)
- Step 02 (login and session management)
- Step 03 (dashboard route)

## Routes
- `GET /` — modified: if `session.get('user_id')` is set, redirect immediately to `/dashboard`. Otherwise render `landing.html` as normal.

No new routes.

## Database changes
No database changes.

## Templates
- **Modify:** `templates/landing.html`
  - No session-conditional content needed — the route handles the redirect before the template renders
  - Refresh the hero section: stronger headline, better sub-copy, tighter layout
  - Refresh the feature cards: add short icons/emoji-free symbols, improve card copy, use CSS variables for accent colours
  - Refresh the CTA section: bolder heading, more persuasive copy, subtle background treatment
  - Keep all `url_for()` links — never hardcode URLs
  - Do NOT add a "Go to dashboard" link anywhere on the page

## Files to change
- `app.py` — `landing()` route: add early `redirect(url_for('dashboard'))` when user is logged in
- `templates/landing.html` — visual refresh of hero, features, and CTA sections
- `static/css/style.css` — add or refine styles for the refreshed landing sections (CSS variables only, no hardcoded hex)

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
- Use `url_for()` for all links
- The redirect must use `redirect(url_for('dashboard'))` — not a raw string
- Do NOT render any session-conditional content in `landing.html` — the route redirect makes it unnecessary
- Do NOT use JS frameworks — vanilla CSS and HTML only
- No emojis in the UI

## Definition of done
- [ ] Visiting `/` while **not** logged in shows the refreshed landing page with hero, features, and CTA
- [ ] Visiting `/` while **logged in** immediately redirects to `/dashboard` — the landing page is never rendered
- [ ] The landing page contains no "Go to dashboard" link or any session-conditional content
- [ ] The hero, feature cards, and CTA section look noticeably more polished than before
- [ ] The navbar continues to show the correct links in both states (no regression)
- [ ] All links use `url_for()` — no hardcoded URLs
- [ ] No hardcoded hex colours — all colours use CSS variables
