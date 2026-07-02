from flask import Flask, render_template, request, redirect, url_for, flash, session, abort, jsonify
from database.db import get_db, init_db, close_db, create_user, get_user_by_email
from werkzeug.security import check_password_hash
from dotenv import load_dotenv
import os
import re
import json
import base64
import secrets
from datetime import datetime
from openai import OpenAI

load_dotenv()

app = Flask(__name__)
app.secret_key = 'dev-secret-key-change-in-production'  # Needed for flash messages
# Defense-in-depth: caps the request body Werkzeug will parse before any route
# code runs, independent of the in-route 5MB bill-image check further below.
app.config['MAX_CONTENT_LENGTH'] = 6 * 1024 * 1024

# Email validation regex
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
VALID_CATEGORIES = {'Food', 'Transport', 'Bills', 'Health', 'Entertainment', 'Shopping', 'Other'}
VALID_INCOME_SOURCES = {'Salary', 'Freelance', 'Business', 'Investment', 'Gift', 'Other'}

# Bill-scanning (OCR billing) settings
ALLOWED_BILL_MIME_TYPES = {'image/jpeg', 'image/png', 'image/webp'}
MAX_BILL_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB
# Groq's vision-capable model lineup changes over time — override via env if this one is retired.
BILL_OCR_MODEL = os.environ.get('BILL_OCR_MODEL', 'meta-llama/llama-4-scout-17b-16e-instruct')

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


def _build_bill_extraction_prompt(valid_values, field_name, doc_kind):
    values_list = ", ".join(sorted(valid_values))
    return (
        f"You are reading a photo of a {doc_kind} for a personal finance app. "
        "Extract exactly these fields and reply with STRICT JSON only — no markdown code "
        "fences, no commentary, nothing before or after the JSON object:\n"
        '{"amount": <number or null>, "' + field_name + '": <one of [' + values_list + '] or null>, '
        '"date": <"YYYY-MM-DD" or null>, "description": <short string under 60 characters or null>}\n\n'
        "Rules:\n"
        "- amount is the total amount on the document, as a plain number with no currency symbol or commas.\n"
        f"- {field_name} must be exactly one of the listed values, or null if you're not confident.\n"
        "- date is the date on the document in YYYY-MM-DD format, or null if illegible or absent.\n"
        "- description briefly names the merchant/payer or what the document is for, or null if unclear.\n"
        "- If you cannot confidently read a field, return null for it — never guess.\n"
        f"- If the image is not a {doc_kind} at all, return null for every field."
    )


def _format_currency_short(amount):
    if amount >= 1000:
        value = amount / 1000
        return f"₹{value:.0f}k" if value == int(value) else f"₹{value:.1f}k"
    return f"₹{amount:.0f}"


def _rounded_top_bar_path(x, y, width, height, radius=6):
    """SVG path for a bar rect rounded on its top two corners only, flat on the baseline."""
    r = min(radius, width / 2, height) if height > 0 else 0
    if r <= 0:
        return f"M{x},{y} L{x + width},{y} L{x + width},{y + height} L{x},{y + height} Z"
    return (
        f"M{x},{y + r} "
        f"Q{x},{y} {x + r},{y} "
        f"L{x + width - r},{y} "
        f"Q{x + width},{y} {x + width},{y + r} "
        f"L{x + width},{y + height} "
        f"L{x},{y + height} Z"
    )


