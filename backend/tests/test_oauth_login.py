import uuid

from app.routers import auth as auth_module


def _unique_email():
    return f"oauth-{uuid.uuid4().hex[:10]}@test.com"


def _userinfo(sub: str, email: str, *, verified: bool = True, name: str = "OAuth User"):
    return {"sub": sub, "email": email, "email_verified": verified, "name": name}


def _configure_google(monkeypatch):
    monkeypatch.setattr(auth_module.settings, "google_client_id", "fake-google-client-id")
    monkeypatch.setattr(auth_module.settings, "google_client_secret", "fake-google-client-secret")


def _configure_linkedin(monkeypatch):
    monkeypatch.setattr(auth_module.settings, "linkedin_client_id", "fake-linkedin-client-id")
    monkeypatch.setattr(auth_module.settings, "linkedin_client_secret", "fake-linkedin-client-secret")


def test_oauth_login_unknown_provider_returns_404(client):
    resp = client.get("/api/auth/facebook/login", follow_redirects=False)
    assert resp.status_code == 404


def test_oauth_callback_unknown_provider_returns_404(client):
    resp = client.get("/api/auth/facebook/callback?code=x&state=y", follow_redirects=False)
    assert resp.status_code == 404


def test_oauth_login_unconfigured_provider_redirects_with_error(client, monkeypatch):
    monkeypatch.setattr(auth_module.settings, "google_client_id", None)
    monkeypatch.setattr(auth_module.settings, "google_client_secret", None)

    resp = client.get("/api/auth/google/login", follow_redirects=False)

    assert resp.status_code == 302
    assert resp.headers["location"].startswith(f"{auth_module.settings.frontend_base_url}/login?oauth_error=")
    assert "oauth_state" not in resp.cookies


def test_oauth_login_configured_provider_redirects_to_provider_and_sets_state_cookie(client, monkeypatch):
    _configure_google(monkeypatch)

    resp = client.get("/api/auth/google/login", follow_redirects=False)

    assert resp.status_code == 302
    assert resp.headers["location"].startswith("https://accounts.google.com/o/oauth2/v2/auth?")
    assert resp.cookies.get("oauth_state")


def test_oauth_callback_state_mismatch_redirects_with_error(client):
    client.cookies.set("oauth_state", "cookie-value")

    resp = client.get("/api/auth/google/callback?code=abc&state=mismatched", follow_redirects=False)

    assert resp.status_code == 302
    assert "/login?oauth_error=" in resp.headers["location"]
    client.cookies.delete("oauth_state")


def test_oauth_callback_missing_state_cookie_redirects_with_error(client):
    client.cookies.delete("oauth_state")

    resp = client.get("/api/auth/google/callback?code=abc&state=whatever", follow_redirects=False)

    assert resp.status_code == 302
    assert "/login?oauth_error=" in resp.headers["location"]


def test_oauth_callback_creates_new_user_and_logs_in(client, monkeypatch):
    email = _unique_email()
    client.cookies.set("oauth_state", "s1")
    monkeypatch.setattr(auth_module.oauth, "exchange_code_for_token", lambda provider, code: "fake-token")
    monkeypatch.setattr(auth_module.oauth, "fetch_userinfo", lambda provider, token: _userinfo("google-new-user", email))

    resp = client.get("/api/auth/google/callback?code=abc&state=s1", follow_redirects=False)

    assert resp.status_code == 302
    assert resp.headers["location"] == auth_module.settings.frontend_base_url
    assert resp.cookies.get("access_token")

    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == email

    client.post("/api/auth/logout")


