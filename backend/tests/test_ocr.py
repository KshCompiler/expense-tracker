from types import SimpleNamespace

from app.routers import ocr as ocr_module

FAKE_JPEG_BYTES = b"\xff\xd8\xff" + b"0" * 32


class _FakeCompletions:
    def __init__(self, content):
        self._content = content

    def create(self, **kwargs):
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=self._content))])


class _FakeOpenAIClient:
    def __init__(self, content):
        self.chat = SimpleNamespace(completions=_FakeCompletions(content))


def _use_fake_llm(monkeypatch, content):
    monkeypatch.setattr(ocr_module.settings, "groq_api_key", "fake-key-for-tests")
    monkeypatch.setattr(ocr_module, "OpenAI", lambda **kwargs: _FakeOpenAIClient(content))


def test_extract_bill_requires_a_file(new_user_client):
    resp = new_user_client.post("/api/expenses/extract-bill")
    assert resp.status_code == 400
    assert resp.json()["detail"] == "No image was uploaded."


def test_extract_bill_rejects_non_image_bytes(new_user_client, monkeypatch):
    _use_fake_llm(monkeypatch, '{"amount": 1, "category": "Food", "date": null, "description": null}')
    resp = new_user_client.post(
        "/api/expenses/extract-bill",
        files={"bill_image": ("not-an-image.txt", b"just some plain text", "image/jpeg")},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Please upload a JPG, PNG, or WEBP image."


def test_extract_bill_returns_503_without_api_key(new_user_client, monkeypatch):
    monkeypatch.setattr(ocr_module.settings, "groq_api_key", None)
    resp = new_user_client.post(
        "/api/expenses/extract-bill",
        files={"bill_image": ("bill.jpg", FAKE_JPEG_BYTES, "image/jpeg")},
    )
    assert resp.status_code == 503


def test_extract_bill_revalidates_model_output_server_side(new_user_client, monkeypatch):
    """The model is never trusted as final: an invalid category from the LLM
    must come back as null even though the LLM "said" a value."""
    _use_fake_llm(
        monkeypatch,
        '{"amount": 250.5, "category": "NotARealCategory", "date": "2026-07-01", "description": "Test merchant"}',
    )
    resp = new_user_client.post(
        "/api/expenses/extract-bill",
        files={"bill_image": ("bill.jpg", FAKE_JPEG_BYTES, "image/jpeg")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["amount"] == 250.5
    assert body["date"] == "2026-07-01"
    assert body["description"] == "Test merchant"
    assert body["category"] is None  # invalid value from the model gets nulled out


def test_extract_bill_accepts_valid_category(new_user_client, monkeypatch):
    _use_fake_llm(
        monkeypatch,
        '{"amount": 42, "category": "Food", "date": "2026-07-01", "description": "Cafe"}',
    )
    resp = new_user_client.post(
        "/api/expenses/extract-bill",
        files={"bill_image": ("bill.jpg", FAKE_JPEG_BYTES, "image/jpeg")},
    )
    assert resp.status_code == 200
    assert resp.json()["category"] == "Food"


def test_extract_bill_nulls_non_positive_amount(new_user_client, monkeypatch):
    _use_fake_llm(
        monkeypatch,
        '{"amount": -5, "category": "Food", "date": "2026-07-01", "description": null}',
    )
    resp = new_user_client.post(
        "/api/expenses/extract-bill",
        files={"bill_image": ("bill.jpg", FAKE_JPEG_BYTES, "image/jpeg")},
    )
    assert resp.status_code == 200
    assert resp.json()["amount"] is None


def test_extract_bill_handles_malformed_llm_json(new_user_client, monkeypatch):
    _use_fake_llm(monkeypatch, "this is not json at all")
    resp = new_user_client.post(
        "/api/expenses/extract-bill",
        files={"bill_image": ("bill.jpg", FAKE_JPEG_BYTES, "image/jpeg")},
    )
    assert resp.status_code == 500


def test_extract_bill_strips_markdown_fences(new_user_client, monkeypatch):
    _use_fake_llm(
        monkeypatch,
        '```json\n{"amount": 10, "category": "Food", "date": "2026-07-01", "description": null}\n```',
    )
    resp = new_user_client.post(
        "/api/expenses/extract-bill",
        files={"bill_image": ("bill.jpg", FAKE_JPEG_BYTES, "image/jpeg")},
    )
    assert resp.status_code == 200
    assert resp.json()["amount"] == 10.0


def test_income_extract_bill_uses_source_field(new_user_client, monkeypatch):
    _use_fake_llm(
        monkeypatch,
        '{"amount": 50000, "source": "Salary", "date": "2026-07-01", "description": "Payslip"}',
    )
    resp = new_user_client.post(
        "/api/income/extract-bill",
        files={"bill_image": ("payslip.jpg", FAKE_JPEG_BYTES, "image/jpeg")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["source"] == "Salary"
    assert "category" not in body or body.get("category") is None
