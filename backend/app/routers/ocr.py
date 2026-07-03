import base64
import json
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from openai import OpenAI

from app.config import settings
from app.constants import ALLOWED_BILL_MIME_TYPES, MAX_BILL_IMAGE_BYTES, VALID_CATEGORIES, VALID_INCOME_SOURCES
from app.deps import get_current_user
from app.models import User
from app.schemas import BillExtractionOut

router = APIRouter(prefix="/api", tags=["ocr"])
logger = logging.getLogger(__name__)


def _sniff_image_mimetype(data: bytes) -> str | None:
    """Identify the image format from its actual bytes rather than trusting the
    client-supplied Content-Type, which is trivially spoofable."""
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def _build_bill_extraction_prompt(valid_values: set[str], field_name: str, doc_kind: str) -> str:
    values_list = ", ".join(sorted(valid_values))
    return (
        f"You are reading a photo of a {doc_kind} for a personal finance app. "
        "Extract exactly these fields and reply with STRICT JSON only — no markdown code "
        "fences, no commentary, nothing before or after the JSON object:\n"
        '{"amount": <number or null>, "' + field_name + '": <one of [' + values_list + "] or null>, "
        '"date": <"YYYY-MM-DD" or null>, "description": <short string under 60 characters or null>}\n\n'
        "Rules:\n"
        "- amount is the total amount on the document, as a plain number with no currency symbol or commas.\n"
        f"- {field_name} must be exactly one of the listed values, or null if you're not confident.\n"
        "- date is the date on the document in YYYY-MM-DD format, or null if illegible or absent.\n"
        "- description briefly names the merchant/payer or what the document is for, or null if unclear.\n"
        "- If you cannot confidently read a field, return null for it — never guess.\n"
        f"- If the image is not a {doc_kind} at all, return null for every field."
    )


async def _extract_financial_document(
    file: UploadFile | None, field_name: str, valid_values: set[str], doc_kind: str
) -> BillExtractionOut:
    if not file or not file.filename:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="No image was uploaded.")

    image_bytes = await file.read(MAX_BILL_IMAGE_BYTES + 1)
    if not image_bytes:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="That image appears to be empty.")
    if len(image_bytes) > MAX_BILL_IMAGE_BYTES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="That image is too large — please use a photo under 5MB.")

    mimetype = _sniff_image_mimetype(image_bytes)
    if mimetype not in ALLOWED_BILL_MIME_TYPES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Please upload a JPG, PNG, or WEBP image.")

    api_key = settings.groq_api_key
    if not api_key:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Document scanning isn't available right now — please enter the details manually.",
        )

    try:
        b64_image = base64.b64encode(image_bytes).decode("utf-8")
        data_url = f"data:{mimetype};base64,{b64_image}"

        client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
        response = client.chat.completions.create(
            model=settings.bill_ocr_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": _build_bill_extraction_prompt(valid_values, field_name, doc_kind)},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ],
            temperature=0,
        )
        raw = response.choices[0].message.content.strip()
        raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            raise ValueError("model response was not a JSON object")
    except Exception as e:
        logger.error("Document extraction error: %s", e, exc_info=True)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Couldn't read that image — please enter the details manually.")

    # Never trust the model's output as final — re-validate every field server-side.
    amount = parsed.get("amount")
    try:
        amount = float(amount) if amount is not None else None
        if amount is not None and amount <= 0:
            amount = None
    except (TypeError, ValueError):
        amount = None

    field_value = parsed.get(field_name)
    if field_value not in valid_values:
        field_value = None

    date = parsed.get("date")
    if date:
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except (TypeError, ValueError):
            date = None
    else:
        date = None

    description = parsed.get("description")
    if isinstance(description, str):
        description = description.strip()[:120] or None
    else:
        description = None

    return BillExtractionOut(amount=amount, date=date, description=description, **{field_name: field_value})


@router.post("/expenses/extract-bill", response_model=BillExtractionOut)
async def extract_bill(
    bill_image: UploadFile | None = File(None),
    current_user: User = Depends(get_current_user),
):
    return await _extract_financial_document(bill_image, "category", VALID_CATEGORIES, "shopping bill or receipt")


@router.post("/income/extract-bill", response_model=BillExtractionOut)
async def extract_income_bill(
    bill_image: UploadFile | None = File(None),
    current_user: User = Depends(get_current_user),
):
    return await _extract_financial_document(
        bill_image, "source", VALID_INCOME_SOURCES, "payslip, invoice, or proof of income"
    )
