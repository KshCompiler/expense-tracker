import hashlib
from datetime import datetime, timedelta, timezone

import jwt
from werkzeug.security import check_password_hash, generate_password_hash

from app.config import settings

ALGORITHM = "HS256"
COOKIE_NAME = "access_token"
ACCESS_TOKEN_PURPOSE = "access"
RESET_TOKEN_PURPOSE = "password_reset"


def hash_password(password: str) -> str:
    return generate_password_hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return check_password_hash(password_hash, password)


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": str(user_id), "purpose": ACCESS_TOKEN_PURPOSE, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        # A missing purpose claim means a session cookie issued before this
        # claim existed - still accepted so no one gets logged out on deploy.
        # Anything with an explicit *different* purpose (e.g. a password
        # reset token) must never be usable as a session token.
        if payload.get("purpose") not in (None, ACCESS_TOKEN_PURPOSE):
            return None
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None


def _password_reset_checksum(password_hash: str) -> str:
    # A checksum of the password hash at issue time, not the hash itself -
    # lets reset_password detect a replayed token without a DB column: once
    # the password actually changes, the checksum computed here goes stale.
    # The single owner of this algorithm - create and verify both call this,
    # so there is exactly one place that can drift.
    return hashlib.sha256(password_hash.encode()).hexdigest()[:16]


def create_password_reset_token(user_id: int, password_hash: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.password_reset_token_expire_minutes)
    checksum = _password_reset_checksum(password_hash)
    payload = {"sub": str(user_id), "purpose": RESET_TOKEN_PURPOSE, "pwh": checksum, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_password_reset_token(token: str) -> tuple[int, str] | None:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        if payload.get("purpose") != RESET_TOKEN_PURPOSE:
            return None
        return int(payload["sub"]), str(payload["pwh"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None


def verify_password_reset_checksum(pwh_claim: str, current_password_hash: str) -> bool:
    return _password_reset_checksum(current_password_hash) == pwh_claim
