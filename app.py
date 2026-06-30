from flask import Flask, render_template, request, redirect, url_for, flash, session, abort, jsonify
from database.db import get_db, init_db, close_db, create_user, get_user_by_email
from werkzeug.security import check_password_hash
from dotenv import load_dotenv
import os
import re
import secrets
from datetime import datetime
from openai import OpenAI

load_dotenv()

app = Flask(__name__)
app.secret_key = 'dev-secret-key-change-in-production'  # Needed for flash messages

# Email validation regex
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
VALID_CATEGORIES = {'Food', 'Transport', 'Bills', 'Health', 'Entertainment', 'Shopping', 'Other'}
VALID_INCOME_SOURCES = {'Salary', 'Freelance', 'Business', 'Investment', 'Gift', 'Other'}

# Initialize database
init_db()
# Seed database with demo data
from database.db import seed_db
seed_db()

# Close database connection after each request
@app.teardown_appcontext
def teardown_db(e=None):
    close_db(e)


@app.context_processor
def inject_csrf_token():
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)
    return dict(csrf_token=session['csrf_token'])


def check_csrf():
    token = request.form.get('csrf_token')
    if not token or token != session.get('csrf_token'):
        abort(403)


# ------------------------------------------------------------------ #
# AI suggestions helpers                                              #
# ------------------------------------------------------------------ #

def _fmt_expenses(rows):
    if not rows:
        return "No expenses recorded"
    return ", ".join(f"{r['category']}: ₹{r['total']:.0f}" for r in rows)


def _build_chat_system_prompt(curr_month, curr_expenses, curr_income,
                               prev_month, prev_expenses, prev_income):
    curr_label = datetime.strptime(curr_month, "%Y-%m").strftime("%B %Y")
    prev_label = datetime.strptime(prev_month, "%Y-%m").strftime("%B %Y")

    return (
        "You are a helpful personal finance assistant built into Spendly, an expense tracker app. "
        "You have access to the user's real spending data shown below. Answer their questions "
        "conversationally and concisely — 2 to 4 sentences max. Reference the actual numbers "
        "when relevant. Use ₹ for currency. Never make up data not shown here.\n\n"
        "User's Financial Data:\n"
        f"- {prev_label}: Income ₹{prev_income:.0f} | Expenses: {_fmt_expenses(prev_expenses)}\n"
        f"- {curr_label}: Income ₹{curr_income:.0f} | Expenses: {_fmt_expenses(curr_expenses)}"
    )


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Get form data
        full_name = request.form.get("full_name")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        # Basic validation
        if not full_name or not email or not password or not confirm_password:
            flash("All fields are required!", "error")
            return render_template("register.html")

        # Check if passwords match
        if password != confirm_password:
            flash("Passwords do not match!", "error")
            return render_template("register.html")

        # Email format validation
        if not EMAIL_REGEX.match(email):
            flash("Please enter a valid email address!", "error")
            return render_template("register.html")

        # Password length validation
        if len(password) < 8:
            flash("Password must be at least 8 characters long!", "error")
            return render_template("register.html")

        # Check if user already exists
        existing_user = get_user_by_email(email)

        if existing_user:
            flash("An account with this email already exists!", "error")
            return render_template("register.html")

        # Insert new user
        try:
            create_user(full_name, email, password)
            flash("Account created successfully", "success")
            return redirect(url_for("landing"))
        except Exception as e:
            flash("An error occurred. Please try again.", "error")
            return render_template("register.html")

    # GET request - show registration form
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            flash("Email and password are required!", "error")
            return render_template("login.html")

        # Get user by email
        user = get_user_by_email(email)

        if user and check_password_hash(user['password_hash'], password):
            session.clear()
            session['user_id'] = user['id']
            session['user_email'] = user['email']
            session['user_full_name'] = user['full_name']

            flash("Login successful!", "success")
            return redirect(url_for("landing"))
        else:
            flash("Invalid email or password!", "error")
            return render_template("login.html")

    # GET request - show login form
    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    # Check if user is logged in
    if 'user_id' not in session:
        flash("Please log in to access your dashboard.", "error")
        return redirect(url_for("login"))

    # Get user data
    user_id = session['user_id']

    # Get user info
    from database.db import get_user_by_id
    user = get_user_by_id(user_id)

    # Get today's date and time
    now = datetime.now()
    today_date = now.strftime("%B %d, %Y")
    current_time = now.strftime("%I:%M %p")

    # Get dashboard data using helper functions
    from database.db import get_user_expenses_this_month, get_user_income_this_month, get_expenses_by_category, get_recent_transactions
    expenses = get_user_expenses_this_month(user_id)
    income = get_user_income_this_month(user_id)
    categories = get_expenses_by_category(user_id)
    recent_transactions = get_recent_transactions(user_id)

    # Calculate summary statistics
    total_expenses = sum(expense['amount'] for expense in expenses) if expenses else 0
    total_income = sum(income_item['amount'] for income_item in income) if income else 0
    remaining_balance = total_income - total_expenses
    transaction_count = len(expenses)

    # Prepare data for template
    dashboard_data = {
        'user': user,
        'today_date': today_date,
        'current_time': current_time,
        'total_expenses': total_expenses,
        'total_income': total_income,
        'remaining_balance': remaining_balance,
        'transaction_count': transaction_count,
        'categories': categories,
        'recent_transactions': recent_transactions,
        'has_transactions': transaction_count > 0
    }

    return render_template("dashboard.html", **dashboard_data)


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    # Clear session data
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("landing"))






