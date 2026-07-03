import os
import sys
import tempfile
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Point the app at a throwaway SQLite file for the whole test session so tests
# never touch the real expense_tracker.db. Must happen before `app.main` (and
# therefore `app.config.settings`) is imported.
_tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp_db.close()
os.environ["DATABASE_PATH"] = _tmp_db.name
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-prod")
os.environ.setdefault("GROQ_API_KEY", "")

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def new_user_client(client):
    """A logged-in client for a freshly registered user with zero transactions.

    Each test gets its own user (unique email) so tests never see each
    other's data, even though the underlying TestClient/DB is shared."""
    email = f"user-{uuid.uuid4().hex[:10]}@test.com"
    resp = client.post(
        "/api/auth/register",
        json={
            "full_name": "Test User",
            "email": email,
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    assert resp.status_code == 201, resp.text

    resp = client.post("/api/auth/login", json={"email": email, "password": "Password123!"})
    assert resp.status_code == 200, resp.text

    yield client
    client.post("/api/auth/logout")
