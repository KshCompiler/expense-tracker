def test_add_income_requires_all_fields(new_user_client):
    resp = new_user_client.post("/api/income", json={"amount": "", "source": "", "date": "", "description": None})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Amount, source, and date are required!"


def test_add_income_rejects_invalid_source(new_user_client):
    resp = new_user_client.post(
        "/api/income",
        json={"amount": "100", "source": "Lottery", "date": "2026-07-01", "description": None},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Please select a valid income source!"


def test_add_income_success(new_user_client):
    resp = new_user_client.post(
        "/api/income",
        json={"amount": "500.00", "source": "Gift", "date": "2026-07-01", "description": "Birthday"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["amount"] == 500.0
    assert body["source"] == "Gift"
    assert body["description"] == "Birthday"