def _build_trend_chart(monthly_trend, width=620, height=210, pad_x=28, pad_top=40, pad_bottom=26, bar_gap_ratio=0.36):
    totals = [m['total'] for m in monthly_trend]
    max_total = max(totals) if totals else 0
    has_data = max_total > 0

    n = len(monthly_trend)
    usable_width = width - (2 * pad_x)
    usable_height = height - pad_top - pad_bottom
    slot_width = usable_width / n if n else 0
    bar_width = slot_width * (1 - bar_gap_ratio)
    baseline = pad_top + usable_height

    bars = []
    for i, m in enumerate(monthly_trend):
        slot_x = pad_x + (i * slot_width)
        bar_x = slot_x + (slot_width - bar_width) / 2
        ratio = (m['total'] / max_total) if max_total > 0 else 0
        bar_height = usable_height * ratio
        bar_y = baseline - bar_height
        label_x = round(slot_x + slot_width / 2, 1)
        value_y = round(max(bar_y - 8, 10), 1)
        display_total = _format_currency_short(m['total']) if m['total'] > 0 else ''
        chip_width = round(10 + len(display_total) * 6.3, 1) if display_total else 0
        bars.append({
            'path': _rounded_top_bar_path(round(bar_x, 1), round(bar_y, 1), round(bar_width, 1), round(bar_height, 1)),
            'label_x': label_x,
            'label_y': round(baseline + 20, 1),
            'value_y': value_y,
            'diamond_y': round(value_y - 18, 1),
            'chip_x': round(label_x - chip_width / 2, 1),
            'chip_y': round(value_y - 12, 1),
            'chip_width': chip_width,
            'label': m['label'],
            'total': m['total'],
            'display_total': display_total,
            'is_zero': m['total'] <= 0,
            'title': f"{m['label']} · ₹{m['total']:,.0f}",
            'is_current': i == n - 1,
            'delay': round(i * 0.05, 2),
        })

    gridlines = [round(baseline - (usable_height * frac), 1) for frac in (0.33, 0.66)] if max_total > 0 else []

    current_total = totals[-1] if totals else 0
    previous_total = totals[-2] if len(totals) >= 2 else None
    delta_pct = None
    trend_direction = 'flat'
    if previous_total is not None:
        if previous_total > 0:
            delta_pct = abs(((current_total - previous_total) / previous_total) * 100)
            if current_total > previous_total:
                trend_direction = 'up'
            elif current_total < previous_total:
                trend_direction = 'down'
        elif current_total > 0:
            delta_pct = 100.0
            trend_direction = 'up'
        else:
            delta_pct = 0.0

    return {
        'width': width,
        'height': height,
        'baseline': round(baseline, 1),
        'bars': bars,
        'gridlines': gridlines,
        'has_data': has_data,
        'current_total': current_total,
        'delta_pct': delta_pct,
        'trend_direction': trend_direction,
    }


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
    from database.db import get_user_expenses_this_month, get_user_income_this_month, get_expenses_by_category, get_recent_transactions, get_monthly_expense_totals
    expenses = get_user_expenses_this_month(user_id)
    income = get_user_income_this_month(user_id)
    categories = get_expenses_by_category(user_id)
    recent_transactions = get_recent_transactions(user_id)
    monthly_trend = get_monthly_expense_totals(user_id)
    trend_chart = _build_trend_chart(monthly_trend)

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
        'has_transactions': transaction_count > 0,
        'trend_chart': trend_chart,
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


def _sniff_image_mimetype(data):
    """Identify the image format from its actual bytes rather than trusting the
    client-supplied Content-Type, which is trivially spoofable."""
    if data.startswith(b'\xff\xd8\xff'):
        return 'image/jpeg'
    if data.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'image/png'
    if data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        return 'image/webp'
    return None


