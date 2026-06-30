# Spec: Home Page AI Feature Showcase

## Overview
Add a dedicated section to the existing landing page that showcases Spendly's AI-powered Smart Spending Suggestions feature. The section displays a static, visually compelling preview of what the AI suggestions look like — example suggestion cards with headings and body text — so visitors understand the value before signing up. This is a pure front-end change: no API calls are made on the landing page; the preview uses hardcoded sample content styled to match the real suggestions page.

## Depends on
- Step 07 (AI Smart Spending Suggestions) — the real feature this section promotes must already exist.

## Routes
No new routes.

## Database changes
No database changes.

## Templates
- **Modify:** `templates/landing.html`
  - Add a new `<section class="ai-showcase">` block between the existing `.features` section and the `.cta-section`.
  - The section has an eyebrow label ("Powered by AI"), a heading, a short subtitle, and a grid of 3 sample AI suggestion cards.
  - Each sample card shows a sparkle/star icon, a heading (e.g., "Reduce Food Spend"), and a 2-sentence body of realistic sample advice.
  - Below the cards, show a CTA link: if logged in, link to `url_for('suggestions')`; if not logged in, link to `url_for('register')`.

## Files to change
- `templates/landing.html` — add AI showcase section
- `static/css/style.css` — add styles for `.ai-showcase`, `.ai-showcase-inner`, `.ai-showcase-header`, `.ai-sample-grid`, `.ai-sample-card`, `.ai-sample-icon`, `.ai-sample-heading`, `.ai-sample-body`, `.ai-showcase-cta`

## Files to create
None.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug (not touched by this step)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Use `url_for()` for all links — never hardcode URLs
- No JS frameworks — vanilla JS only
- The sample cards must use hardcoded text — never call the AI API on the landing page
- The section must be fully responsive and look good on mobile and desktop
- Icons for sample cards must be plain Unicode characters or emoji-free symbols (no external icon libraries)
- The section styling must be consistent with the existing `.features` section (same spacing rhythm, same CSS variable palette)

## Definition of done
- [ ] Landing page has a visible "AI showcase" section between the features grid and the CTA section
- [ ] Section displays exactly 3 sample AI suggestion cards, each with an icon, heading, and body
- [ ] Body text on each card is realistic financial advice (references categories like Food, Bills, Transport)
- [ ] When a logged-in user visits the landing page, the CTA inside the section links to `/suggestions`
- [ ] When a logged-out user visits the landing page, the CTA inside the section links to `/register`
- [ ] No hardcoded hex colours — all colours use CSS variables
- [ ] All links use `url_for()` — no hardcoded URLs
- [ ] Section is visually consistent with the rest of the landing page (same font scale, spacing, card aesthetic)
- [ ] Page passes a quick manual check: no layout breaks at mobile width (≤ 480 px) and desktop width (≥ 1024 px)
