import logging
import time

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app import crud
from app.config import settings
from app.deps import get_current_user, get_db
from app.email import send_password_reset_email
from app.models import User
from app.schemas import ForgotPasswordRequest, LoginRequest, MessageOut, RegisterRequest, ResetPasswordRequest, UserOut
from app.security import (
    COOKIE_NAME,
    create_access_token,
    create_password_reset_token,
    decode_password_reset_token,
    hash_password,
    verify_password,
    verify_password_reset_checksum,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])
logger = logging.getLogger(__name__)

# Kept as the exact string ResetPassword.tsx matches on to show its "VOID"
# stamp state instead of a generic error banner - if this message changes,
# frontend/src/pages/ResetPassword.tsx's RESET_TOKEN_INVALID_MESSAGE must
# change with it.
RESET_TOKEN_INVALID_MESSAGE = "This reset link is invalid or has expired."
# Minimum time (seconds) the forgot-password route takes to respond, so an
# unregistered email (no SMTP call) isn't distinguishable from a registered
# one (real SMTP round-trip) by response latency - the response body is
# already identical either way, this closes the timing side channel too.
FORGOT_PASSWORD_MIN_RESPONSE_SECONDS = 0.3


def _forgot_password_message() -> str:
    return (
        "If an account exists for that email, we've sent a password reset link. "
        f"It expires in {settings.password_reset_token_expire_minutes} minutes."
    )


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if crud.get_user_by_email(db, payload.email):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="An account with this email already exists!")

    try:
        user = crud.create_user(db, payload.full_name, payload.email, payload.password)
    except Exception:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="An error occurred. Please try again.")
    return user


@router.post("/login", response_model=UserOut)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, payload.email)
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password!")

    token = create_access_token(user.id)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite=settings.cookie_samesite,
        secure=settings.cookie_secure,
        path="/",
    )
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response):
    response.delete_cookie(
        COOKIE_NAME,
        path="/",
        samesite=settings.cookie_samesite,
        secure=settings.cookie_secure,
    )


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/forgot-password", response_model=MessageOut)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    start = time.monotonic()
    user = crud.get_user_by_email(db, payload.email)
    if user is not None:
        token = create_password_reset_token(user.id, user.password_hash)
        reset_link = f"{settings.frontend_base_url}/reset-password?token={token}"
        try:
            send_password_reset_email(user.email, reset_link)
        except Exception:
            logger.exception("Failed to send password reset email")

    elapsed = time.monotonic() - start
    if elapsed < FORGOT_PASSWORD_MIN_RESPONSE_SECONDS:
        time.sleep(FORGOT_PASSWORD_MIN_RESPONSE_SECONDS - elapsed)
    return MessageOut(message=_forgot_password_message())


@router.post("/reset-password", response_model=MessageOut)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    decoded = decode_password_reset_token(payload.token)
    if decoded is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=RESET_TOKEN_INVALID_MESSAGE)

    user_id, pwh_claim = decoded
    user = crud.get_user_by_id(db, user_id)
    if user is None or not verify_password_reset_checksum(pwh_claim, user.password_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=RESET_TOKEN_INVALID_MESSAGE)

    crud.update_user_password(db, user, hash_password(payload.password))
    return MessageOut(message="Your password has been reset. You can now sign in.")
