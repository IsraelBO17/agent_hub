"""Operator commands. `python -m app.cli users invite <email>` (make invite email=...).

Runs against the database in DATABASE_URL (for Neon, pass the URL from Secrets Manager).
"""

import argparse
import asyncio
import sys

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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="app.cli")
    commands = parser.add_subparsers(dest="group", required=True)
    users = commands.add_parser("users").add_subparsers(dest="command", required=True)
    invite = users.add_parser("invite", help="let this email sign in with Google (D9)")
    invite.add_argument("email")
    args = parser.parse_args(argv)
    if "@" not in args.email:
        parser.error("not an email address")
    return asyncio.run(_invite(args.email.strip()))


if __name__ == "__main__":
    sys.exit(main())
