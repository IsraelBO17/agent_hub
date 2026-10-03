"""Auth rules and transactions: one method per capability block in SPEC.md (feature: auth)."""

import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import issue_access_token
from app.core.service import BaseService
from app.core.settings import Settings
from app.features.auth.exceptions import AccountDisabled, NotInvited, SessionExpired
from app.features.auth.google import GoogleIdentity
from app.features.auth.models import User
from app.features.auth.repository import RefreshTokenRepository, UserRepository
from app.features.auth.schemas import AccessToken, Me, Preferences, SignedIn


@dataclass(frozen=True)
class Client:
    """Where a session is used from, recorded on its refresh tokens."""

    user_agent: str | None
    ip: str | None


def hash_token(token: str) -> bytes:
    return hashlib.sha256(token.encode()).digest()


def to_me(user: User) -> Me:
    return Me(
        id=user.id,
        email=user.email,
        name=user.name,
        avatar_url=user.avatar_url,
        preferences=Preferences.model_validate(user.preferences or {}),
    )


class AuthService(BaseService):
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        super().__init__(session)
        self.settings = settings
        self.users = UserRepository(session)
        self.tokens = RefreshTokenRepository(session)

    async def sign_in(self, identity: GoogleIdentity, client: Client) -> tuple[SignedIn, str]:
        """The Google token is already verified (outside any transaction). Returns the response
        and the new refresh token for the cookie."""
        async with self.transaction():
            user = await self.users.by_google_sub(identity.sub)
            if user is None:
                user = await self.users.invited_by_email(identity.email)
                if user is None:
                    raise NotInvited(email=identity.email)
                user.google_sub = identity.sub
                user.status = "active"
            if user.status == "disabled":
                raise AccountDisabled()
            user.name = identity.name
            user.avatar_url = identity.picture
            user.last_login_at = datetime.now(UTC)
            await self.users.flush()
            refresh = await self._new_refresh_token(user.id, uuid.uuid4(), client)
            access = self._access_token(user.id)
            me = to_me(user)
        return SignedIn(**access.model_dump(), user=me), refresh

    async def refresh(self, token: str | None, client: Client) -> tuple[AccessToken, str]:
        if not token:
            raise SessionExpired()
        failure: Exception | None = None
        result: tuple[AccessToken, str] | None = None
        async with self.transaction():
            row = await self.tokens.by_hash_for_update(hash_token(token))
            if row is None or row.revoked_at is not None or row.expires_at <= datetime.now(UTC):
                raise SessionExpired()
            if row.rotated_at is not None:
                # Reuse of a rotated token: someone else may hold it. Sign the whole family out;
                # the revocation commits, then the error is raised (standard §11.2).
                await self.tokens.revoke_family(row.family_id)
                failure = SessionExpired()
            else:
                user = await self.users.get(row.user_id)
                if user is None or user.status != "active":
                    await self.tokens.revoke_family(row.family_id)
                    failure = AccountDisabled()
                else:
                    await self.tokens.mark_rotated(row)
                    new_token = await self._new_refresh_token(user.id, row.family_id, client)
                    result = (self._access_token(user.id), new_token)
        if failure is not None:
            raise failure
        if result is None:  # unreachable: every other path raised
            raise SessionExpired()
        return result

    async def sign_out(self, token: str | None) -> None:
        if not token:
            return
        async with self.transaction():
            row = await self.tokens.by_hash_for_update(hash_token(token))
            if row is not None:
                await self.tokens.revoke_family(row.family_id)

    async def me(self, user_id: uuid.UUID) -> Me | None:
        user = await self.users.get(user_id)
        if user is None or user.status != "active":
            return None
        return to_me(user)

    async def invite(self, email: str) -> bool:
        """Operator command: let `email` sign in. False if the email already exists."""
        async with self.transaction():
            if await self.users.email_exists(email):
                return False
            await self.users.add_invited(email)
        return True

    async def activate_local_test_user(self, email: str) -> uuid.UUID:
        """LOCAL TESTING ONLY (the CLI checks the environment and database first): an active user
        for `email`, with a placeholder Google sub, so the API can be called without Google."""
        async with self.transaction():
            user = await self.users.invited_by_email(email)
            if user is None and not await self.users.email_exists(email):
                user = await self.users.add_invited(email)
            if user is not None:
                user.google_sub = f"local-test:{email.lower()}"
                user.status = "active"
                await self.users.flush()
            found = user or await self.users.by_email(email)
            if found is None:
                raise NotInvited(email=email)
            return found.id

    async def _new_refresh_token(
        self, user_id: uuid.UUID, family_id: uuid.UUID, client: Client
    ) -> str:
        token = secrets.token_urlsafe(32)
        await self.tokens.add(
            user_id=user_id,
            family_id=family_id,
            token_hash=hash_token(token),
            expires_at=datetime.now(UTC) + timedelta(days=self.settings.refresh_token_ttl_days),
            user_agent=client.user_agent,
            ip=client.ip,
        )
        return token

    def _access_token(self, user_id: uuid.UUID) -> AccessToken:
        token = issue_access_token(self.settings, user_id)
        exp = jwt.decode(token, options={"verify_signature": False})["exp"]
        return AccessToken(access_token=token, expires_at=datetime.fromtimestamp(exp, UTC))
