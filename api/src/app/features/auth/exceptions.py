"""Typed errors for auth. Each code is in openapi.yaml's ErrorCode enum."""

from app.core.errors import ApiError, Forbidden, Unauthenticated


class InvalidGoogleToken(Unauthenticated):
    code, title = "invalid_google_token", "Google sign-in failed"


class SessionExpired(Unauthenticated):
    code, title = "session_expired", "Your session has ended; sign in again"


class NotInvited(Forbidden):
    code, title = "not_invited", "This Google account doesn't have access to Agent Hub"


class AccountDisabled(Forbidden):
    code, title = "account_disabled", "This account is disabled"


class OriginNotAllowed(Forbidden):
    code, title = "origin_not_allowed", "Requests from this origin aren't allowed"


class IdentityProviderUnavailable(ApiError):
    status, code, title, retryable = (
        503,
        "identity_provider_unavailable",
        "Google sign-in is unavailable; try again",
        True,
    )
