import uuid


def _unique_email():
    return f"auth-{uuid.uuid4().hex[:10]}@test.com"


def test_register_requires_all_fields(client):
    resp = client.post(
        "/api/auth/register",
        json={"full_name": "", "email": "", "password": "", "confirm_password": ""},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "All fields are required!"


def test_register_passwords_must_match(client):
    resp = client.post(
        "/api/auth/register",
        json={
            "full_name": "Test",
            "email": _unique_email(),
            "password": "password123",
            "confirm_password": "different123",
        },
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Passwords do not match!"


def test_register_rejects_bad_email(client):
    resp = client.post(
        "/api/auth/register",
        json={
            "full_name": "Test",
            "email": "not-an-email",
            "password": "password123",
            "confirm_password": "password123",
        },
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Please enter a valid email address!"


def test_register_rejects_short_password(client):
    resp = client.post(
        "/api/auth/register",
        json={
            "full_name": "Test",
            "email": _unique_email(),
            "password": "short1",
            "confirm_password": "short1",
        },
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Password must be at least 8 characters long!"


def test_register_rejects_duplicate_email(client):
    email = _unique_email()
    payload = {
        "full_name": "Test",
        "email": email,
        "password": "password123",
        "confirm_password": "password123",
    }
    first = client.post("/api/auth/register", json=payload)
    assert first.status_code == 201

    second = client.post("/api/auth/register", json=payload)
    assert second.status_code == 400
    assert second.json()["detail"] == "An account with this email already exists!"


def test_login_invalid_credentials(client):
    resp = client.post("/api/auth/login", json={"email": "nobody@test.com", "password": "wrongpass"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid email or password!"


def test_register_then_login_flow(client):
    email = _unique_email()
    client.post(
        "/api/auth/register",
        json={
            "full_name": "Flow User",
            "email": email,
            "password": "password123",
            "confirm_password": "password123",
        },
    )
    login_resp = client.post("/api/auth/login", json={"email": email, "password": "password123"})
    assert login_resp.status_code == 200
    assert login_resp.json()["email"] == email

    me_resp = client.get("/api/auth/me")
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == email

    logout_resp = client.post("/api/auth/logout")
    assert logout_resp.status_code == 204

    me_after_logout = client.get("/api/auth/me")
    assert me_after_logout.status_code == 401


def test_protected_route_requires_auth(client):
    client.post("/api/auth/logout")
    resp = client.get("/api/dashboard")
    assert resp.status_code == 401
