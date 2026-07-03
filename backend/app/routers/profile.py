from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import crud
from app.deps import get_current_user, get_db
from app.models import User
from app.schemas import ProfileOut

router = APIRouter(prefix="/api", tags=["profile"])


@router.get("/profile", response_model=ProfileOut)
def get_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    total_expenses, total_income, transaction_count = crud.get_user_lifetime_totals(db, current_user.id)
    return ProfileOut(
        id=current_user.id,
        full_name=current_user.full_name,
        email=current_user.email,
        created_at=current_user.created_at,
        total_expenses_all_time=total_expenses,
        total_income_all_time=total_income,
        transaction_count_all_time=transaction_count,
    )
