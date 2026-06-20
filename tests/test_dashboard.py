import importlib
import os
import tempfile
import pytest
from flask import Flask, session

@pytest.fixture
def client():
    """Create a test client for the app with a temporary database."""
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp()

    # Import database.db module
    import database.db
    # Override the DB_PATH
    original_db_path = database.db.DB_PATH
    database.db.DB_PATH = db_path

    # Reload the database.db module to ensure our override is used
    importlib.reload(database.db)

    # Import the app module
    import app
    # Reload the app module to ensure it uses the reloaded database.db and runs its initialization
    importlib.reload(app)
    from app import app

    with app.test_client() as client:
        with app.app_context():
            # The app.py's module level code has already run (on import/reload), which includes init_db() and seed_db()
            yield client

    # Clean up: close and remove the temporary database file
    os.close(db_fd)
    os.unlink(db_path)
    # Note: We do not restore the original DB_PATH in database.db because the module is reloaded in each fixture


def test_dashboard_requires_login(client):
    """Test that accessing the dashboard without login redirects to login page."""
    response = client.get('/dashboard', follow_redirects=False)
    assert response.status_code == 302  # Redirect
    assert '/login' in response.location


def test_dashboard_after_login(client):
    """Test that logging in and accessing the dashboard shows the dashboard page."""
    # Log in as the demo user (seeded by seed_db)
    response = client.post('/login', data={
        'email': 'demo@spendly.com',
        'password': 'demo123'
    }, follow_redirects=False)
    # Login should redirect to dashboard on success
    assert response.status_code == 302
    assert '/dashboard' in response.location

    # Follow the redirect to dashboard
    response = client.get('/dashboard')
    assert response.status_code == 200
    # Check that the dashboard template is rendered
    assert b'Dashboard - Spendly' in response.data
    # Check that the user's full name is displayed (from seed data: Demo User)
    assert b'Welcome back, Demo User!' in response.data


def test_dashboard_displays_summary_cards_with_test_data(client):
    """Test that the dashboard displays the summary cards with correct data."""
    # We will create a new user and add expenses for the current month.
    # First, register a new user
    response = client.post('/register', data={
        'full_name': 'Test User',
        'email': 'test2@example.com',
        'password': 'testpassword123',
        'confirm_password': 'testpassword123'
    }, follow_redirects=False)
    # Should redirect to landing
    assert response.status_code == 302
    assert '/' in response.location

    # Log in
    response = client.post('/login', data={
        'email': 'test2@example.com',
        'password': 'testpassword123'
    }, follow_redirects=False)
    assert response.status_code == 302
    assert '/dashboard' in response.location

    # Add expenses for the current month
    from database.db import get_db, add_expense
    from datetime import datetime
    current_month = datetime.now().strftime("%Y-%m")
    test_date = f"{current_month}-01"

    conn = get_db()
    user = conn.execute("SELECT id FROM users WHERE email = ?", ('test2@example.com',)).fetchone()
    user_id = user['id']
    conn.close()

    # Add test expenses
    add_expense(user_id, 50.0, 'Food', test_date, 'Lunch')
    add_expense(user_id, 30.0, 'Transport', test_date, 'Bus fare')
    add_expense(user_id, 100.0, 'Entertainment', test_date, 'Concert ticket')

    # Now access the dashboard
    response = client.get('/dashboard')
    assert response.status_code == 200

    # Check that the summary cards show the correct totals
    # Total expenses: 50 + 30 + 100 = 180
    # Total income: 0 (since income tracking is not implemented)
    # Remaining balance: -180
    # Transaction count: 3

    # We'll check for the amounts in the response
    # Note: the amounts are formatted as dollars with two decimal places
    assert b'$180.00' in response.data  # total expenses
    assert b'$0.00' in response.data    # total income
    # Remaining balance should be negative and displayed in red (negative class)
    # We'll check for the value and the negative class
    assert b'-$180.00' in response.data
    # Transaction count
    assert b'3' in response.data


