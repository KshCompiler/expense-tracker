import os
import sqlite3

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

    expenses = [
        (user_id, 450.00,  "Food",          "2026-04-01", "Groceries from D-Mart"),
        (user_id, 120.00,  "Transport",     "2026-04-02", "Metro card recharge"),
        (user_id, 1200.00, "Bills",         "2026-04-03", "Electricity bill"),
        (user_id, 350.00,  "Health",        "2026-04-05", "Pharmacy — vitamins"),
        (user_id, 500.00,  "Entertainment", "2026-04-06", "Movie tickets"),
        (user_id, 800.00,  "Shopping",      "2026-04-07", "New earphones"),
        (user_id, 200.00,  "Other",         "2026-04-08", "Miscellaneous"),
        (user_id, 180.00,  "Food",          "2026-04-08", "Lunch with colleagues"),
    ]

    conn.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        expenses,
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
    # For now, returning empty list as income tracking is not implemented
    # This would be implemented when income tracking is added
    conn = get_db()
    try:
        return []
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
