import secrets
from dataclasses import dataclass
from urllib.parse import urlencode

import httpx

from app.config import settings

OAUTH_STATE_COOKIE = "oauth_state"
OAUTH_STATE_MAX_AGE_SECONDS = 600  # 10 minutes - just long enough for a consent screen
_HTTP_TIMEOUT_SECONDS = 10.0


class OAuthError(Exception):
    """Any recoverable OAuth flow failure (misconfiguration, provider HTTP
    error, malformed response). The router catches this and redirects to
    /login?oauth_error=... with a generic message - the raw provider error
    text is never shown to the user."""


@dataclass(frozen=True)
class _ProviderConfig:
    authorize_url: str
    token_url: str
    userinfo_url: str
    scope: str
    client_id: str | None
    client_secret: str | None


def _config(provider: str) -> _ProviderConfig:
    if provider == "google":
        return _ProviderConfig(
            authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
            userinfo_url="https://www.googleapis.com/oauth2/v3/userinfo",
            scope="openid email profile",
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
        )
    if provider == "linkedin":
        return _ProviderConfig(
            authorize_url="https://www.linkedin.com/oauth/v2/authorization",
            token_url="https://www.linkedin.com/oauth/v2/accessToken",
            userinfo_url="https://api.linkedin.com/v2/userinfo",
            scope="openid profile email",
            client_id=settings.linkedin_client_id,
            client_secret=settings.linkedin_client_secret,
        )
    # Unreachable in practice - callers validate against the {"google", "linkedin"}
    # allowlist before ever calling into this module.
    raise ValueError(f"Unsupported provider: {provider}")


def redirect_uri_for(provider: str) -> str:
    return f"{settings.backend_base_url}/api/auth/{provider}/callback"


def is_configured(provider: str) -> bool:
    cfg = _config(provider)
    return bool(cfg.client_id and cfg.client_secret)


def generate_state() -> str:
    return secrets.token_urlsafe(32)


def build_authorize_url(provider: str, state: str) -> str:
    cfg = _config(provider)
    params = {
        "client_id": cfg.client_id,
        "redirect_uri": redirect_uri_for(provider),
        "response_type": "code",
        "scope": cfg.scope,
        "state": state,
    }
    return f"{cfg.authorize_url}?{urlencode(params)}"


def exchange_code_for_token(provider: str, code: str) -> str:
    cfg = _config(provider)
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri_for(provider),
        "client_id": cfg.client_id,
        "client_secret": cfg.client_secret,
    }
    try:
        resp = httpx.post(
            cfg.token_url, data=data, headers={"Accept": "application/json"}, timeout=_HTTP_TIMEOUT_SECONDS
        )
        resp.raise_for_status()
        token = resp.json().get("access_token")
    except httpx.HTTPError as exc:
        raise OAuthError(f"Token exchange with {provider} failed") from exc
    if not token:
        raise OAuthError(f"{provider} token response missing access_token")
    return token


def _to_bool(value) -> bool:
    # LinkedIn's OIDC userinfo endpoint has been observed to return
    # email_verified as a *string* ("true"/"false"), not a JSON boolean -
    # bool("false") is truthy, so this must be an explicit string check,
    # not a bare bool() coercion.
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() == "true"
    return bool(value)


def fetch_userinfo(provider: str, access_token: str) -> dict:
    cfg = _config(provider)
    try:
        resp = httpx.get(
            cfg.userinfo_url,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=_HTTP_TIMEOUT_SECONDS,
        )
        resp.raise_for_status()
        raw = resp.json()
    except httpx.HTTPError as exc:
        raise OAuthError(f"Fetching userinfo from {provider} failed") from exc

    # Google's and LinkedIn's OIDC userinfo responses both use `sub`, `email`,
    # `email_verified`, `name` - same claim names, so this is defensive
    # extraction/coercion rather than per-provider field mapping.
    sub = raw.get("sub")
    email = raw.get("email")
    if not sub or not email:
        raise OAuthError(f"{provider} userinfo response missing sub/email")

    return {
        "sub": str(sub),
        "email": str(email),
        "email_verified": _to_bool(raw.get("email_verified", False)),
        "name": raw.get("name") or email,
    }
