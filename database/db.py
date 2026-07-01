import os
import sqlite3
from datetime import datetime

from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "expense_tracker.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name     TEXT    NOT NULL,
            email         TEXT    UNIQUE NOT NULL,
            password_hash TEXT    NOT NULL,
            created_at    TEXT    DEFAULT (datetime('now')),
            updated_at    TEXT    DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id),
            amount      REAL    NOT NULL,
            category    TEXT    NOT NULL,
            date        TEXT    NOT NULL,
            description TEXT,
            created_at  TEXT    DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS income (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id),
            amount      REAL    NOT NULL,
            source      TEXT    NOT NULL,
            date        TEXT    NOT NULL,
            description TEXT,
            created_at  TEXT    DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    conn.close()


def create_user(full_name, email, password):
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO users (full_name, email, password_hash) VALUES (?, ?, ?)",
        (full_name, email, generate_password_hash(password)),
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id


def get_user_by_email(email):
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE email = ?", (email,)
    ).fetchone()
    conn.close()
    return user


def get_user_by_id(user_id):
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    conn.close()
    return user


def seed_db():
    conn = get_db()

    row = conn.execute("SELECT COUNT(*) FROM users").fetchone()
    if row[0] > 0:
        conn.close()
        return

    cursor = conn.execute(
        "INSERT INTO users (full_name, email, password_hash) VALUES (?, ?, ?)",
        ("Demo User", "demo@spendly.com", generate_password_hash("demo123")),
    )
    user_id = cursor.lastrowid

    # Build dates relative to today so the demo data always includes the
    # current month, instead of drifting stale as real time passes.
    now = datetime.now()

    def month_date(months_ago, day):
        total = (now.year * 12 + (now.month - 1)) - months_ago
        year, month = divmod(total, 12)
        month += 1
        return f"{year:04d}-{month:02d}-{day:02d}"

    expenses = [
        # Two months ago
        (user_id, 450.00,  "Food",          month_date(2, 1), "Groceries from D-Mart"),
        (user_id, 120.00,  "Transport",     month_date(2, 2), "Metro card recharge"),
        (user_id, 1200.00, "Bills",         month_date(2, 3), "Electricity bill"),
        (user_id, 350.00,  "Health",        month_date(2, 5), "Pharmacy — vitamins"),
        (user_id, 500.00,  "Entertainment", month_date(2, 6), "Movie tickets"),
        (user_id, 800.00,  "Shopping",      month_date(2, 7), "New earphones"),
        (user_id, 200.00,  "Other",         month_date(2, 8), "Miscellaneous"),
        (user_id, 180.00,  "Food",          month_date(2, 8), "Lunch with colleagues"),
        # Last month
        (user_id, 520.00,  "Food",          month_date(1, 2), "Weekly groceries"),
        (user_id, 250.00,  "Transport",     month_date(1, 4), "Cab rides"),
        (user_id, 1400.00, "Bills",         month_date(1, 5), "Rent contribution"),
        (user_id, 600.00,  "Shopping",      month_date(1, 10), "Clothing"),
        (user_id, 300.00,  "Health",        month_date(1, 14), "Doctor visit"),
        (user_id, 150.00,  "Entertainment", month_date(1, 18), "Streaming subscriptions"),
        (user_id, 420.00,  "Food",          month_date(1, 22), "Restaurant dinner"),
        # This month
        (user_id, 680.00,  "Food",          month_date(0, 1), "Groceries — Big Basket"),
        (user_id, 1500.00, "Bills",         month_date(0, 3), "Electricity + internet"),
        (user_id, 200.00,  "Transport",     month_date(0, 5), "Auto and cab rides"),
        (user_id, 450.00,  "Health",        month_date(0, 8), "Gym membership"),
        (user_id, 900.00,  "Shopping",      month_date(0, 10), "New shoes"),
        (user_id, 350.00,  "Entertainment", month_date(0, 14), "Concert tickets"),
        (user_id, 280.00,  "Food",          month_date(0, 17), "Team lunch"),
        (user_id, 120.00,  "Transport",     month_date(0, 19), "Metro monthly pass"),
        (user_id, 175.00,  "Other",         month_date(0, 21), "Stationery and misc"),
    ]

    conn.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        expenses,
    )

    income_entries = [
        (user_id, 50000.00, "Salary",    month_date(2, 1), "Monthly salary"),
        (user_id,  5000.00, "Freelance", month_date(2, 15), "Web design project"),
        (user_id, 50000.00, "Salary",    month_date(1, 1), "Monthly salary"),
        (user_id,  3500.00, "Freelance", month_date(1, 20), "Logo design"),
        (user_id, 50000.00, "Salary",    month_date(0, 1), "Monthly salary"),
        (user_id,  8000.00, "Freelance", month_date(0, 10), "App development project"),
    ]
    conn.executemany(
        "INSERT INTO income (user_id, amount, source, date, description) VALUES (?, ?, ?, ?, ?)",
        income_entries,
    )

    conn.commit()
    conn.close()

