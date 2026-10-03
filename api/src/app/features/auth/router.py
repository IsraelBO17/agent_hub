"""HTTP endpoints for auth and /v1/me. Thin: parse, call the service, set the cookie."""

from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Request, Response, status

from app.core.auth import CurrentUser
from app.core.db import SessionDep
from app.core.errors import Unauthenticated
from app.core.settings import Settings, get_settings
from app.features.auth.exceptions import OriginNotAllowed
from app.features.auth.google import GoogleVerifier
from app.features.auth.schemas import AccessToken, GoogleSignIn, Me, SignedIn
from app.features.auth.service import AuthService, Client

COOKIE = "ah_refresh"
COOKIE_PATH = "/v1/auth"

SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_service(session: SessionDep, settings: SettingsDep) -> AuthService:
    return AuthService(session, settings)


def get_google_verifier(request: Request) -> GoogleVerifier:
    """Created in the lifespan; tests override this dependency with a stubbed key set."""
    verifier: GoogleVerifier = request.app.state.google_verifier
    return verifier


def require_allowed_origin(request: Request, settings: SettingsDep) -> None:
    """CSRF guard for the cookie endpoints, alongside SameSite=Strict (D8): the browser always
    sends Origin on these POSTs, so a missing one is refused too."""
    if request.headers.get("origin") not in settings.allowed_origins:
        raise OriginNotAllowed()


def client_of(request: Request) -> Client:
    return Client(
        user_agent=(request.headers.get("user-agent") or "")[:500] or None,
        ip=request.client.host if request.client else None,
    )


def set_refresh_cookie(response: Response, token: str, settings: Settings) -> None:
    response.set_cookie(
        COOKIE,
        token,
        max_age=settings.refresh_token_ttl_days * 86400,
        path=COOKIE_PATH,
        secure=True,
        httponly=True,
        samesite="strict",
    )  # host-only: no Domain attribute (D8, D25)


Service = Annotated[AuthService, Depends(get_service)]
Verifier = Annotated[GoogleVerifier, Depends(get_google_verifier)]
RefreshCookie = Annotated[str | None, Cookie(alias=COOKIE)]

auth = APIRouter(prefix="/v1/auth", tags=["auth"], dependencies=[Depends(require_allowed_origin)])
me_router = APIRouter(prefix="/v1", tags=["me"])


@auth.post("/google")
async def sign_in_with_google(
    body: GoogleSignIn,
    request: Request,
    response: Response,
    svc: Service,
    verifier: Verifier,
    settings: SettingsDep,
) -> SignedIn:
    identity = await verifier.verify(body.id_token)  # outside any transaction
    signed_in, refresh = await svc.sign_in(identity, client_of(request))
    set_refresh_cookie(response, refresh, settings)
    return signed_in


@auth.post("/refresh")
async def refresh_session(
    request: Request,
    response: Response,
    svc: Service,
    settings: SettingsDep,
    token: RefreshCookie = None,
) -> AccessToken:
    access, refresh = await svc.refresh(token, client_of(request))
    set_refresh_cookie(response, refresh, settings)
    return access


@auth.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def sign_out(response: Response, svc: Service, token: RefreshCookie = None) -> None:
    await svc.sign_out(token)
    response.delete_cookie(COOKIE, path=COOKIE_PATH, secure=True, httponly=True, samesite="strict")


@me_router.get("/me")
async def get_me(user: CurrentUser, svc: Service) -> Me:
    me = await svc.me(user.user_id)
    if me is None:  # the user was removed or disabled after the token was issued
        raise Unauthenticated()
    return me
