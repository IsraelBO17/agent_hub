"""Schema behaviour tests. Run against a disposable database:

    DATABASE_URL_DIRECT=postgresql://... uv run pytest

The migration is applied from scratch, each test runs in a rolled-back transaction.
"""

import os
import uuid

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

URL = os.environ.get("DATABASE_URL_DIRECT", "")


@pytest.fixture(scope="session")
def engine():
    if not URL:
        pytest.skip("DATABASE_URL_DIRECT not set")
    cfg = Config(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")
    return create_engine(URL.replace("postgresql://", "postgresql+psycopg://", 1))


@pytest.fixture
def db(engine):
    with engine.connect() as conn:
        tx = conn.begin()
        yield conn
        tx.rollback()


def insert(db, sql, **params):
    return db.execute(text(sql), params).scalar()


@pytest.fixture
def world(db):
    """Two users, one agent, one session for user A."""
    a = insert(db, "INSERT INTO users (google_sub, email, status) VALUES ('sub-a', 'A@x.dev', 'active') RETURNING id")
    b = insert(db, "INSERT INTO users (google_sub, email, status) VALUES ('sub-b', 'b@x.dev', 'active') RETURNING id")
    agent = insert(
        db,
        "INSERT INTO agents (slug, name, description, icon, color, runtime_type, runtime_arn)"
        " VALUES ('research-analyst', 'Research Analyst', 'd', 'search', 'blue', 'agentcore', 'arn:x') RETURNING id",
    )
    session = insert(db, "INSERT INTO sessions (user_id, agent_id) VALUES (:u, :a) RETURNING id", u=a, a=agent)
    return {"a": a, "b": b, "agent": agent, "session": session}


def add_message(db, w, seq, role="user", status="complete", client_id=None, user=None):
    return insert(
        db,
        "INSERT INTO messages (session_id, user_id, seq, role, status, client_message_id)"
        " VALUES (:s, :u, :seq, :role, :status, :cid) RETURNING id",
        s=w["session"], u=user or w["a"], seq=seq, role=role, status=status, cid=client_id,
    )


def fails(db, fn):
    sp = db.begin_nested()
    with pytest.raises(IntegrityError):
        fn()
    sp.rollback()


def test_email_unique_case_insensitive(db, world):
    fails(db, lambda: insert(db, "INSERT INTO users (email) VALUES ('a@X.dev') RETURNING id"))


def test_active_user_needs_google_sub(db):
    fails(db, lambda: insert(db, "INSERT INTO users (email, status) VALUES ('c@x.dev', 'active') RETURNING id"))


def test_agent_needs_runtime_target(db):
    fails(db, lambda: insert(
        db,
        "INSERT INTO agents (slug, name, description, icon, color, runtime_type)"
        " VALUES ('x', 'X', 'd', 'bot', 'red', 'agentcore') RETURNING id",
    ))


def test_one_streaming_reply_per_session(db, world):
    add_message(db, world, 1)
    add_message(db, world, 2, role="assistant", status="streaming")
    add_message(db, world, 3)
    fails(db, lambda: add_message(db, world, 4, role="assistant", status="streaming"))


def test_send_is_idempotent(db, world):
    cid = uuid.uuid4()
    add_message(db, world, 1, client_id=cid)
    fails(db, lambda: add_message(db, world, 2, client_id=cid))


def test_seq_unique_within_session(db, world):
    add_message(db, world, 1)
    fails(db, lambda: add_message(db, world, 1))


def test_user_message_is_always_complete(db, world):
    fails(db, lambda: add_message(db, world, 1, status="streaming"))


def test_cannot_attach_rows_to_another_users_session(db, world):
    fails(db, lambda: add_message(db, world, 1, user=world["b"]))


def test_approval_rules(db, world):
    msg = add_message(db, world, 1, role="assistant", status="streaming")
    tool = insert(
        db,
        "INSERT INTO tool_calls (message_id, session_id, user_id, tool_use_id, name, status)"
        " VALUES (:m, :s, :u, 't1', 'execute_transfer', 'awaiting_approval') RETURNING id",
        m=msg, s=world["session"], u=world["a"],
    )
    approval = insert(
        db,
        "INSERT INTO approval_requests (tool_call_id, message_id, session_id, user_id, agent_id, tool_name,"
        " arguments, expires_at) VALUES (:t, :m, :s, :u, :a, 'execute_transfer', '{}', now() + interval '10 min')"
        " RETURNING id",
        t=tool, m=msg, s=world["session"], u=world["a"], a=world["agent"],
    )
    # Cannot execute while pending, cannot be approved without a decision time.
    fails(db, lambda: db.execute(text("UPDATE approval_requests SET executed_at = now() WHERE id = :i"), {"i": approval}))
    fails(db, lambda: db.execute(text("UPDATE approval_requests SET status = 'approved' WHERE id = :i"), {"i": approval}))
    db.execute(text("UPDATE approval_requests SET status = 'denied', decided_at = now() WHERE id = :i"), {"i": approval})
    fails(db, lambda: db.execute(text("UPDATE approval_requests SET executed_at = now() WHERE id = :i"), {"i": approval}))


def test_deleting_a_session_cascades(db, world):
    msg = add_message(db, world, 1)
    insert(
        db,
        "INSERT INTO files (user_id, session_id, message_id, purpose, s3_key, filename, content_type)"
        " VALUES (:u, :s, :m, 'upload', 'k1', 'a.pdf', 'application/pdf') RETURNING id",
        u=world["a"], s=world["session"], m=msg,
    )
    art = insert(
        db,
        "INSERT INTO artifacts (session_id, user_id, artifact_key, type, title)"
        " VALUES (:s, :u, 'doc1', 'document', 'Brief') RETURNING id",
        s=world["session"], u=world["a"],
    )
    insert(
        db,
        "INSERT INTO artifact_versions (artifact_id, user_id, version, status, content)"
        " VALUES (:a, :u, 1, 'complete', '# Brief') RETURNING id",
        a=art, u=world["a"],
    )
    db.execute(text("DELETE FROM sessions WHERE id = :s"), {"s": world["session"]})
    for table in ("messages", "files", "artifacts", "artifact_versions"):
        assert db.execute(text(f"SELECT count(*) FROM {table}")).scalar() == 0, table


def test_agent_with_sessions_cannot_be_deleted(db, world):
    fails(db, lambda: db.execute(text("DELETE FROM agents WHERE id = :a"), {"a": world["agent"]}))


def test_message_search(db, world):
    insert(
        db,
        "INSERT INTO messages (session_id, user_id, seq, role, search_text)"
        " VALUES (:s, :u, 1, 'user', 'Compare vector databases for retrieval') RETURNING id",
        s=world["session"], u=world["a"],
    )
    hits = db.execute(
        text("SELECT count(*) FROM messages WHERE search_vector @@ plainto_tsquery('english', 'database')")
    ).scalar()
    assert hits == 1