def test_oauth_callback_links_existing_verified_email_account_same_history(client, monkeypatch):
    email = _unique_email()
    register = client.post(
        "/api/auth/register",
        json={"full_name": "Local User", "email": email, "password": "Password123!", "confirm_password": "Password123!"},
    )
    assert register.status_code == 201
    original_user_id = register.json()["id"]

    login = client.post("/api/auth/login", json={"email": email, "password": "Password123!"})
    assert login.status_code == 200

    expense = client.post(
        "/api/expenses",
        json={"amount": "42.5", "category": "Food", "date": "2026-07-01", "description": "Pre-link lunch"},
    )
    assert expense.status_code == 201

    client.post("/api/auth/logout")

    client.cookies.set("oauth_state", "s2")
    monkeypatch.setattr(auth_module.oauth, "exchange_code_for_token", lambda provider, code: "fake-token")
    monkeypatch.setattr(auth_module.oauth, "fetch_userinfo", lambda provider, token: _userinfo("google-linked", email))

    resp = client.get("/api/auth/google/callback?code=abc&state=s2", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.cookies.get("access_token")

    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["id"] == original_user_id
    assert me.json()["email"] == email

    expenses = client.get("/api/expenses/" + str(expense.json()["id"]))
    assert expenses.status_code == 200
    assert expenses.json()["description"] == "Pre-link lunch"

    client.post("/api/auth/logout")


def test_oauth_callback_rejects_unverified_email_no_existing_link(client, monkeypatch):
    email = _unique_email()
    client.cookies.set("oauth_state", "s3")
    monkeypatch.setattr(auth_module.oauth, "exchange_code_for_token", lambda provider, code: "fake-token")
    monkeypatch.setattr(
        auth_module.oauth, "fetch_userinfo", lambda provider, token: _userinfo("google-unverified", email, verified=False)
    )

    resp = client.get("/api/auth/google/callback?code=abc&state=s3", follow_redirects=False)

    assert resp.status_code == 302
    assert "/login?oauth_error=" in resp.headers["location"]
    assert "access_token" not in resp.cookies


def test_oauth_callback_links_second_provider_to_already_linked_user(client, monkeypatch):
    email = _unique_email()

    client.cookies.set("oauth_state", "s4")
    monkeypatch.setattr(auth_module.oauth, "exchange_code_for_token", lambda provider, code: "fake-token")
    monkeypatch.setattr(auth_module.oauth, "fetch_userinfo", lambda provider, token: _userinfo("google-multi", email))
    first = client.get("/api/auth/google/callback?code=abc&state=s4", follow_redirects=False)
    assert first.status_code == 302
    first_user_id = client.get("/api/auth/me").json()["id"]
    client.post("/api/auth/logout")

    client.cookies.set("oauth_state", "s5")
    monkeypatch.setattr(auth_module.oauth, "fetch_userinfo", lambda provider, token: _userinfo("linkedin-multi", email))
    second = client.get("/api/auth/linkedin/callback?code=abc&state=s5", follow_redirects=False)
    assert second.status_code == 302
    second_user_id = client.get("/api/auth/me").json()["id"]

    assert second_user_id == first_user_id
    client.post("/api/auth/logout")


def test_oauth_callback_existing_link_succeeds_even_if_unverified_on_later_login(client, monkeypatch):
    email = _unique_email()

    client.cookies.set("oauth_state", "s6")
    monkeypatch.setattr(auth_module.oauth, "exchange_code_for_token", lambda provider, code: "fake-token")
    monkeypatch.setattr(auth_module.oauth, "fetch_userinfo", lambda provider, token: _userinfo("google-repeat", email))
    first = client.get("/api/auth/google/callback?code=abc&state=s6", follow_redirects=False)
    assert first.status_code == 302
    first_user_id = client.get("/api/auth/me").json()["id"]
    client.post("/api/auth/logout")

    client.cookies.set("oauth_state", "s7")
    monkeypatch.setattr(
        auth_module.oauth, "fetch_userinfo", lambda provider, token: _userinfo("google-repeat", email, verified=False)
    )
    second = client.get("/api/auth/google/callback?code=abc&state=s7", follow_redirects=False)

    assert second.status_code == 302
    assert second.cookies.get("access_token")
    assert client.get("/api/auth/me").json()["id"] == first_user_id
    client.post("/api/auth/logout")


def test_password_login_on_oauth_only_account_returns_generic_401_not_500(client, monkeypatch):
    email = _unique_email()
    client.cookies.set("oauth_state", "s8")
    monkeypatch.setattr(auth_module.oauth, "exchange_code_for_token", lambda provider, code: "fake-token")
    monkeypatch.setattr(auth_module.oauth, "fetch_userinfo", lambda provider, token: _userinfo("google-passwordless", email))
    callback = client.get("/api/auth/google/callback?code=abc&state=s8", follow_redirects=False)
    assert callback.status_code == 302
    client.post("/api/auth/logout")

    resp = client.post("/api/auth/login", json={"email": email, "password": "anything123!"})

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid email or password!"


def test_oauth_callback_provider_http_failure_redirects_with_generic_error(client, monkeypatch):
    client.cookies.set("oauth_state", "s9")

    def _boom(provider, code):
        raise auth_module.oauth.OAuthError("boom")

    monkeypatch.setattr(auth_module.oauth, "exchange_code_for_token", _boom)

    resp = client.get("/api/auth/google/callback?code=abc&state=s9", follow_redirects=False)

    assert resp.status_code == 302
    assert "/login?oauth_error=" in resp.headers["location"]
    assert "boom" not in resp.headers["location"]
    assert "access_token" not in resp.cookies
