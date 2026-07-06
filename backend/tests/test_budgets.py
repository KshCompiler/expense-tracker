import uuid
from datetime import datetime
from types import SimpleNamespace

from app.routers import budgets as budgets_module

TODAY = datetime.now().strftime("%Y-%m-%d")


def _month_date(months_ago: int, day: int = 15) -> str:
    now = datetime.now()
    total = (now.year * 12 + (now.month - 1)) - months_ago
    year, month = divmod(total, 12)
    month += 1
    return f"{year:04d}-{month:02d}-{day:02d}"


class _FakeCompletions:
    def __init__(self, content: str):
        self._content = content

    def create(self, **kwargs):
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=self._content))])


class _FakeOpenAIClient:
    def __init__(self, content: str = "LIMIT: 4000\nRATIONALE: Based on recent spending."):
        self.chat = SimpleNamespace(completions=_FakeCompletions(content))


def _add_expense(client, amount: str, category: str = "Food", date: str = TODAY):
    resp = client.post(
        "/api/expenses", json={"amount": amount, "category": category, "date": date, "description": None}
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_create_and_list_budget(new_user_client):
    create_resp = new_user_client.post("/api/budgets", json={"category": "Food", "monthly_limit": "5000"})
    assert create_resp.status_code == 201, create_resp.text
    body = create_resp.json()
    assert body["category"] == "Food"
    assert body["monthly_limit"] == 5000.0

    list_resp = new_user_client.get("/api/budgets")
    assert list_resp.status_code == 200
    statuses = list_resp.json()
    assert len(statuses) == 1
    assert statuses[0]["category"] == "Food"
    assert statuses[0]["spent"] == 0.0
    assert statuses[0]["percent_used"] == 0.0
    assert statuses[0]["status"] == "ok"
    assert statuses[0]["remaining"] == 5000.0


def test_create_budget_rejects_invalid_category(new_user_client):
    resp = new_user_client.post("/api/budgets", json={"category": "Education", "monthly_limit": "1000"})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Please select a valid category!"


def test_create_budget_rejects_non_positive_limit(new_user_client):
    resp = new_user_client.post("/api/budgets", json={"category": "Food", "monthly_limit": "0"})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Amount must be greater than zero!"


def test_create_duplicate_category_rejected(new_user_client):
    resp = new_user_client.post("/api/budgets", json={"category": "Bills", "monthly_limit": "1000"})
    assert resp.status_code == 201

    dup_resp = new_user_client.post("/api/budgets", json={"category": "Bills", "monthly_limit": "2000"})
    assert dup_resp.status_code == 400
    assert dup_resp.json()["detail"] == "You already have a budget for this category — edit it instead."


def test_update_and_delete_budget(new_user_client):
    create_resp = new_user_client.post("/api/budgets", json={"category": "Health", "monthly_limit": "1000"})
    budget_id = create_resp.json()["id"]

    edit_resp = new_user_client.put(f"/api/budgets/{budget_id}", json={"monthly_limit": "1500"})
    assert edit_resp.status_code == 200
    assert edit_resp.json()["monthly_limit"] == 1500.0

    delete_resp = new_user_client.delete(f"/api/budgets/{budget_id}")
    assert delete_resp.status_code == 204

    list_resp = new_user_client.get("/api/budgets")
    assert all(b["id"] != budget_id for b in list_resp.json())


def test_budget_not_found_for_nonexistent_id(new_user_client):
    resp = new_user_client.put("/api/budgets/999999999", json={"monthly_limit": "1000"})
    assert resp.status_code == 404

    resp = new_user_client.delete("/api/budgets/999999999")
    assert resp.status_code == 404


def test_cannot_access_another_users_budget(client, new_user_client):
    create_resp = new_user_client.post("/api/budgets", json={"category": "Shopping", "monthly_limit": "1000"})
    budget_id = create_resp.json()["id"]
    new_user_client.post("/api/auth/logout")

    email = f"owner-check-{uuid.uuid4().hex[:10]}@test.com"
    client.post(
        "/api/auth/register",
        json={"full_name": "User B", "email": email, "password": "Password123!", "confirm_password": "Password123!"},
    )
    client.post("/api/auth/login", json={"email": email, "password": "Password123!"})

    resp = client.put(f"/api/budgets/{budget_id}", json={"monthly_limit": "500"})
    assert resp.status_code == 404

    resp = client.delete(f"/api/budgets/{budget_id}")
    assert resp.status_code == 404

    client.post("/api/auth/logout")


def test_budget_status_thresholds(new_user_client):
    new_user_client.post("/api/budgets", json={"category": "Entertainment", "monthly_limit": "1000"})

    def status_for_entertainment():
        statuses = new_user_client.get("/api/budgets").json()
        return next(b for b in statuses if b["category"] == "Entertainment")

    assert status_for_entertainment()["status"] == "ok"

    _add_expense(new_user_client, "800", category="Entertainment")
    assert status_for_entertainment()["status"] == "warning"

    _add_expense(new_user_client, "300", category="Entertainment")
    over = status_for_entertainment()
    assert over["status"] == "over"
    assert over["spent"] == 1100.0
    assert over["remaining"] == -100.0


def test_overall_budget_sums_all_categories_independent_of_per_category(new_user_client):
    new_user_client.post("/api/budgets", json={"category": "Overall", "monthly_limit": "10000"})
    new_user_client.post("/api/budgets", json={"category": "Food", "monthly_limit": "1000"})

    _add_expense(new_user_client, "400", category="Food")
    _add_expense(new_user_client, "600", category="Transport")

    statuses = new_user_client.get("/api/budgets").json()
    overall = next(b for b in statuses if b["category"] == "Overall")
    food = next(b for b in statuses if b["category"] == "Food")

    assert overall["spent"] == 1000.0
    assert food["spent"] == 400.0


def test_suggest_budget_limit_with_history(new_user_client, monkeypatch):
    monkeypatch.setattr(budgets_module.settings, "groq_api_key", "fake-key")
    monkeypatch.setattr(budgets_module, "OpenAI", lambda **kwargs: _FakeOpenAIClient())

    _add_expense(new_user_client, "2000", category="Shopping")

    resp = new_user_client.get("/api/budgets/suggest/Shopping")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    # History is [0, 0, 2000] (oldest to newest); recency-weighted average with
    # weights [1, 2, 3] is (0*1 + 0*2 + 2000*3) / 6 = 1000, so the model's raw
    # 4000 must be clamped to 2x that weighted anchor, i.e. 2000.
    weighted_avg = 1000.0
    assert body["suggested_limit"] == round(weighted_avg * 2.0, 2)
    assert body["rationale"] == "Based on recent spending."


def test_suggest_budget_limit_shortens_long_rationale(new_user_client, monkeypatch):
    long_rationale = (
        "This is a much longer rationale than the interface should ever show a user because it "
        "rambles on well past what a one-line helper caption ought to contain."
    )
    monkeypatch.setattr(budgets_module.settings, "groq_api_key", "fake-key")
    monkeypatch.setattr(
        budgets_module, "OpenAI", lambda **kwargs: _FakeOpenAIClient(f"LIMIT: 4000\nRATIONALE: {long_rationale}")
    )

    _add_expense(new_user_client, "2000", category="Health")

    resp = new_user_client.get("/api/budgets/suggest/Health")
    assert resp.status_code == 200, resp.text
    rationale = resp.json()["rationale"]
    assert len(rationale) <= budgets_module.MAX_RATIONALE_LENGTH + 1  # +1 for the trailing "…"
    assert rationale.endswith("…")


def test_suggest_budget_limit_excludes_outlier_month(new_user_client, monkeypatch):
    monkeypatch.setattr(budgets_module.settings, "groq_api_key", "fake-key")
    monkeypatch.setattr(
        budgets_module,
        "OpenAI",
        lambda **kwargs: _FakeOpenAIClient("LIMIT: 3000\nRATIONALE: Trend looks steady."),
    )

    # Two ordinary months, then a wedding-sized spike this month.
    _add_expense(new_user_client, "500", category="Entertainment", date=_month_date(2))
    _add_expense(new_user_client, "520", category="Entertainment", date=_month_date(1))
    _add_expense(new_user_client, "5000", category="Entertainment", date=_month_date(0))

    resp = new_user_client.get("/api/budgets/suggest/Entertainment")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    # The ₹5000 month is a spike relative to the other two (median ₹510, ratio > 1.8x),
    # so it's excluded from the anchor entirely: weighted avg of just [500, 520] with
    # weights [1, 2] is (500*1 + 520*2) / 3 ≈ 513.33, not the ~2757 a naive weighted
    # average across all three months (including the spike) would produce.
    weighted_avg = (500 * 1 + 520 * 2) / 3
    assert body["suggested_limit"] == round(weighted_avg * 2.0, 2)


def test_suggest_budget_limit_no_history(new_user_client):
    resp = new_user_client.get("/api/budgets/suggest/Health")
    assert resp.status_code == 400
    assert "Not enough spending history" in resp.json()["detail"]


def test_suggest_budget_limit_without_groq_key(new_user_client, monkeypatch):
    monkeypatch.setattr(budgets_module.settings, "groq_api_key", None)
    _add_expense(new_user_client, "500", category="Bills")

    resp = new_user_client.get("/api/budgets/suggest/Bills")
    assert resp.status_code == 500
