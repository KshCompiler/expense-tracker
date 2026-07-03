from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app import crud
from app.constants import VALID_INCOME_SOURCES
from app.deps import get_current_user, get_db
from app.models import User
from app.schemas import IncomeIn, IncomeOut
from app.validation import validate_transaction_input

router = APIRouter(prefix="/api/income", tags=["income"])


@router.post("", response_model=IncomeOut, status_code=status.HTTP_201_CREATED)
def create_income(payload: IncomeIn, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    amount, date = validate_transaction_input(
        payload.amount, payload.source, VALID_INCOME_SOURCES, payload.date, "source", "income source"
    )
    return crud.add_income(db, current_user.id, amount, payload.source, date, payload.description)
