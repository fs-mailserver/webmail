"""Real PostgreSQL integration tests (skipped unless TEST_DATABASE_URL is set).

Run inside the stack against a throwaway database, e.g.:
    docker compose exec webmail-db createdb -U webmail webmail_test
    docker compose run --rm -e TEST_DATABASE_URL=postgresql+asyncpg://webmail:...@webmail-db/webmail_test mail-backend test
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.models import Account, Base, Folder, Message, Thread, User

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
BACKEND_DIR = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(not TEST_DATABASE_URL, reason="TEST_DATABASE_URL not set")


def _alembic(*args: str) -> None:
    env = {**os.environ, "WEBMAIL_DATABASE_URL": TEST_DATABASE_URL or ""}
    subprocess.run([sys.executable, "-m", "alembic", *args], cwd=BACKEND_DIR, env=env, check=True)


@pytest.fixture(scope="module")
def migrated_db():  # type: ignore[no-untyped-def]
    _alembic("downgrade", "base")
    _alembic("upgrade", "head")
    yield
    _alembic("downgrade", "base")


async def test_schema_matches_models(migrated_db) -> None:  # type: ignore[no-untyped-def]
    engine = create_async_engine(TEST_DATABASE_URL or "")
    async with engine.connect() as conn:
        diff = await conn.run_sync(
            lambda sync_conn: compare_metadata(MigrationContext.configure(sync_conn, opts={"compare_type": True}), Base.metadata)
        )
    await engine.dispose()
    assert diff == [], diff


async def test_full_text_search_vector(migrated_db) -> None:  # type: ignore[no-untyped-def]
    from datetime import datetime, timezone

    engine = create_async_engine(TEST_DATABASE_URL or "")
    async with AsyncSession(engine, expire_on_commit=False) as session:
        user = User(email="fts@example.com", hashed_password="x")
        session.add(user)
        await session.flush()
        account = Account(user_id=user.id, email="fts@example.com", imap_host="h", smtp_host="h", encrypted_password="fernet:v1:x")
        session.add(account)
        await session.flush()
        folder = Folder(account_id=account.id, name="INBOX", path="INBOX", special_use="inbox")
        thread = Thread(account_id=account.id, subject="Ponuda", last_message_at=datetime.now(timezone.utc))
        session.add_all([folder, thread])
        await session.flush()
        session.add(
            Message(
                thread_id=thread.id,
                account_id=account.id,
                folder_id=folder.id,
                uid=1,
                message_id="<1@example.com>",
                sender_email="gost@example.com",
                subject="Rezervacija apartmana",
                date=datetime.now(timezone.utc),
                body_plain="Pozdrav, zanima me smještaj u kolovozu.",
            )
        )
        await session.commit()
        found = await session.scalar(
            select(Message.uid).where(Message.search_vector.op("@@")(text("plainto_tsquery('simple', 'kolovozu')")))
        )
        assert found == 1
    await engine.dispose()

