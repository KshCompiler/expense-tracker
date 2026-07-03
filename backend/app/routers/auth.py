from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app import crud
from app.config import settings
from app.constants import EMAIL_REGEX
from app.deps import get_current_user, get_db
from app.models import User
from app.schemas import LoginRequest, RegisterRequest, UserOut
from app.security import COOKIE_NAME, create_access_token, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if not payload.full_name or not payload.email or not payload.password or not payload.confirm_password:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="All fields are required!")

    if payload.password != payload.confirm_password:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Passwords do not match!")

    if not EMAIL_REGEX.match(payload.email):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Please enter a valid email address!")

    if len(payload.password) < 8:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Password must be at least 8 characters long!")

    if crud.get_user_by_email(db, payload.email):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="An account with this email already exists!")

    try:
        user = crud.create_user(db, payload.full_name, payload.email, payload.password)
    except Exception:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="An error occurred. Please try again.")
    return user


@router.post("/login", response_model=UserOut)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    if not payload.email or not payload.password:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Email and password are required!")

    user = crud.get_user_by_email(db, payload.email)
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password!")

    token = create_access_token(user.id)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="strict",
        secure=settings.cookie_secure,
        path="/",
    )
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/")


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user