@app.route("/income/add", methods=["GET", "POST"])
def add_income():
    if 'user_id' not in session:
        flash("Please log in to add income.", "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        check_csrf()

        amount = request.form.get("amount")
        source = request.form.get("source")
        date = request.form.get("date")
        description = request.form.get("description")

        if not amount or not source or not date:
            flash("Amount, source, and date are required!", "error")
            return render_template("add_income.html")

        if source not in VALID_INCOME_SOURCES:
            flash("Please select a valid income source!", "error")
            return render_template("add_income.html")

        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            flash("Please enter a valid date!", "error")
            return render_template("add_income.html")

        try:
            amount = float(amount)
            if amount <= 0:
                flash("Amount must be greater than zero!", "error")
                return render_template("add_income.html")
        except ValueError:
            flash("Please enter a valid amount!", "error")
            return render_template("add_income.html")

        from database.db import add_income as db_add_income
        try:
            db_add_income(session['user_id'], amount, source, date, description)
            flash("Income added successfully!", "success")
            return redirect(url_for("dashboard"))
        except Exception:
            flash("An error occurred while adding income. Please try again.", "error")
            return render_template("add_income.html")

    return render_template("add_income.html")


@app.route("/expenses/<int:id>/edit", methods=["GET", "POST"])
def edit_expense(id):
    # Check if user is logged in
    if 'user_id' not in session:
        flash("Please log in to edit expenses.", "error")
        return redirect(url_for("login"))

    # Get the expense to verify it belongs to the user
    from database.db import get_expense_by_id
    expense = get_expense_by_id(id)

    if not expense or expense['user_id'] != session['user_id']:
        flash("Expense not found or you don't have permission to edit it.", "error")
        return redirect(url_for("view_transactions"))

    if request.method == "POST":
        check_csrf()

        # Get form data
        amount = request.form.get("amount")
        category = request.form.get("category")
        date = request.form.get("date")
        description = request.form.get("description")

        # Basic validation
        if not amount or not category or not date:
            flash("Amount, category, and date are required!", "error")
            return render_template("edit_expense.html", expense=expense)

        if category not in VALID_CATEGORIES:
            flash("Please select a valid category!", "error")
            return render_template("edit_expense.html", expense=expense)

        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            flash("Please enter a valid date!", "error")
            return render_template("edit_expense.html", expense=expense)

        try:
            amount = float(amount)
            if amount <= 0:
                flash("Amount must be greater than zero!", "error")
                return render_template("edit_expense.html", expense=expense)
        except ValueError:
            flash("Please enter a valid amount!", "error")
            return render_template("edit_expense.html", expense=expense)

        # Update expense using helper function
        from database.db import update_expense
        try:
            update_expense(id, amount, category, date, description)
            flash("Expense updated successfully!", "success")
            return redirect(url_for("view_transactions"))
        except Exception as e:
            flash("An error occurred while updating the expense. Please try again.", "error")
            return render_template("edit_expense.html", expense=expense)

    # GET request - show edit expense form
    return render_template("edit_expense.html", expense=expense)


@app.route("/expenses/<int:id>/delete", methods=["POST"])
def delete_expense(id):
    # Check if user is logged in
    if 'user_id' not in session:
        flash("Please log in to delete expenses.", "error")
        return redirect(url_for("login"))

    # Get the expense to verify it belongs to the user
    from database.db import get_expense_by_id
    expense = get_expense_by_id(id)

    if not expense or expense['user_id'] != session['user_id']:
        flash("Expense not found or you don't have permission to delete it.", "error")
        return redirect(url_for("view_transactions"))

    check_csrf()

    # Delete expense using helper function
    from database.db import delete_expense_helper
    try:
        delete_expense_helper(id)
        flash("Expense deleted successfully!", "success")
    except Exception as e:
        flash("An error occurred while deleting the expense. Please try again.", "error")

    return redirect(url_for("view_transactions"))


@app.route("/expenses/add", methods=["GET", "POST"])
def add_expense():
    # Check if user is logged in
    if 'user_id' not in session:
        flash("Please log in to add expenses.", "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        check_csrf()

        # Get form data
        amount = request.form.get("amount")
        category = request.form.get("category")
        date = request.form.get("date")
        description = request.form.get("description")

        # Basic validation
        if not amount or not category or not date:
            flash("Amount, category, and date are required!", "error")
            return render_template("add_expense.html")

        if category not in VALID_CATEGORIES:
            flash("Please select a valid category!", "error")
            return render_template("add_expense.html")

        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            flash("Please enter a valid date!", "error")
            return render_template("add_expense.html")

        try:
            amount = float(amount)
            if amount <= 0:
                flash("Amount must be greater than zero!", "error")
                return render_template("add_expense.html")
        except ValueError:
            flash("Please enter a valid amount!", "error")
            return render_template("add_expense.html")

        # Add expense using helper function
        from database.db import add_expense
        try:
            add_expense(session['user_id'], amount, category, date, description)
            flash("Expense added successfully!", "success")
            return redirect(url_for("dashboard"))
        except Exception as e:
            flash("An error occurred while adding the expense. Please try again.", "error")
            return render_template("add_expense.html")

    # GET request - show add expense form
    return render_template("add_expense.html")


@app.route("/view_transactions")
def view_transactions():
    # Check if user is logged in
    if 'user_id' not in session:
        flash("Please log in to view transactions.", "error")
        return redirect(url_for("login"))

    # Get user data
    user_id = session['user_id']

    # Get all transactions using helper function
    from database.db import get_all_user_transactions
    transactions = get_all_user_transactions(user_id)

    return render_template("view_transactions.html", transactions=transactions)


@app.route("/profile")
def profile():
    # Check if user is logged in
    if 'user_id' not in session:
        flash("Please log in to view your profile.", "error")
        return redirect(url_for("login"))

    # Get user data using helper function
    from database.db import get_user_by_id
    user_id = session['user_id']
    user = get_user_by_id(user_id)

    return render_template("profile.html", user=user)


@app.route("/suggestions")
def suggestions():
    if "user_id" not in session:
        flash("Please log in to view suggestions.", "error")
        return redirect(url_for("login"))
    return render_template("suggestions.html")


@app.route("/api/chat", methods=["POST"])
def api_chat():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    user_message = data.get("message", "").strip()
    history = data.get("history", [])

    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    user_id = session["user_id"]
    try:
        now = datetime.now()
        curr_month = now.strftime("%Y-%m")
        prev_month = f"{now.year - 1}-12" if now.month == 1 else f"{now.year}-{now.month - 1:02d}"

        from database.db import get_monthly_expense_summary, get_monthly_income_total
        curr_expenses = get_monthly_expense_summary(user_id, curr_month)
        curr_income   = get_monthly_income_total(user_id, curr_month)
        prev_expenses = get_monthly_expense_summary(user_id, prev_month)
        prev_income   = get_monthly_income_total(user_id, prev_month)

        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not set")

        system_prompt = _build_chat_system_prompt(
            curr_month, curr_expenses, curr_income,
            prev_month, prev_expenses, prev_income,
        )

        messages = [{"role": "system", "content": system_prompt}]
        for turn in history[-10:]:
            if turn.get("role") in ("user", "assistant") and turn.get("content"):
                messages.append({"role": turn["role"], "content": turn["content"]})
        messages.append({"role": "user", "content": user_message})

        client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
        )
        reply = response.choices[0].message.content.strip()
        return jsonify({"reply": reply})

    except Exception as e:
        app.logger.error("Chat error: %s", e, exc_info=True)
        return jsonify({"error": "Failed to get a response"}), 500




if __name__ == "__main__":
    app.run(debug=True, port=5001)