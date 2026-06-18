# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Setup
1. Create a virtual environment (if not already present):
   ```bash
   python -m venv venv
   ```
2. Activate the virtual environment:
   - On Windows: `venv\Scripts\activate`
   - On macOS/Linux: `source venv/bin/activate`
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application
- Start the Flask development server:
  ```bash
  python app.py
  ```
  The app will be available at http://localhost:5001.

- Alternatively, using Flask CLI:
  ```bash
  export FLASK_APP=app.py   # set FLASK_APP=app.py on Windows
  flask run --port=5001
  ```

### Testing
- Run the test suite with pytest:
  ```bash
  pytest
  ```
- To run a specific test file:
  ```bash
  pytest tests/test_specific.py
  ```

### Database Management
- The database is initialized automatically when the app starts via `init_db()` in `app.py`.
- To manually initialize or recreate the database, you can run:
  ```bash
  python -c "from database.db import init_db; init_db()"
  ```
- The SQLite database file is `expense_tracker.db` in the project root.

## Project Structure

```
expense-tracker/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── expense_tracker.db     # SQLite database (generated)
├── static/                # Static assets (CSS, JavaScript)
│   ├── css/
│   │   └── style.css
│   └── js/
├── templates/             # HTML templates for Flask rendering
│   ├── landing.html
│   ├── login.html
│   └── register.html
├── database/
│   ├── db.py              # Database helper functions (get_db, init_db, close_db)
│   └── __init__.py
└── venv/                  # Virtual environment (created during setup)
```

## Architecture Overview

- **Framework**: Flask web application.
- **Database**: SQLite with SQLAlchemy-like row factory for convenient access.
- **Database Connection**: Managed via Flask's `g` object; connections are opened per request and closed automatically using `teardown_appcontext`.
- **Models**: Defined via raw SQL in `database/db.py` (`init_db` function). Includes `users` and `expenses` tables.
- **Routing**: 
  - `/` – Landing page.
  - `/register` – User registration (GET/POST).
  - `/login` – Login page (placeholder).
  - Additional placeholder routes for logout, profile, expense management (to be implemented in later steps).
- **Template Engine**: Jinja2 (default with Flask).
- **Static Files**: Served from the `static/` directory.
- **Security**: Uses a hardcoded secret key for session/flash messages; **must be changed** in production.
- **Environment**: Runs on port 5001 with debug enabled in development.

## Common Tasks

- **Adding a new route**: Edit `app.py`, add a new `@app.route` decorator and corresponding view function. Create a template in `templates/` if needed.
- **Modifying the database schema**: Edit the `CREATE TABLE` statements in `database/db.py::init_db()`. Remember to handle migrations appropriately (currently uses `CREATE TABLE IF NOT EXISTS`).
- **Adding static assets**: Place CSS in `static/css/`, JavaScript in `static/js/`, and reference them in templates with `url_for('static', filename='css/style.css')`.
- **Running linting/formatting**: Not configured by default; you can add tools like `flake8` or `black` to `requirements.txt` as needed.

## Notes

- The application is structured for a tutorial where students implement features incrementally (as indicated by placeholder comments).
- All database operations use parameterized queries to prevent SQL injection.
- Flash messages are used for user feedback; ensure templates display them (they are expected to be present in base templates).
- When deploying to production, set `app.secret_key` from an environment variable and disable debug mode.
Warnings and things to avoid
Never use raw string returns for stub routes once a step is implemented — always render a template
Never hardcode URLs in templates — always use url_for()
Never put DB logic in route functions — it belongs in database/db.py
Never install new packages mid-feature without flagging it — keep requirements.txt in sync
Never use JS frameworks — the frontend is intentionally vanilla
database/db.py is currently empty — do not assume helpers exist until the step that implements them
FK enforcement is manual — SQLite foreign keys are off by default; get_db() must run PRAGMA foreign_keys = ON on every connection
The app runs on port 5001, not the Flask default 5000 — don't change this