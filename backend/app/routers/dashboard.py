from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import crud
from app.deps import get_current_user, get_db
from app.models import User
from app.schemas import CategoryTotal, DashboardOut, MonthlyTrendPoint

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardOut)
def get_dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    now = datetime.now()

    expenses = crud.get_user_expenses_this_month(db, current_user.id)
    income = crud.get_user_income_this_month(db, current_user.id)
    categories = crud.get_expenses_by_category(db, current_user.id)
    recent_transactions = crud.get_recent_transactions(db, current_user.id)
    monthly_trend = crud.get_monthly_expense_totals(db, current_user.id)

    total_expenses = sum(e.amount for e in expenses) if expenses else 0.0
    total_income = sum(i.amount for i in income) if income else 0.0

    return DashboardOut(
        user=current_user,
        today_date=now.strftime("%B %d, %Y"),
        current_time=now.strftime("%I:%M %p"),
        total_expenses=total_expenses,
        total_income=total_income,
        remaining_balance=total_income - total_expenses,
        transaction_count=len(expenses),
        categories=[CategoryTotal(category=c, total=t) for c, t in categories],
        recent_transactions=recent_transactions,
        has_transactions=len(recent_transactions) > 0,
        monthly_trend=[MonthlyTrendPoint(**point) for point in monthly_trend],
    )
