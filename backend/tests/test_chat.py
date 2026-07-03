from types import SimpleNamespace

from app.routers import chat as chat_module


class _FakeCompletions:
    def create(self, **kwargs):
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="You spent nothing this month."))]
        )


class _FakeOpenAIClient:
    def __init__(self, **kwargs):
        self.chat = SimpleNamespace(completions=_FakeCompletions())


def test_chat_requires_auth(client):
    client.post("/api/auth/logout")
    resp = client.post("/api/chat", json={"message": "hi", "history": []})
    assert resp.status_code == 401


def test_chat_rejects_empty_message(new_user_client, monkeypatch):
    monkeypatch.setattr(chat_module.settings, "groq_api_key", "fake-key")
    monkeypatch.setattr(chat_module, "OpenAI", _FakeOpenAIClient)
    resp = new_user_client.post("/api/chat", json={"message": "   ", "history": []})
    assert resp.status_code == 400


def test_chat_returns_reply(new_user_client, monkeypatch):
    monkeypatch.setattr(chat_module.settings, "groq_api_key", "fake-key")
    monkeypatch.setattr(chat_module, "OpenAI", _FakeOpenAIClient)
    resp = new_user_client.post("/api/chat", json={"message": "How much did I spend?", "history": []})
    assert resp.status_code == 200
    assert resp.json()["reply"] == "You spent nothing this month."


def test_chat_returns_500_without_api_key(new_user_client, monkeypatch):
    monkeypatch.setattr(chat_module.settings, "groq_api_key", None)
    resp = new_user_client.post("/api/chat", json={"message": "hello", "history": []})
    assert resp.status_code == 500
