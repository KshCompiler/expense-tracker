def test_transactions_empty_for_fresh_user(new_user_client):
    resp = new_user_client.get("/api/transactions")
    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []
    assert body["total"] == 0
    assert body["total_pages"] == 1
    assert body["invalid_range"] is False


def test_transactions_search_and_date_filter(new_user_client):
    new_user_client.post(
        "/api/expenses",
        json={"amount": "10", "category": "Food", "date": "2026-01-05", "description": "coffee run"},
    )
    new_user_client.post(
        "/api/expenses",
        json={"amount": "20", "category": "Transport", "date": "2026-02-10", "description": "bus pass"},
    )

    resp = new_user_client.get("/api/transactions", params={"q": "coffee"})
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["description"] == "coffee run"

    resp = new_user_client.get(
        "/api/transactions", params={"from_date": "2026-02-01", "to_date": "2026-02-28"}
    )
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["description"] == "bus pass"


def test_transactions_invalid_range_returns_explicit_empty_state(new_user_client):
    """The original Flask route left `transactions=None` here, wiping the whole
    results section. The FastAPI port instead returns an explicit empty page
    with invalid_range=True so the frontend can show a proper message."""
    resp = new_user_client.get(
        "/api/transactions", params={"from_date": "2026-07-20", "to_date": "2026-07-01"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []
    assert body["total"] == 0
    assert body["invalid_range"] is True


def test_transactions_pagination(new_user_client):
    for i in range(25):
        new_user_client.post(
            "/api/expenses",
            json={"amount": "5", "category": "Other", "date": "2026-03-01", "description": f"item {i}"},
        )

    page1 = new_user_client.get("/api/transactions", params={"page": 1}).json()
    assert page1["total"] == 25
    assert page1["total_pages"] == 2
    assert len(page1["items"]) == 20

    page2 = new_user_client.get("/api/transactions", params={"page": 2}).json()
    assert len(page2["items"]) == 5

    # page clamps to the last page instead of erroring for an out-of-range request
    page_out_of_range = new_user_client.get("/api/transactions", params={"page": 99}).json()
    assert page_out_of_range["page"] == 2
