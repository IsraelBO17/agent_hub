"""Queries for users and refresh_tokens. Flushes; never commits."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.auth.models import RefreshToken, User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, user_id: uuid.UUID) -> User | None:
        return await self.session.get(User, user_id)

    async def by_google_sub(self, sub: str) -> User | None:
        return await self.session.scalar(
            select(User).where(User.google_sub == sub).with_for_update()
        )

    async def invited_by_email(self, email: str) -> User | None:
        return await self.session.scalar(
            select(User)
            .where(func.lower(User.email) == email.lower(), User.status == "invited")
            .with_for_update()
        )

    async def by_email(self, email: str) -> User | None:
        return await self.session.scalar(
            select(User).where(func.lower(User.email) == email.lower())
        )

    async def email_exists(self, email: str) -> bool:
        found = await self.session.scalar(
            select(User.id).where(func.lower(User.email) == email.lower()).limit(1)
        )
        return found is not None

    async def add_invited(self, email: str) -> User:
        user = User(email=email, status="invited", invited_at=datetime.now(UTC))
        self.session.add(user)
        await self.session.flush()
        return user

    async def flush(self) -> None:
        await self.session.flush()


class RefreshTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def by_hash_for_update(self, token_hash: bytes) -> RefreshToken | None:
        """Locks the row, so two refreshes with the same token are decided one after the other."""
        return await self.session.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash).with_for_update()
        )

    async def add(
        self,
        *,
        user_id: uuid.UUID,
        family_id: uuid.UUID,
        token_hash: bytes,
        expires_at: datetime,
        user_agent: str | None,
        ip: str | None,
    ) -> RefreshToken:
        row = RefreshToken(
            user_id=user_id,
            family_id=family_id,
            token_hash=token_hash,
            expires_at=expires_at,
            user_agent=user_agent,
            ip=ip,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def mark_rotated(self, row: RefreshToken) -> None:
        row.rotated_at = datetime.now(UTC)
        await self.session.flush()

    async def revoke_family(self, family_id: uuid.UUID) -> None:
        await self.session.execute(
            update(RefreshToken)
            .where(RefreshToken.family_id == family_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=func.now())
        )
