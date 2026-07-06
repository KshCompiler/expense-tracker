import logging
import re
import statistics

from fastapi import APIRouter, Depends, HTTPException, status
from openai import OpenAI
from sqlalchemy.orm import Session

from app import crud
from app.config import settings
from app.deps import get_current_user, get_db
from app.models import User
from app.schemas import BudgetCategory, BudgetIn, BudgetOut, BudgetStatus, BudgetSuggestionOut, BudgetUpdateIn

router = APIRouter(prefix="/api/budgets", tags=["budgets"])
logger = logging.getLogger(__name__)


def _get_owned_budget(db: Session, budget_id: int, current_user: User):
    budget = crud.get_budget_by_id(db, budget_id)
    if not budget or budget.user_id != current_user.id:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="Budget not found or you don't have permission to access it.",
        )
    return budget


@router.get("", response_model=list[BudgetStatus])
def list_budgets(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return crud.compute_budget_statuses(db, current_user.id)


@router.post("", response_model=BudgetOut, status_code=status.HTTP_201_CREATED)
def create_budget(payload: BudgetIn, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if crud.get_budget_by_category(db, current_user.id, payload.category) is not None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="You already have a budget for this category — edit it instead.",
        )
    return crud.create_budget(db, current_user.id, payload.category, payload.monthly_limit)


@router.put("/{budget_id}", response_model=BudgetOut)
def edit_budget(
    budget_id: int,
    payload: BudgetUpdateIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_owned_budget(db, budget_id, current_user)
    return crud.update_budget(db, budget_id, payload.monthly_limit)


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_budget(budget_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _get_owned_budget(db, budget_id, current_user)
    crud.delete_budget(db, budget_id)


def _find_outlier_month(history: list[float]) -> int | None:
    """Flags a month that looks like a one-off spike (a wedding, a big
    one-time purchase) rather than a genuine change in spending level - one
    whose spend is far above the median of the *other* months. Returns its
    index, or None if no month stands out this way. Requires at least 3
    months so "the other months" is a meaningful baseline."""
    if len(history) < 3:
        return None
    for i, value in enumerate(history):
        baseline = statistics.median(history[:i] + history[i + 1 :])
        if baseline > 0 and value > baseline * 1.8:
            return i
    return None


def _weighted_average(history: list[float], exclude_index: int | None = None) -> float:
    """Recency-weighted mean - the most recent month counts for more than the
    oldest, so a category that's trending up or down shifts the anchor instead
    of being smoothed away by a flat average of all months. A month flagged as
    a one-off outlier is excluded entirely (weight 0) rather than allowed to
    drag the anchor up just because it happened to be recent."""
    if not history:
        return 0.0
    weights = [0.0 if i == exclude_index else w for i, w in enumerate(range(1, len(history) + 1))]
    total_weight = sum(weights)
    if total_weight == 0:
        return 0.0
    return sum(h * w for h, w in zip(history, weights)) / total_weight


def _describe_trend(history: list[float], exclude_index: int | None = None) -> str:
    trend_history = [h for i, h in enumerate(history) if i != exclude_index]
    if len(trend_history) < 2 or trend_history[0] <= 0:
        return "flat"
    change = (trend_history[-1] - trend_history[0]) / trend_history[0]
    if change > 0.15:
        return "rising"
    if change < -0.15:
        return "falling"
    return "flat"


def _build_suggestion_prompt(category: str, history: list[float], outlier_index: int | None) -> str:
    months_desc = ", ".join(f"₹{m:.0f}" for m in history)
    trend = _describe_trend(history, exclude_index=outlier_index)
    outlier_note = ""
    if outlier_index is not None:
        outlier_note = (
            f" The ₹{history[outlier_index]:.0f} month looks like a one-off spike (e.g. a big one-time "
            "purchase or event) rather than the new normal - treat it as an outlier and don't let it "
            "drive the suggested limit up."
        )
    return (
        f"You are a budgeting assistant inside Spendly, an expense tracker app. "
        f"A user wants a suggested monthly budget limit for the '{category}' category. "
        f"Their spending in this category over the last {len(history)} months was: {months_desc} "
        f"(oldest to newest) - the underlying trend (ignoring any outlier) is {trend}.{outlier_note} "
        "Weigh the most recent non-outlier month(s) more heavily than older ones instead of just "
        "averaging all months equally, especially if the trend is rising or falling. Reply with "
        "EXACTLY two lines, no other text:\n"
        "LIMIT: <a single number, no currency symbol or commas>\n"
        "RATIONALE: <no more than 10 words, plain language, mentioning the trend or outlier only if relevant>"
    )


MAX_RATIONALE_LENGTH = 80


def _shorten_rationale(rationale: str) -> str:
    rationale = rationale.strip()
    if len(rationale) <= MAX_RATIONALE_LENGTH:
        return rationale
    return rationale[:MAX_RATIONALE_LENGTH].rsplit(" ", 1)[0].rstrip(".,;:") + "…"


def _clamp_suggested_limit(raw_value: float, weighted_spend: float) -> float:
    floor, ceiling = weighted_spend * 0.5, weighted_spend * 2.0
    return round(max(floor, min(raw_value, ceiling)), 2)


@router.get("/suggest/{category}", response_model=BudgetSuggestionOut)
def suggest_budget_limit(
    category: BudgetCategory,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    history = crud.get_category_spend_history(db, current_user.id, category, months=3)
    outlier_index = _find_outlier_month(history)
    weighted_spend = _weighted_average(history, exclude_index=outlier_index)
    if weighted_spend <= 0:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"Not enough spending history for {category} yet to suggest a limit — "
            "add a few expenses first, or set one manually.",
        )

    try:
        api_key = settings.groq_api_key
        if not api_key:
            raise ValueError("GROQ_API_KEY not set")

        client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": _build_suggestion_prompt(category, history, outlier_index)}],
        )
        reply = response.choices[0].message.content.strip()

        limit_match = re.search(r"LIMIT:\s*₹?\s*([\d,]+\.?\d*)", reply)
        if not limit_match:
            raise ValueError(f"Could not parse a suggested limit from model reply: {reply!r}")
        raw_value = float(limit_match.group(1).replace(",", ""))
        if raw_value <= 0:
            raise ValueError("Model suggested a non-positive limit")

        rationale_match = re.search(r"RATIONALE:\s*(.+)", reply)
        rationale = (
            rationale_match.group(1).strip()
            if rationale_match
            else f"Based on your recent {category} spend of ₹{weighted_spend:.0f}/month."
        )

        return BudgetSuggestionOut(
            suggested_limit=_clamp_suggested_limit(raw_value, weighted_spend),
            rationale=_shorten_rationale(rationale),
        )

    except Exception as e:
        logger.error("Budget suggestion error: %s", e, exc_info=True)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get a budget suggestion")
