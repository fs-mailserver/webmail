"""Test configuration.

Unit tests run without any external service (DB/Redis are replaced by fakes).
Integration tests in test_db_integration.py run only when TEST_DATABASE_URL points to a
throwaway PostgreSQL database (e.g. inside `docker compose run --rm mail-backend test`).
"""

import os
import uuid
from collections.abc import AsyncIterator, Iterator
from datetime import datetime, timezone
from typing import Any

import pytest
from cryptography.fernet import Fernet

os.environ.setdefault("WEBMAIL_ENVIRONMENT", "test")
os.environ.setdefault("WEBMAIL_DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/webmail_test")
os.environ.setdefault("WEBMAIL_JWT_SECRET", "test-secret-" + "x" * 40)
os.environ.setdefault("MAILBOX_CREDENTIAL_ENCRYPTION_KEY", Fernet.generate_key().decode())
os.environ.setdefault("WEBMAIL_STORAGE_ROOT", "/tmp/webmail-test-storage")
os.environ.setdefault("WEBMAIL_CORS_ORIGINS", "https://webmail.example.com")

import bcrypt  # noqa: E402
import httpx  # noqa: E402

from app.core.db import get_db_session  # noqa: E402
from app.core.security import create_access_token  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Account, User  # noqa: E402

TEST_PASSWORD = "correct-horse-battery"
_TEST_HASH = bcrypt.hashpw(TEST_PASSWORD.encode(), bcrypt.gensalt(rounds=4)).decode()


def make_user(email: str = "user@example.com", role: str = "user", is_active: bool = True) -> User:
    return User(
        id=uuid.uuid4(),
        email=email,
        hashed_password=_TEST_HASH,
        full_name=None,
        role=role,
        is_active=is_active,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


class FakeSession:
    """Minimal in-memory stand-in for AsyncSession covering what the routes use."""

    def __init__(self) -> None:
        self.objects: dict[tuple[type, uuid.UUID], Any] = {}
        self.committed = 0

    def put(self, obj: Any) -> Any:
        self.objects[(type(obj), obj.id)] = obj
        return obj

    async def get(self, model: type, ident: uuid.UUID) -> Any:
        return self.objects.get((model, ident))

    async def scalar(self, stmt: Any) -> Any:
        # Supports `select(User).where(User.email == value)` used by login.
        criterion = stmt.whereclause
        value = criterion.right.value
        column = criterion.left.key
        model = stmt.column_descriptions[0]["entity"]
        for (kind, _), obj in self.objects.items():
            if kind is model and getattr(obj, column) == value:
                return obj
        return None

    async def scalars(self, stmt: Any) -> list[Any]:
        model = stmt.column_descriptions[0]["entity"]
        rows = [obj for (kind, _), obj in self.objects.items() if kind is model]
        criterion = stmt.whereclause
        if criterion is not None:
            rows = [obj for obj in rows if getattr(obj, criterion.left.key) == criterion.right.value]
        return rows

    def add(self, obj: Any) -> None:
        if getattr(obj, "id", None) is None:
            obj.id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        for attr in ("created_at", "updated_at"):
            if hasattr(type(obj), attr) and getattr(obj, attr, None) is None:
                setattr(obj, attr, now)
        if isinstance(obj, Account):
            obj.sync_status = obj.sync_status or "idle"
            obj.is_active = True if obj.is_active is None else obj.is_active
        if isinstance(obj, User):
            obj.is_active = True if obj.is_active is None else obj.is_active
        self.put(obj)

    async def delete(self, obj: Any) -> None:
        self.objects.pop((type(obj), obj.id), None)

    async def commit(self) -> None:
        self.committed += 1

    async def rollback(self) -> None:
        pass

    async def refresh(self, obj: Any) -> None:
        pass


@pytest.fixture
def fake_session() -> Iterator[FakeSession]:
    session = FakeSession()

    async def _override() -> AsyncIterator[FakeSession]:
        yield session

    app.dependency_overrides[get_db_session] = _override
    yield session
    app.dependency_overrides.pop(get_db_session, None)


@pytest.fixture
async def client() -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as http:
        yield http


def auth_headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user.id, user.role).token}"}

