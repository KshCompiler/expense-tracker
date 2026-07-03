from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app import crud
from app.deps import get_current_user, get_db
from app.models import User
from app.schemas import IncomeIn, IncomeOut

router = APIRouter(prefix="/api/income", tags=["income"])


@router.post("", response_model=IncomeOut, status_code=status.HTTP_201_CREATED)
def create_income(payload: IncomeIn, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return crud.add_income(
        db, current_user.id, payload.amount, payload.source, payload.date.isoformat(), payload.description
    )