def close_db(e=None):
    """Dummy function to maintain compatibility with app.py"""
    pass


def get_user_expenses_this_month(user_id):
    """Get all expenses for a user for the current month"""
    conn = get_db()
    try:
        # Get current year-month
        from datetime import datetime
        current_month = datetime.now().strftime("%Y-%m")

        expenses = conn.execute("""
            SELECT * FROM expenses
            WHERE user_id = ? AND date LIKE ?
            ORDER BY date DESC
        """, (user_id, f"{current_month}%")).fetchall()
        return expenses
    finally:
        conn.close()


def get_user_income_this_month(user_id):
    """Get all income for a user for the current month"""
    conn = get_db()
    try:
        from datetime import datetime
        current_month = datetime.now().strftime("%Y-%m")
        income = conn.execute("""
            SELECT * FROM income
            WHERE user_id = ? AND date LIKE ?
            ORDER BY date DESC
        """, (user_id, f"{current_month}%")).fetchall()
        return income
    finally:
        conn.close()


def add_income(user_id, amount, source, date, description):
    """Add a new income entry for a user"""
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO income (user_id, amount, source, date, description) VALUES (?, ?, ?, ?, ?)",
            (user_id, amount, source, date, description)
        )
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def get_expenses_by_category(user_id):
    """Get expenses grouped by category for the current month"""
    conn = get_db()
    try:
        from datetime import datetime
        current_month = datetime.now().strftime("%Y-%m")

        categories = conn.execute("""
            SELECT category, SUM(amount) as total
            FROM expenses
            WHERE user_id = ? AND date LIKE ?
            GROUP BY category
        """, (user_id, f"{current_month}%")).fetchall()
        return categories
    finally:
        conn.close()


def get_recent_transactions(user_id, limit=5):
    """Get recent transactions for a user"""
    conn = get_db()
    try:
        transactions = conn.execute("""
            SELECT * FROM expenses
            WHERE user_id = ?
            ORDER BY date DESC, created_at DESC
            LIMIT ?
        """, (user_id, limit)).fetchall()
        return transactions
    finally:
        conn.close()


def get_all_user_transactions(user_id):
    """Get all transactions for a user"""
    conn = get_db()
    try:
        transactions = conn.execute("""
            SELECT * FROM expenses
            WHERE user_id = ?
            ORDER BY date DESC, created_at DESC
        """, (user_id,)).fetchall()
        return transactions
    finally:
        conn.close()


def _filtered_where(user_id, from_date, to_date, q):
    conditions = ["user_id = ?"]
    params = [user_id]
    if from_date:
        conditions.append("date >= ?")
        params.append(from_date)
    if to_date:
        conditions.append("date <= ?")
        params.append(to_date)
    if q:
        conditions.append("LOWER(description) LIKE ?")
        params.append(f"%{q.lower()}%")
    return " AND ".join(conditions), params


