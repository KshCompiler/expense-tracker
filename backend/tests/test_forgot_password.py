import uuid
from urllib.parse import parse_qs, urlparse

from app import crud
from app import security as security_module
from app.routers import auth as auth_module


def _unique_email():
    return f"forgot-{uuid.uuid4().hex[:10]}@test.com"


def _register(client, email, password="OldPass123!"):
    resp = client.post(
        "/api/auth/register",
        json={"full_name": "Test User", "email": email, "password": password, "confirm_password": password},
    )
    assert resp.status_code == 201, resp.text


def _extract_token(reset_link):
    return parse_qs(urlparse(reset_link).query)["token"][0]


def test_forgot_password_existing_email_sends_email(client, monkeypatch):
    email = _unique_email()
    _register(client, email)

    calls = []
    monkeypatch.setattr(auth_module, "send_password_reset_email", lambda to, link: calls.append((to, link)))

    resp = client.post("/api/auth/forgot-password", json={"email": email})
    assert resp.status_code == 200
    assert resp.json()["message"] == auth_module._forgot_password_message()

    assert len(calls) == 1
    to_email, reset_link = calls[0]
    assert to_email == email
    assert "/reset-password?token=" in reset_link


def test_forgot_password_nonexistent_email_same_response(client, monkeypatch):
    calls = []
    monkeypatch.setattr(auth_module, "send_password_reset_email", lambda to, link: calls.append((to, link)))

    resp = client.post("/api/auth/forgot-password", json={"email": _unique_email()})
    assert resp.status_code == 200
    assert resp.json()["message"] == auth_module._forgot_password_message()
    assert calls == []


def test_reset_password_valid_token_changes_password_and_old_password_fails(client, monkeypatch):
    email = _unique_email()
    _register(client, email, password="OldPass123!")

    calls = []
    monkeypatch.setattr(auth_module, "send_password_reset_email", lambda to, link: calls.append((to, link)))
    client.post("/api/auth/forgot-password", json={"email": email})
    token = _extract_token(calls[0][1])

    resp = client.post(
        "/api/auth/reset-password",
        json={"token": token, "password": "NewPass456!", "confirm_password": "NewPass456!"},
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "Your password has been reset. You can now sign in."

    resp = client.post("/api/auth/login", json={"email": email, "password": "NewPass456!"})
    assert resp.status_code == 200

    resp = client.post("/api/auth/login", json={"email": email, "password": "OldPass123!"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid email or password!"


def test_reset_password_replayed_token_rejected(client, monkeypatch):
    email = _unique_email()
    _register(client, email, password="OldPass123!")

    calls = []
    monkeypatch.setattr(auth_module, "send_password_reset_email", lambda to, link: calls.append((to, link)))
    client.post("/api/auth/forgot-password", json={"email": email})
    token = _extract_token(calls[0][1])

    resp = client.post(
        "/api/auth/reset-password",
        json={"token": token, "password": "NewPass456!", "confirm_password": "NewPass456!"},
    )
    assert resp.status_code == 200

    resp = client.post(
        "/api/auth/reset-password",
        json={"token": token, "password": "AnotherPass789!", "confirm_password": "AnotherPass789!"},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == auth_module.RESET_TOKEN_INVALID_MESSAGE


def test_reset_password_garbage_token_rejected(client):
    resp = client.post(
        "/api/auth/reset-password",
        json={"token": "not-a-real-jwt", "password": "NewPass456!", "confirm_password": "NewPass456!"},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == auth_module.RESET_TOKEN_INVALID_MESSAGE


def test_reset_password_expired_token_rejected(client, monkeypatch):
    email = _unique_email()
    _register(client, email, password="OldPass123!")

    from app.database import SessionLocal

    with SessionLocal() as db:
        user = crud.get_user_by_email(db, email)
        monkeypatch.setattr(security_module.settings, "password_reset_token_expire_minutes", -1)
        expired_token = security_module.create_password_reset_token(user.id, user.password_hash)

    resp = client.post(
        "/api/auth/reset-password",
        json={"token": expired_token, "password": "NewPass456!", "confirm_password": "NewPass456!"},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == auth_module.RESET_TOKEN_INVALID_MESSAGE