def test_dashboard_displays_category_breakdown(client):
    """Test that the dashboard displays expense breakdown by category."""
    # Create and log in a user
    client.post('/register', data={
        'full_name': 'Test User',
        'email': 'test3@example.com',
        'password': 'testpassword123',
        'confirm_password': 'testpassword123'
    })
    client.post('/login', data={
        'email': 'test3@example.com',
        'password': 'testpassword123'
    })

    # Add expenses in different categories
    from database.db import get_db, add_expense
    from datetime import datetime
    current_month = datetime.now().strftime("%Y-%m")
    test_date = f"{current_month}-01"

    conn = get_db()
    user = conn.execute("SELECT id FROM users WHERE email = ?", ('test3@example.com',)).fetchone()
    user_id = user['id']
    conn.close()

    # Add expenses: Food: 100, Transport: 50, Food: 50 (total Food: 150, Transport: 50)
    add_expense(user_id, 100.0, 'Food', test_date, 'Groceries')
    add_expense(user_id, 50.0, 'Transport', test_date, 'Taxi')
    add_expense(user_id, 50.0, 'Food', test_date, 'Snacks')

    response = client.get('/dashboard')
    assert response.status_code == 200

    # Check that the category breakdown is displayed
    # Food: total 150, percentage: (150/200)*100 = 75.0%
    # Transport: total 50, percentage: (50/200)*100 = 25.0%
    assert b'Food' in response.data
    assert b'$150.00' in response.data
    assert b'75.0%' in response.data
    assert b'Transport' in response.data
    assert b'$50.00' in response.data
    assert b'25.0%' in response.data


def test_dashboard_displays_recent_transactions(client):
    """Test that the dashboard displays recent transactions."""
    # Create and log in a user
    client.post('/register', data={
        'full_name': 'Test User',
        'email': 'test4@example.com',
        'password': 'testpassword123',
        'confirm_password': 'testpassword123'
    })
    client.post('/login', data={
        'email': 'test4@example.com',
        'password': 'testpassword123'
    })

    # Add expenses
    from database.db import get_db, add_expense
    from datetime import datetime
    current_month = datetime.now().strftime("%Y-%m")
    test_date = f"{current_month}-01"

    conn = get_db()
    user = conn.execute("SELECT id FROM users WHERE email = ?", ('test4@example.com',)).fetchone()
    user_id = user['id']
    conn.close()

    # Add three expenses
    add_expense(user_id, 10.0, 'Food', test_date, 'Breakfast')
    add_expense(user_id, 20.0, 'Transport', test_date, 'Bus')
    add_expense(user_id, 30.0, 'Food', test_date, 'Lunch')

    response = client.get('/dashboard')
    assert response.status_code == 200

    # Check that the recent transactions table is displayed
    # The dashboard shows the 5 most recent transactions (we have 3)
    # We should see the three transactions in the table
    assert b'Breakfast' in response.data
    assert b'$10.00' in response.data
    assert b'Bus' in response.data
    assert b'$20.00' in response.data
    assert b'Lunch' in response.data
    assert b'$30.00' in response.data

    # Also check that the table headers are present
    assert b'Date' in response.data
    assert b'Category' in response.data
    assert b'Description' in response.data
    assert b'Amount' in response.data


def test_dashboard_empty_state(client):
    """Test that the dashboard shows an empty state when there are no transactions."""
    # Create and log in a user with no expenses
    client.post('/register', data={
        'full_name': 'Test User',
        'email': 'test5@example.com',
        'password': 'testpassword123',
        'confirm_password': 'testpassword123'
    })
    client.post('/login', data={
        'email': 'test5@example.com',
        'password': 'testpassword123'
    })

    response = client.get('/dashboard')
    assert response.status_code == 200

    # Check for the empty state message
    assert b'No transactions yet. Start by adding your first expense!' in response.data
    # Check for the action button to add expense
    assert b'Add Expense' in response.data
    # Check that the category breakdown shows "No expenses yet"
    assert b'No expenses yet' in response.data


