from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import crud
from app.deps import get_current_user, get_db
from app.models import User
from app.schemas import TransactionsPage

router = APIRouter(prefix="/api/transactions", tags=["transactions"])

PER_PAGE = 20


def _parse_date(raw: str | None) -> str | None:
    if not raw:
        return None
    try:
        datetime.strptime(raw, "%Y-%m-%d")
        return raw
    except ValueError:
        return None


@router.get("", response_model=TransactionsPage)
def list_transactions(
    from_date: str | None = Query(default=None),
    to_date: str | None = Query(default=None),
    q: str | None = Query(default=None),
    page: int = Query(default=1),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    parsed_from = _parse_date(from_date)
    parsed_to = _parse_date(to_date)
    query = (q or "").strip() or None

    # Unlike the original Flask route (which left `transactions` as None and
    # blanked the entire results section), an invalid range here returns an
    # explicit empty page with `invalid_range=True` so the frontend can show
    # a proper empty-state message instead of hiding the whole UI.
    if parsed_from and parsed_to and parsed_from > parsed_to:
        return TransactionsPage(items=[], page=1, per_page=PER_PAGE, total=0, total_pages=1, invalid_range=True)

    total = crud.count_filtered_transactions(db, current_user.id, parsed_from, parsed_to, query)
    total_pages = max(1, -(-total // PER_PAGE))
    page = max(1, min(page, total_pages))
    offset = (page - 1) * PER_PAGE

    items = crud.get_filtered_transactions(db, current_user.id, parsed_from, parsed_to, query, PER_PAGE, offset)

    return TransactionsPage(
        items=items,
        page=page,
        per_page=PER_PAGE,
        total=total,
        total_pages=total_pages,
        invalid_range=False,
    )