def _extract_financial_document(field_name, valid_values, doc_kind):
    """Shared by /expenses/extract-bill and /income/extract-bill: validate the
    uploaded image, ask the vision model to read it, and re-validate every
    field server-side before handing it back. `field_name` is "category" for
    expenses or "source" for income; `valid_values` constrains that field."""
    file = request.files.get('bill_image')
    if not file or file.filename == '':
        return jsonify({"error": "No image was uploaded."}), 400

    image_bytes = file.read(MAX_BILL_IMAGE_BYTES + 1)
    if not image_bytes:
        return jsonify({"error": "That image appears to be empty."}), 400
    if len(image_bytes) > MAX_BILL_IMAGE_BYTES:
        return jsonify({"error": "That image is too large — please use a photo under 5MB."}), 400

    mimetype = _sniff_image_mimetype(image_bytes)
    if mimetype not in ALLOWED_BILL_MIME_TYPES:
        return jsonify({"error": "Please upload a JPG, PNG, or WEBP image."}), 400

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return jsonify({"error": "Document scanning isn't available right now — please enter the details manually."}), 503

    try:
        b64_image = base64.b64encode(image_bytes).decode('utf-8')
        data_url = f"data:{mimetype};base64,{b64_image}"

        client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
        response = client.chat.completions.create(
            model=BILL_OCR_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": _build_bill_extraction_prompt(valid_values, field_name, doc_kind)},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ],
            temperature=0,
        )
        raw = response.choices[0].message.content.strip()
        raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            raise ValueError("model response was not a JSON object")
    except Exception as e:
        app.logger.error("Document extraction error: %s", e, exc_info=True)
        return jsonify({"error": "Couldn't read that image — please enter the details manually."}), 500

    # Never trust the model's output as final — re-validate every field server-side.
    amount = parsed.get("amount")
    try:
        amount = float(amount) if amount is not None else None
        if amount is not None and amount <= 0:
            amount = None
    except (TypeError, ValueError):
        amount = None

    field_value = parsed.get(field_name)
    if field_value not in valid_values:
        field_value = None

    date = parsed.get("date")
    if date:
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except (TypeError, ValueError):
            date = None
    else:
        date = None

    description = parsed.get("description")
    if isinstance(description, str):
        description = description.strip()[:120] or None
    else:
        description = None

    result = {"amount": amount, "date": date, "description": description, field_name: field_value}
    return jsonify(result)


@app.route("/expenses/extract-bill", methods=["POST"])
def extract_bill():
    if 'user_id' not in session:
        return jsonify({"error": "Please log in to scan a bill."}), 401

    check_csrf()
    return _extract_financial_document('category', VALID_CATEGORIES, 'shopping bill or receipt')


@app.route("/income/extract-bill", methods=["POST"])
def extract_income_bill():
    if 'user_id' not in session:
        return jsonify({"error": "Please log in to scan a document."}), 401

    check_csrf()
    return _extract_financial_document('source', VALID_INCOME_SOURCES, 'payslip, invoice, or proof of income')


@app.route("/view_transactions")
def view_transactions():
    if 'user_id' not in session:
        flash("Please log in to view transactions.", "error")
        return redirect(url_for("login"))

    user_id = session['user_id']
    PER_PAGE = 20

    raw_from = request.args.get("from_date", "").strip()
    raw_to   = request.args.get("to_date",   "").strip()
    q        = request.args.get("q", "").strip() or None

    from_date = None
    to_date   = None

    if raw_from:
        try:
            datetime.strptime(raw_from, "%Y-%m-%d")
            from_date = raw_from
        except ValueError:
            pass

    if raw_to:
        try:
            datetime.strptime(raw_to, "%Y-%m-%d")
            to_date = raw_to
        except ValueError:
            pass

    filter_active = bool(from_date or to_date or q)
    transactions  = None
    total         = 0
    page          = 1
    total_pages   = 1

    if from_date and to_date and from_date > to_date:
        flash("'From' date must be on or before 'To' date.", "error")
    else:
        from database.db import get_filtered_transactions, count_filtered_transactions
        total       = count_filtered_transactions(user_id, from_date, to_date, q)
        total_pages = max(1, -(-total // PER_PAGE))  # ceil division

        try:
            page = int(request.args.get("page", 1))
        except ValueError:
            page = 1
        page = max(1, min(page, total_pages))

        offset       = (page - 1) * PER_PAGE
        transactions = get_filtered_transactions(user_id, from_date, to_date, q, PER_PAGE, offset)

    return render_template(
        "view_transactions.html",
        transactions=transactions,
        from_date=from_date,
        to_date=to_date,
        q=q,
        filter_active=filter_active,
        page=page,
        total_pages=total_pages,
        total=total,
        per_page=PER_PAGE,
    )


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