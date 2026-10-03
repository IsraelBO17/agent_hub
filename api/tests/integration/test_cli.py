"""The operator's invite command (D9)."""

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.settings import get_settings
from app.features.auth.models import User
from app.features.auth.service import AuthService


async def test_invite_is_idempotent_by_email(sessions: async_sessionmaker[AsyncSession]) -> None:
    email = "Invitee@Example.com"
    try:
        async with sessions() as s:
            assert await AuthService(s, get_settings()).invite(email) is True
        async with sessions() as s:
            assert await AuthService(s, get_settings()).invite(email.lower()) is False
            user = await s.scalar(select(User).where(func.lower(User.email) == email.lower()))
            assert user is not None and user.status == "invited" and user.invited_at is not None
    finally:
        async with sessions() as s, s.begin():
            await s.execute(delete(User).where(func.lower(User.email) == email.lower()))
