import logging
import time
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app import crud, oauth
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

OAUTH_PROVIDERS = {"google", "linkedin", "microsoft"}

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


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite=settings.cookie_samesite,
        secure=settings.cookie_secure,
        path="/",
    )


def _oauth_error_message(provider: str) -> str:
    return (
        f"{provider.capitalize()} sign-in isn't available right now. "
        "Please try again or sign in with your password."
    )


def _oauth_error_redirect(message: str) -> RedirectResponse:
    url = f"{settings.frontend_base_url}/login?oauth_error={quote(message)}"
    return RedirectResponse(url, status_code=status.HTTP_302_FOUND)


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
    if not user or user.password_hash is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password!")

    token = create_access_token(user.id)
    _set_session_cookie(response, token)
    return user


@router.get("/{provider}/login")
def oauth_login(provider: str):
    if provider not in OAUTH_PROVIDERS:
        raise HTTPException(status.HTTP_404_NOT_FOUND)

    if not oauth.is_configured(provider):
        return _oauth_error_redirect(_oauth_error_message(provider))

    state = oauth.generate_state()
    redirect = RedirectResponse(oauth.build_authorize_url(provider, state), status_code=status.HTTP_302_FOUND)
    redirect.set_cookie(
        key=oauth.OAUTH_STATE_COOKIE,
        value=state,
        httponly=True,
        # Always "lax", regardless of settings.cookie_samesite: the provider
        # sends the browser back to our /callback via a cross-site top-level
        # GET redirect, and a "strict" cookie (this app's default for the
        # session cookie) is never sent on that request - only "lax" (or
        # "none") survives it. This is the standard SameSite level for an
        # OAuth state/nonce cookie, independent of the session cookie policy.
        samesite="lax",
        secure=settings.cookie_secure,
        max_age=oauth.OAUTH_STATE_MAX_AGE_SECONDS,
        path="/",
    )
    return redirect


@router.get("/{provider}/callback")
def oauth_callback(
    provider: str,
    request: Request,
    code: str | None = None,
    state: str | None = None,
    db: Session = Depends(get_db),
):
    if provider not in OAUTH_PROVIDERS:
        raise HTTPException(status.HTTP_404_NOT_FOUND)

    cookie_state = request.cookies.get(oauth.OAUTH_STATE_COOKIE)

    def _finish(redirect: RedirectResponse) -> RedirectResponse:
        # Delete the state cookie on every code path, success or failure.
        # samesite must match what it was set with ("lax") for the browser to
        # recognize this as clearing the same cookie.
        redirect.delete_cookie(
            oauth.OAUTH_STATE_COOKIE,
            path="/",
            samesite="lax",
            secure=settings.cookie_secure,
        )
        return redirect

    if not code or not state or not cookie_state or state != cookie_state:
        return _finish(_oauth_error_redirect("Sign-in failed. Please try again."))

    try:
        access_token = oauth.exchange_code_for_token(provider, code)
        userinfo = oauth.fetch_userinfo(provider, access_token)
        user = crud.get_or_create_oauth_user(
            db,
            provider=provider,
            provider_user_id=userinfo["sub"],
            email=userinfo["email"],
            full_name=userinfo["name"],
            email_verified=userinfo["email_verified"],
        )
    except oauth.OAuthError:
        return _finish(_oauth_error_redirect(_oauth_error_message(provider)))
    except crud.OAuthUnverifiedEmailError:
        return _finish(_oauth_error_redirect(
            "We couldn't verify your email with that provider. Please try again or sign in with your password."
        ))
    except Exception:
        logger.exception("Unexpected OAuth callback error for provider=%s", provider)
        return _finish(_oauth_error_redirect("Something went wrong signing you in. Please try again."))

    token = create_access_token(user.id)
    redirect = RedirectResponse(f"{settings.frontend_base_url}/dashboard", status_code=status.HTTP_302_FOUND)
    _set_session_cookie(redirect, token)
    return _finish(redirect)


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
        # user.password_hash may be None (an OAuth-only account) - fall back to
        # "" so the checksum still has something deterministic to hash. Once
        # this reset flow assigns a real password, that checksum no longer
        # matches, so the link still becomes single-use as intended.
        token = create_password_reset_token(user.id, user.password_hash or "")
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
    if user is None or not verify_password_reset_checksum(pwh_claim, user.password_hash or ""):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=RESET_TOKEN_INVALID_MESSAGE)

    crud.update_user_password(db, user, hash_password(payload.password))
    return MessageOut(message="Your password has been reset. You can now sign in.")
