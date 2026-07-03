from datetime import datetime


def test_dashboard_shape_for_fresh_user(new_user_client):
    resp = new_user_client.get("/api/dashboard")
    assert resp.status_code == 200
    body = resp.json()

    assert body["total_expenses"] == 0.0
    assert body["total_income"] == 0.0
    assert body["remaining_balance"] == 0.0
    assert body["transaction_count"] == 0
    assert body["categories"] == []
    assert body["recent_transactions"] == []
    assert body["has_transactions"] is False
    assert len(body["monthly_trend"]) == 6
    for point in body["monthly_trend"]:
        assert set(point.keys()) == {"year_month", "label", "total"}


def test_dashboard_reflects_added_expense_and_income(new_user_client):
    today = datetime.now().strftime("%Y-%m-%d")
    new_user_client.post(
        "/api/expenses", json={"amount": "100", "category": "Food", "date": today, "description": None}
    )
    new_user_client.post(
        "/api/income", json={"amount": "1000", "source": "Salary", "date": today, "description": None}
    )

    resp = new_user_client.get("/api/dashboard")
    body = resp.json()
    assert body["total_expenses"] == 100.0
    assert body["total_income"] == 1000.0
    assert body["remaining_balance"] == 900.0
    assert body["transaction_count"] == 1
    assert body["has_transactions"] is True
    assert body["categories"] == [{"category": "Food", "total": 100.0}]
