import uuid
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.core.security import (
    InvalidTokenError,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


async def test_password_hash_and_verify() -> None:
    hashed = await hash_password("a-long-password")
    assert hashed.startswith("$2")
    assert await verify_password("a-long-password", hashed)
    assert not await verify_password("wrong-password", hashed)
    assert not await verify_password("anything", None)
    assert not await verify_password("anything", "not-a-hash")


def test_token_roundtrip() -> None:
    user_id = uuid.uuid4()
    token = create_access_token(user_id, "admin")
    assert decode_access_token(token.token) == user_id
    assert token.expires_in == get_settings().access_token_expire_minutes * 60


def test_expired_token_rejected() -> None:
    issued = datetime.now(timezone.utc) - timedelta(days=60)
    token = create_access_token(uuid.uuid4(), "user", now=issued)
    with pytest.raises(InvalidTokenError):
        decode_access_token(token.token)


def test_tampered_and_foreign_tokens_rejected() -> None:
    token = create_access_token(uuid.uuid4(), "user").token
    with pytest.raises(InvalidTokenError):
        decode_access_token(token[:-2] + ("AA" if token[-2:] != "AA" else "BB"))
    foreign = jwt.encode({"sub": str(uuid.uuid4()), "exp": 9999999999, "iat": 1, "type": "access"}, "x" * 40, algorithm="HS256")
    with pytest.raises(InvalidTokenError):
        decode_access_token(foreign)


def test_wrong_token_type_rejected() -> None:
    secret = get_settings().jwt_secret.get_secret_value()
    refresh = jwt.encode({"sub": str(uuid.uuid4()), "exp": 9999999999, "iat": 1, "type": "refresh"}, secret, algorithm="HS256")
    with pytest.raises(InvalidTokenError):
        decode_access_token(refresh)


def test_settings_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WEBMAIL_DATABASE_URL", "postgresql://u:p@db/webmail")
    settings = Settings()  # type: ignore[call-arg]
    assert settings.database_url == "postgresql+asyncpg://u:p@db/webmail"

    monkeypatch.setenv("WEBMAIL_JWT_SECRET", "short")
    with pytest.raises(ValidationError):
        Settings()  # type: ignore[call-arg]

    monkeypatch.setenv("WEBMAIL_JWT_SECRET", "y" * 40)
    monkeypatch.setenv("WEBMAIL_DATABASE_URL", "mysql://nope")
    with pytest.raises(ValidationError):
        Settings()  # type: ignore[call-arg]


def test_cors_origins_parsing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WEBMAIL_CORS_ORIGINS", " https://a.example.com/ ,https://b.example.com,, ")
    assert Settings().cors_origins == ["https://a.example.com", "https://b.example.com"]  # type: ignore[call-arg]