def test_dashboard_recent_transactions_limit(client):
    """Test that the dashboard shows only the 5 most recent transactions."""
    # Create and log in a user
    client.post('/register', data={
        'full_name': 'Test User',
        'email': 'test8@example.com',
        'password': 'testpassword123',
        'confirm_password': 'testpassword123'
    })
    client.post('/login', data={
        'email': 'test8@example.com',
        'password': 'testpassword123'
    })

    # Add six expenses for the current month with different dates to test ordering
    from database.db import get_db, add_expense
    from datetime import datetime
    current_month = datetime.now().strftime("%Y-%m")
    # We'll use different days in the current month
    dates = [
        f"{current_month}-01",
        f"{current_month}-02",
        f"{current_month}-03",
        f"{current_month}-04",
        f"{current_month}-05",
        f"{current_month}-06"
    ]
    amounts = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0]

    conn = get_db()
    user = conn.execute("SELECT id FROM users WHERE email = ?", ('test8@example.com',)).fetchone()
    user_id = user['id']
    conn.close()

    # Add expenses in ascending order of date (oldest first)
    for i in range(6):
        add_expense(user_id, amounts[i], 'Food', dates[i], f'Expense {i+1}')

    response = client.get('/dashboard')
    assert response.status_code == 200

    # The dashboard should show the 5 most recent transactions (dates 02 through 06, assuming today is after 06th)
    # But note: the query orders by date DESC, so the most recent are the highest dates.
    # We added dates from 01 to 06, so the most recent are 06, 05, 04, 03, 02.
    # We should see amounts 60, 50, 40, 30, 20 (for dates 06, 05, 04, 03, 02)
    # We should NOT see the oldest amount (10.00 from date 01)

    # Check that the five most recent amounts are present
    assert b'$60.00' in response.data
    assert b'$50.00' in response.data
    assert b'$40.00' in response.data
    assert b'$30.00' in response.data
    assert b'$20.00' in response.data
    # Check that the oldest amount is NOT present
    assert b'$10.00' not in response.data


def test_dashboard_quick_actions(client):
    """Test that the dashboard shows quick action buttons with correct links."""
    # Create and log in a user
    client.post('/register', data={
        'full_name': 'Test User',
        'email': 'test6@example.com',
        'password': 'testpassword123',
        'confirm_password': 'testpassword123'
    })
    client.post('/login', data={
        'email': 'test6@example.com',
        'password': 'testpassword123'
    })

    response = client.get('/dashboard')
    assert response.status_code == 200

    # Check for the quick action buttons and their hrefs
    # Add Expense button
    assert b'href="/expenses/add"' in response.data
    # View All button
    assert b'href="/view_transactions"' in response.data
    # Profile button
    assert b'href="/profile"' in response.data
    # Logout button
    assert b'href="/logout"' in response.data


def test_dashboard_displays_current_date_and_time(client):
    """Test that the dashboard displays the current date and time."""
    # Create and log in a user
    client.post('/register', data={
        'full_name': 'Test User',
        'email': 'test7@example.com',
        'password': 'testpassword123',
        'confirm_password': 'testpassword123'
    })
    client.post('/login', data={
        'email': 'test7@example.com',
        'password': 'testpassword123'
    })

    response = client.get('/dashboard')
    assert response.status_code == 200

    # Check that the date and time are displayed (we can't check the exact value because it changes,
    # but we can check that the elements are present)
    # Look for the welcome-info section
    assert b'welcome-info' in response.data
    # Check for the date and time icons (we used emojis in the template)
    assert b'📅' in response.data  # date icon
    assert b'🕐' in response.data  # time icon


if __name__ == '__main__':
    pytest.main([__file__])