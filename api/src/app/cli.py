"""Operator commands (`hub`), against the database in DATABASE_URL. Run from api/.

hub agents add <descriptor.yaml>   register an agent, or update it to match its descriptor (D6)
hub agents list                    the whole registry, retired and hidden included
hub users invite <email>           let this email sign in with Google (make invite)
hub users local-token <email>      LOCAL ONLY: an active test user and an access token, to call
                                   the API without Google (make docs)
"""

import argparse
import asyncio
import sys
from collections.abc import Awaitable, Callable
from pathlib import Path
from urllib.parse import urlparse

import yaml
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import issue_access_token
from app.core.db import Database
from app.core.errors import ApiError
from app.core.settings import Settings, get_settings
from app.features.agents.descriptor import AgentDescriptor, load_descriptor
from app.features.agents.service import AgentService
from app.features.auth.service import AuthService


async def _in_session[T](work: Callable[[AsyncSession, Settings], Awaitable[T]]) -> T:
    """One session on a private engine (not the app's `init_db` global), disposed afterwards."""
    settings = get_settings()
    db = Database(settings)
    try:
        async with db.sessions() as session:
            return await work(session, settings)
    finally:
        await db.engine.dispose()


async def _invite(email: str) -> int:
    created = await _in_session(lambda s, settings: AuthService(s, settings).invite(email))
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
    user_id = await _in_session(
        lambda s, settings: AuthService(s, settings).activate_local_test_user(email)
    )
    print(issue_access_token(settings, user_id))
    return 0


def _read_descriptor(path: str) -> AgentDescriptor | None:
    try:
        return load_descriptor(Path(path))
    except OSError as exc:
        print(f"can't read {path}: {exc.strerror}", file=sys.stderr)
    except yaml.YAMLError as exc:
        print(f"{path} isn't valid YAML: {exc}", file=sys.stderr)
    except ValidationError as exc:
        print(f"{path} isn't a valid descriptor:", file=sys.stderr)
        for err in exc.errors():
            where = ".".join(str(p) for p in err["loc"]) or "(top level)"
            print(f"  {where}: {err['msg']}", file=sys.stderr)
    return None


async def _agents_add(path: str) -> int:
    descriptor = _read_descriptor(path)
    if descriptor is None:
        return 1
    settings = get_settings()
    try:
        result = await _in_session(lambda s, st: AgentService(s, st).register(descriptor))
    except ApiError as exc:
        print(f"{exc.code}: {exc}", file=sys.stderr)
        return 1
    slug, version = descriptor.slug, descriptor.version or "no version"
    if result.action == "unchanged":
        print(f"{slug} unchanged ({settings.env})")
        return 0
    if result.action == "updated" and result.previous_version != descriptor.version:
        print(
            f"updated {slug}: {result.previous_version or 'no version'} → {version} ({settings.env})"
        )
    else:
        print(f"{result.action} {slug} ({version}, {settings.env})")
    if descriptor.runtime_type == "agentcore":
        print("the API can call it only if its runtime ARN is in infra's agent_runtime_arns (D27)")
    return 0


async def _agents_list() -> int:
    settings = get_settings()
    agents = await _in_session(lambda s, st: AgentService(s, st).registry())
    if not agents:
        print(f"no agents registered ({settings.env})")
        return 0
    rows = [("SLUG", "NAME", "STAGE", "STATUS", "VISIBILITY", "VERSION", "RETIRED")]
    rows += [
        (
            a.slug,
            a.name,
            a.stage,
            a.status,
            a.visibility,
            a.version or "-",
            a.retired_at.date().isoformat() if a.retired_at else "-",
        )
        for a in agents
    ]
    widths = [max(len(r[i]) for r in rows) for i in range(len(rows[0]))]
    for r in rows:
        print("  ".join(cell.ljust(w) for cell, w in zip(r, widths, strict=True)).rstrip())
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="hub", description="Agent Hub operator commands.")
    groups = parser.add_subparsers(dest="group", required=True)

    agents = groups.add_parser("agents", help="the agent registry (D6)")
    agent_cmds = agents.add_subparsers(dest="command", required=True)
    add = agent_cmds.add_parser("add", help="register an agent, or update it from its descriptor")
    add.add_argument("descriptor", help="path to the agent's YAML, e.g. ../agents/<slug>.yaml")
    agent_cmds.add_parser("list", help="every registered agent")

    users = groups.add_parser("users", help="who may sign in (D9)")
    user_cmds = users.add_subparsers(dest="command", required=True)
    invite = user_cmds.add_parser("invite", help="let this email sign in with Google")
    invite.add_argument("email")
    local = user_cmds.add_parser("local-token", help="LOCAL ONLY: active test user + access token")
    local.add_argument("email")

    args = parser.parse_args(argv)
    if args.group == "agents":
        if args.command == "add":
            return asyncio.run(_agents_add(args.descriptor))
        return asyncio.run(_agents_list())
    if "@" not in args.email:
        parser.error("not an email address")
    if args.command == "local-token":
        return asyncio.run(_local_token(args.email.strip()))
    return asyncio.run(_invite(args.email.strip()))


if __name__ == "__main__":
    sys.exit(main())
