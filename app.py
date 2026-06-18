from flask import Flask, render_template, request, redirect, url_for, flash
from database.db import get_db, init_db, close_db, create_user, get_user_by_email
import os
import re

app = Flask(__name__)
app.secret_key = 'dev-secret-key-change-in-production'  # Needed for flash messages

# Email validation regex
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

# Initialize database
init_db()

# Close database connection after each request
@app.teardown_appcontext
def teardown_db(e=None):
    close_db(e)


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


@app.route("/login")
def login():
    return render_template("login.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    return "Logout — coming in Step 3"


@app.route("/profile")
def profile():
    return "Profile page — coming in Step 4"


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)