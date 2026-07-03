def test_profile_requires_auth(client):
    client.post("/api/auth/logout")
    resp = client.get("/api/profile")
    assert resp.status_code == 401


def test_profile_shape_and_lifetime_stats(new_user_client):
    new_user_client.post(
        "/api/expenses", json={"amount": "100", "category": "Food", "date": "2026-01-01", "description": None}
    )
    new_user_client.post(
        "/api/income", json={"amount": "5000", "source": "Salary", "date": "2026-01-01", "description": None}
    )

    resp = new_user_client.get("/api/profile")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_expenses_all_time"] == 100.0
    assert body["total_income_all_time"] == 5000.0
    assert body["transaction_count_all_time"] == 1
    assert "email" in body and "full_name" in body and "created_at" in body
