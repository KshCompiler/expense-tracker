import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from openai import OpenAI
from sqlalchemy.orm import Session

from app import crud
from app.config import settings
from app.deps import get_current_user, get_db
from app.models import User
from app.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/api", tags=["chat"])
logger = logging.getLogger(__name__)


def _fmt_expenses(rows: list[tuple[str, float]]) -> str:
    if not rows:
        return "No expenses recorded"
    return ", ".join(f"{category}: ₹{total:.0f}" for category, total in rows)


def _build_chat_system_prompt(curr_month, curr_expenses, curr_income, prev_month, prev_expenses, prev_income) -> str:
    curr_label = datetime.strptime(curr_month, "%Y-%m").strftime("%B %Y")
    prev_label = datetime.strptime(prev_month, "%Y-%m").strftime("%B %Y")

    return (
        "You are a helpful personal finance assistant built into Spendly, an expense tracker app. "
        "You have access to the user's real spending data shown below. Answer their questions "
        "conversationally and concisely — 2 to 4 sentences max. Reference the actual numbers "
        "when relevant. Use ₹ for currency. Never make up data not shown here.\n\n"
        "User's Financial Data:\n"
        f"- {prev_label}: Income ₹{prev_income:.0f} | Expenses: {_fmt_expenses(prev_expenses)}\n"
        f"- {curr_label}: Income ₹{curr_income:.0f} | Expenses: {_fmt_expenses(curr_expenses)}"
    )


@router.post("/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_message = payload.message.strip()
    if not user_message:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Empty message")

    try:
        now = datetime.now()
        curr_month = now.strftime("%Y-%m")
        prev_month = f"{now.year - 1}-12" if now.month == 1 else f"{now.year}-{now.month - 1:02d}"

        curr_expenses = crud.get_monthly_expense_summary(db, current_user.id, curr_month)
        curr_income = crud.get_monthly_income_total(db, current_user.id, curr_month)
        prev_expenses = crud.get_monthly_expense_summary(db, current_user.id, prev_month)
        prev_income = crud.get_monthly_income_total(db, current_user.id, prev_month)

        api_key = settings.groq_api_key
        if not api_key:
            raise ValueError("GROQ_API_KEY not set")

        system_prompt = _build_chat_system_prompt(
            curr_month, curr_expenses, curr_income, prev_month, prev_expenses, prev_income
        )

        messages = [{"role": "system", "content": system_prompt}]
        for turn in payload.history[-10:]:
            if turn.role in ("user", "assistant") and turn.content:
                messages.append({"role": turn.role, "content": turn.content})
        messages.append({"role": "user", "content": user_message})

        client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
        response = client.chat.completions.create(model="llama-3.1-8b-instant", messages=messages)
        reply = response.choices[0].message.content.strip()
        return ChatResponse(reply=reply)

    except Exception as e:
        logger.error("Chat error: %s", e, exc_info=True)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get a response")
