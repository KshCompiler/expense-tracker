from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud
from app.deps import get_current_user, get_db
from app.models import User
from app.schemas import ExpenseIn, ExpenseOut

router = APIRouter(prefix="/api/expenses", tags=["expenses"])


def _get_owned_expense(db: Session, expense_id: int, current_user: User):
    expense = crud.get_expense_by_id(db, expense_id)
    if not expense or expense.user_id != current_user.id:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="Expense not found or you don't have permission to access it.",
        )
    return expense


@router.post("", response_model=ExpenseOut, status_code=status.HTTP_201_CREATED)
def create_expense(payload: ExpenseIn, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return crud.add_expense(
        db, current_user.id, payload.amount, payload.category, payload.date.isoformat(), payload.description
    )


@router.get("/{expense_id}", response_model=ExpenseOut)
def get_expense(expense_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _get_owned_expense(db, expense_id, current_user)


@router.put("/{expense_id}", response_model=ExpenseOut)
def edit_expense(
    expense_id: int,
    payload: ExpenseIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_owned_expense(db, expense_id, current_user)
    return crud.update_expense(
        db, expense_id, payload.amount, payload.category, payload.date.isoformat(), payload.description
    )


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(expense_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _get_owned_expense(db, expense_id, current_user)
    crud.delete_expense_helper(db, expense_id)