def get_filtered_transactions(user_id, from_date=None, to_date=None, q=None, limit=20, offset=0):
    """Return a page of expenses for user_id filtered by optional date bounds and keyword."""
    conn = get_db()
    try:
        where, params = _filtered_where(user_id, from_date, to_date, q)
        sql = (
            "SELECT * FROM expenses "
            "WHERE {} "
            "ORDER BY date DESC, created_at DESC "
            "LIMIT ? OFFSET ?"
        ).format(where)
        return conn.execute(sql, params + [limit, offset]).fetchall()
    finally:
        conn.close()


def count_filtered_transactions(user_id, from_date=None, to_date=None, q=None):
    """Return total row count matching the given filters (for pagination)."""
    conn = get_db()
    try:
        where, params = _filtered_where(user_id, from_date, to_date, q)
        row = conn.execute(
            f"SELECT COUNT(*) FROM expenses WHERE {where}", params
        ).fetchone()
        return row[0]
    finally:
        conn.close()


def add_expense(user_id, amount, category, date, description):
    """Add a new expense for a user"""
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            (user_id, amount, category, date, description)
        )
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def get_expense_by_id(expense_id):
    """Get an expense by its ID"""
    conn = get_db()
    try:
        expense = conn.execute(
            "SELECT * FROM expenses WHERE id = ?", (expense_id,)
        ).fetchone()
        return expense
    finally:
        conn.close()


def update_expense(expense_id, amount, category, date, description):
    """Update an existing expense"""
    conn = get_db()
    try:
        conn.execute(
            """UPDATE expenses
               SET amount = ?, category = ?, date = ?, description = ?
               WHERE id = ?""",
            (amount, category, date, description, expense_id)
        )
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def delete_expense_helper(expense_id):
    """Delete an expense by its ID"""
    conn = get_db()
    try:
        conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def get_monthly_expense_summary(user_id, year_month):
    """Return list of (category, total) rows for the given YYYY-MM."""
    conn = get_db()
    try:
        return conn.execute(
            """
            SELECT category, SUM(amount) AS total
            FROM expenses
            WHERE user_id = ? AND date LIKE ?
            GROUP BY category
            ORDER BY total DESC
            """,
            (user_id, f"{year_month}%"),
        ).fetchall()
    finally:
        conn.close()


def get_monthly_income_total(user_id, year_month):
    """Return total income as float for the given YYYY-MM, or 0.0 if none."""
    conn = get_db()
    try:
        row = conn.execute(
            """
            SELECT COALESCE(SUM(amount), 0.0) AS total
            FROM income
            WHERE user_id = ? AND date LIKE ?
            """,
            (user_id, f"{year_month}%"),
        ).fetchone()
        return float(row["total"]) if row else 0.0
    finally:
        conn.close()


def get_monthly_expense_totals(user_id, months=6):
    """Return monthly expense totals for the last `months` calendar months.

    Each entry: {'year_month': 'YYYY-MM', 'label': 'Mon', 'total': float}.
    Oldest month first, current month last. Months with no expenses come
    back as 0.0 so the series has no gaps.
    """
    now = datetime.now()

    keys = []
    for i in range(months - 1, -1, -1):
        total_months = (now.year * 12 + (now.month - 1)) - i
        year, month = divmod(total_months, 12)
        month += 1
        keys.append(f"{year:04d}-{month:02d}")

    conn = get_db()
    try:
        rows = conn.execute(
            """
            SELECT strftime('%Y-%m', date) AS ym, SUM(amount) AS total
            FROM expenses
            WHERE user_id = ? AND date >= ?
            GROUP BY ym
            """,
            (user_id, f"{keys[0]}-01"),
        ).fetchall()
    finally:
        conn.close()

    totals_by_key = {row["ym"]: float(row["total"]) for row in rows}

    return [
        {
            "year_month": key,
            "label": datetime.strptime(key, "%Y-%m").strftime("%b"),
            "total": totals_by_key.get(key, 0.0),
        }
        for key in keys
    ]
