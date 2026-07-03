from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.models import User
from app.security import COOKIE_NAME, decode_access_token

__all__ = ["get_db", "get_current_user"]


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(COOKIE_NAME)
    user_id = decode_access_token(token) if token else None
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    user = crud.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    return user
