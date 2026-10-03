"""Operator commands, against the database in DATABASE_URL.

python -m app.cli users invite <email>      let this email sign in with Google (make invite)
python -m app.cli users local-token <email> LOCAL ONLY: an active test user and an access
                                            token, to call the API without Google (make docs)
"""

import argparse
import asyncio
import sys
from urllib.parse import urlparse

from app.core.auth import issue_access_token
from app.core.db import init_db
from app.core.settings import get_settings
from app.features.auth.service import AuthService


async def _invite(email: str) -> int:
    settings = get_settings()
    db = init_db(settings)
    try:
        async with db.sessions() as session:
            created = await AuthService(session, settings).invite(email)
    finally:
        await db.engine.dispose()
    print(f"invited {email}" if created else f"{email} already exists; nothing changed")
    return 0


LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


async def _local_token(email: str) -> int:
    """Refuses anything but a local environment and a local database: this makes an active user
    without Google, which must never happen on a deployed database."""
    settings = get_settings()
    host = urlparse(settings.database_url.replace("+psycopg", "")).hostname
    if settings.env != "local" or host not in LOCAL_HOSTS:
        print("local-token works only with APP_ENV=local and a localhost database", file=sys.stderr)
        return 2
    db = init_db(settings)
    try:
        async with db.sessions() as session:
            user_id = await AuthService(session, settings).activate_local_test_user(email)
    finally:
        await db.engine.dispose()
    print(issue_access_token(settings, user_id))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="app.cli")
    commands = parser.add_subparsers(dest="group", required=True)
    users = commands.add_parser("users").add_subparsers(dest="command", required=True)
    invite = users.add_parser("invite", help="let this email sign in with Google (D9)")
    invite.add_argument("email")
    local = users.add_parser("local-token", help="LOCAL ONLY: active test user + access token")
    local.add_argument("email")
    args = parser.parse_args(argv)
    if "@" not in args.email:
        parser.error("not an email address")
    if args.command == "local-token":
        return asyncio.run(_local_token(args.email.strip()))
    return asyncio.run(_invite(args.email.strip()))


if __name__ == "__main__":
    sys.exit(main())
