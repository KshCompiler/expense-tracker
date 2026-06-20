# Spec: Improve Dashboard Page Design

## Overview
Create and design the dashboard page template that displays a user's financial overview including income, expenses, remaining balance, transaction count, expense categories, and recent transactions. The dashboard is the main interface users see after logging in and should provide a clear, visual summary of their financial status.

## Depends on
- Step 01: Create account backend (user authentication system must be working)
- Step 02: Login and Logout functionality (users must be able to log in to access dashboard)

## Routes
- `GET /dashboard` — displays dashboard page for logged-in users — access level: logged-in

## Database changes
No database changes required. The dashboard uses existing helper functions in database/db.py to retrieve data.

## Templates
- **Create:** `templates/dashboard.html` — new template extending base.html that displays dashboard data
- **Modify:** 
  - `templates/base.html` — may need to add CSS classes or variables for dashboard-specific styling
  - `static/css/style.css` — may need to add dashboard-specific styles

## Files to change
- `app.py` — verify dashboard route is correctly implemented (already exists)
- `database/db.py` — verify helper functions exist and work correctly (already exist)
- `templates/base.html` — potential modifications for dashboard styling
- `static/css/style.css` — potential additions for dashboard-specific styles

## Files to create
- `templates/dashboard.html` — new dashboard template

## New dependencies
No new dependencies. Work within existing requirements.txt.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only (already followed in database/db.py)
- Passwords hashed with werkzeug (already implemented)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Use `url_for()` for every internal link — never hardcode URLs
- Route functions: one responsibility only — fetch data, render template, done
- Error handling: use `abort()` for HTTP errors, not bare `return "error string"`

## Definition of done
A specific testable checklist. Each item must be
something that can be verified by running the app.
- [ ] User can access /dashboard after logging in
- [ ] Dashboard page extends base.html
- [ ] Dashboard displays user's full name from session
- [ ] Dashboard shows today's date and current time
- [ ] Dashboard displays total expenses for current month
- [ ] Dashboard displays total income for current month (shows 0 if not implemented)
- [ ] Dashboard displays remaining balance (income - expenses)
- [ ] Dashboard displays transaction count for current month
- [ ] Dashboard displays expenses grouped by category with visual representation
- [ ] Dashboard displays recent transactions (last 5)
- [ ] Dashboard is responsive and works on mobile devices
- [ ] Dashboard uses CSS variables for colors, not hardcoded hex values
- [ ] All internal links use url_for()
- [ ] Page loads without errors
- [ ] Dashboard shows appropriate message when no transactions exist