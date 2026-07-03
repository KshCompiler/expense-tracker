def test_add_expense_requires_all_fields(new_user_client):
    resp = new_user_client.post(
        "/api/expenses", json={"amount": "", "category": "", "date": "", "description": None}
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Amount, category, and date are required!"


def test_add_expense_rejects_invalid_category(new_user_client):
    resp = new_user_client.post(
        "/api/expenses",
        json={"amount": "10", "category": "Education", "date": "2026-07-01", "description": None},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Please select a valid category!"


def test_add_expense_rejects_invalid_date(new_user_client):
    resp = new_user_client.post(
        "/api/expenses",
        json={"amount": "10", "category": "Food", "date": "07/01/2026", "description": None},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Please enter a valid date!"


def test_add_expense_rejects_non_numeric_amount(new_user_client):
    resp = new_user_client.post(
        "/api/expenses",
        json={"amount": "abc", "category": "Food", "date": "2026-07-01", "description": None},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Please enter a valid amount!"


def test_add_expense_rejects_non_positive_amount(new_user_client):
    resp = new_user_client.post(
        "/api/expenses",
        json={"amount": "0", "category": "Food", "date": "2026-07-01", "description": None},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Amount must be greater than zero!"


def test_expense_crud_and_ownership(new_user_client):
    create_resp = new_user_client.post(
        "/api/expenses",
        json={"amount": "99.50", "category": "Food", "date": "2026-07-01", "description": "Lunch"},
    )
    assert create_resp.status_code == 201
    expense = create_resp.json()
    expense_id = expense["id"]
    assert expense["amount"] == 99.50
    assert expense["category"] == "Food"

    get_resp = new_user_client.get(f"/api/expenses/{expense_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["description"] == "Lunch"

    edit_resp = new_user_client.put(
        f"/api/expenses/{expense_id}",
        json={"amount": "150.00", "category": "Shopping", "date": "2026-07-02", "description": "Lunch edited"},
    )
    assert edit_resp.status_code == 200
    assert edit_resp.json()["amount"] == 150.00
    assert edit_resp.json()["category"] == "Shopping"

    delete_resp = new_user_client.delete(f"/api/expenses/{expense_id}")
    assert delete_resp.status_code == 204

    after_delete = new_user_client.get(f"/api/expenses/{expense_id}")
    assert after_delete.status_code == 404


def test_expense_not_found_for_nonexistent_id(new_user_client):
    resp = new_user_client.get("/api/expenses/999999999")
    assert resp.status_code == 404


def test_cannot_access_another_users_expense(client, new_user_client):
    create_resp = new_user_client.post(
        "/api/expenses",
        json={"amount": "42", "category": "Food", "date": "2026-07-01", "description": "Owned by user A"},
    )
    expense_id = create_resp.json()["id"]
    new_user_client.post("/api/auth/logout")

    # Register+login as a second, different user and try to reach user A's expense.
    import uuid

    email = f"owner-check-{uuid.uuid4().hex[:10]}@test.com"
    client.post(
        "/api/auth/register",
        json={"full_name": "User B", "email": email, "password": "password123", "confirm_password": "password123"},
    )
    client.post("/api/auth/login", json={"email": email, "password": "password123"})

    resp = client.get(f"/api/expenses/{expense_id}")
    assert resp.status_code == 404

    resp = client.delete(f"/api/expenses/{expense_id}")
    assert resp.status_code == 404

    client.post("/api/auth/logout")
