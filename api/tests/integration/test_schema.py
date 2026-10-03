"""Schema behaviour tests (docs/DATA_MODEL.md): the constraints the database enforces.

Runs on the local test database (`make db-up`). The migrations are applied from scratch
(downgrade to base, then upgrade to head, so both directions are exercised); each test runs in a
rolled-back transaction.
"""

import os
import uuid
from collections.abc import Callable, Iterator
from typing import Any

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Connection, Engine, create_engine, text
from sqlalchemy.exc import IntegrityError

from app.core.settings import get_settings

World = dict[str, Any]


@pytest.fixture(scope="module")
def engine() -> Iterator[Engine]:
    cfg = Config(os.path.join(os.path.dirname(__file__), "..", "..", "alembic.ini"))
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")
    eng = create_engine(get_settings().migrations_url)
    yield eng
    eng.dispose()


@pytest.fixture
def db(engine: Engine) -> Iterator[Connection]:
    with engine.connect() as conn:
        tx = conn.begin()
        yield conn
        tx.rollback()


def insert(db: Connection, sql: str, **params: Any) -> Any:
    return db.execute(text(sql), params).scalar()


@pytest.fixture
def world(db: Connection) -> World:
    """Two users, one agent, one session for user A."""
    a = insert(
        db,
        "INSERT INTO users (google_sub, email, status) VALUES ('sub-a', 'A@x.dev', 'active') RETURNING id",
    )
    b = insert(
        db,
        "INSERT INTO users (google_sub, email, status) VALUES ('sub-b', 'b@x.dev', 'active') RETURNING id",
    )
    agent = insert(
        db,
        "INSERT INTO agents (slug, name, description, icon, color, runtime_type, runtime_arn)"
        " VALUES ('research-analyst', 'Research Analyst', 'd', 'search', 'blue', 'agentcore', 'arn:x') RETURNING id",
    )
    session = insert(
        db, "INSERT INTO sessions (user_id, agent_id) VALUES (:u, :a) RETURNING id", u=a, a=agent
    )
    return {"a": a, "b": b, "agent": agent, "session": session}


def add_message(
    db: Connection,
    w: World,
    seq: int,
    role: str = "user",
    status: str = "complete",
    client_id: Any = None,
    user: Any = None,
) -> Any:
    return insert(
        db,
        "INSERT INTO messages (session_id, user_id, seq, role, status, client_message_id)"
        " VALUES (:s, :u, :seq, :role, :status, :cid) RETURNING id",
        s=w["session"],
        u=user or w["a"],
        seq=seq,
        role=role,
        status=status,
        cid=client_id,
    )


def fails(db: Connection, fn: Callable[[], Any]) -> None:
    sp = db.begin_nested()
    with pytest.raises(IntegrityError):
        fn()
    sp.rollback()


def test_email_unique_case_insensitive(db: Connection, world: World) -> None:
    fails(db, lambda: insert(db, "INSERT INTO users (email) VALUES ('a@X.dev') RETURNING id"))


def test_active_user_needs_google_sub(db: Connection) -> None:
    fails(
        db,
        lambda: insert(
            db, "INSERT INTO users (email, status) VALUES ('c@x.dev', 'active') RETURNING id"
        ),
    )


def test_agent_needs_runtime_target(db: Connection) -> None:
    fails(
        db,
        lambda: insert(
            db,
            "INSERT INTO agents (slug, name, description, icon, color, runtime_type)"
            " VALUES ('x', 'X', 'd', 'bot', 'red', 'agentcore') RETURNING id",
        ),
    )


def test_one_streaming_reply_per_session(db: Connection, world: World) -> None:
    add_message(db, world, 1)
    add_message(db, world, 2, role="assistant", status="streaming")
    add_message(db, world, 3)
    fails(db, lambda: add_message(db, world, 4, role="assistant", status="streaming"))


def test_reply_waiting_for_approval_blocks_another_open_reply(db: Connection, world: World) -> None:
    add_message(db, world, 1)
    add_message(db, world, 2, role="assistant", status="awaiting_approval")
    add_message(db, world, 3)
    fails(db, lambda: add_message(db, world, 4, role="assistant", status="streaming"))


def test_send_is_idempotent(db: Connection, world: World) -> None:
    cid = uuid.uuid4()
    add_message(db, world, 1, client_id=cid)
    fails(db, lambda: add_message(db, world, 2, client_id=cid))


def test_send_is_idempotent_across_a_users_sessions(db: Connection, world: World) -> None:
    # The first send creates the session, so a resend must collide even though it targets a new session (F03).
    cid = uuid.uuid4()
    add_message(db, world, 1, client_id=cid)
    other = insert(
        db,
        "INSERT INTO sessions (user_id, agent_id) VALUES (:u, :a) RETURNING id",
        u=world["a"],
        a=world["agent"],
    )
    fails(db, lambda: add_message(db, {**world, "session": other}, 1, client_id=cid))
    b_session = insert(
        db,
        "INSERT INTO sessions (user_id, agent_id) VALUES (:u, :a) RETURNING id",
        u=world["b"],
        a=world["agent"],
    )
    add_message(db, {**world, "session": b_session}, 1, client_id=cid, user=world["b"])


def test_seq_unique_within_session(db: Connection, world: World) -> None:
    add_message(db, world, 1)
    fails(db, lambda: add_message(db, world, 1))


def test_user_message_is_always_complete(db: Connection, world: World) -> None:
    fails(db, lambda: add_message(db, world, 1, status="streaming"))


def test_cannot_attach_rows_to_another_users_session(db: Connection, world: World) -> None:
    fails(db, lambda: add_message(db, world, 1, user=world["b"]))


def test_approval_rules(db: Connection, world: World) -> None:
    msg = add_message(db, world, 1, role="assistant", status="streaming")
    tool = insert(
        db,
        "INSERT INTO tool_calls (message_id, session_id, user_id, tool_use_id, name, status)"
        " VALUES (:m, :s, :u, 't1', 'execute_transfer', 'awaiting_approval') RETURNING id",
        m=msg,
        s=world["session"],
        u=world["a"],
    )
    approval = insert(
        db,
        "INSERT INTO approval_requests (tool_call_id, message_id, session_id, user_id, agent_id, tool_name,"
        " arguments, expires_at) VALUES (:t, :m, :s, :u, :a, 'execute_transfer', '{}', now() + interval '10 min')"
        " RETURNING id",
        t=tool,
        m=msg,
        s=world["session"],
        u=world["a"],
        a=world["agent"],
    )
    # Cannot execute while pending, cannot be approved without a decision time.
    fails(
        db,
        lambda: db.execute(
            text("UPDATE approval_requests SET executed_at = now() WHERE id = :i"), {"i": approval}
        ),
    )
    fails(
        db,
        lambda: db.execute(
            text("UPDATE approval_requests SET status = 'approved' WHERE id = :i"), {"i": approval}
        ),
    )
    db.execute(
        text("UPDATE approval_requests SET status = 'denied', decided_at = now() WHERE id = :i"),
        {"i": approval},
    )
    fails(
        db,
        lambda: db.execute(
            text("UPDATE approval_requests SET executed_at = now() WHERE id = :i"), {"i": approval}
        ),
    )


def test_deleting_a_session_cascades(db: Connection, world: World) -> None:
    msg = add_message(db, world, 1)
    insert(
        db,
        "INSERT INTO files (user_id, session_id, message_id, purpose, s3_key, filename, content_type)"
        " VALUES (:u, :s, :m, 'upload', 'k1', 'a.pdf', 'application/pdf') RETURNING id",
        u=world["a"],
        s=world["session"],
        m=msg,
    )
    art = insert(
        db,
        "INSERT INTO artifacts (session_id, user_id, artifact_key, type, title)"
        " VALUES (:s, :u, 'doc1', 'document', 'Brief') RETURNING id",
        s=world["session"],
        u=world["a"],
    )
    insert(
        db,
        "INSERT INTO artifact_versions (artifact_id, user_id, version, status, content)"
        " VALUES (:a, :u, 1, 'complete', '# Brief') RETURNING id",
        a=art,
        u=world["a"],
    )
    db.execute(text("DELETE FROM sessions WHERE id = :s"), {"s": world["session"]})
    for table in ("messages", "files", "artifacts", "artifact_versions"):
        count = text(f"SELECT count(*) FROM {table}")  # noqa: S608  (table names from the tuple above)
        assert db.execute(count).scalar() == 0, table


def test_agent_with_sessions_cannot_be_deleted(db: Connection, world: World) -> None:
    fails(db, lambda: db.execute(text("DELETE FROM agents WHERE id = :a"), {"a": world["agent"]}))


def test_message_search(db: Connection, world: World) -> None:
    insert(
        db,
        "INSERT INTO messages (session_id, user_id, seq, role, search_text)"
        " VALUES (:s, :u, 1, 'user', 'Compare vector databases for retrieval') RETURNING id",
        s=world["session"],
        u=world["a"],
    )
    hits = db.execute(
        text(
            "SELECT count(*) FROM messages WHERE search_vector @@ plainto_tsquery('english', 'database')"
        )
    ).scalar()
    assert hits == 1
