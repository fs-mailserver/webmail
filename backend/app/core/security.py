"""Password hashing (bcrypt) and JWT access tokens."""

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import anyio
import bcrypt
import jwt

from app.core.config import get_settings

# bcrypt only uses the first 72 bytes; we reject longer inputs at the schema level.
BCRYPT_MAX_BYTES = 72
BCRYPT_ROUNDS = 12
TOKEN_TYPE_ACCESS = "access"

# Pre-computed hash used to equalise timing when the user does not exist.
_DUMMY_HASH = bcrypt.hashpw(b"timing-equaliser", bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode("ascii")


class InvalidTokenError(Exception):
    pass


@dataclass(frozen=True)
class AccessToken:
    token: str
    expires_in: int


def _hash_password_sync(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode("ascii")


def _verify_password_sync(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("ascii"))
    except ValueError:
        return False


async def hash_password(password: str) -> str:
    # bcrypt is CPU-bound (~250ms); never run it on the event loop.
    return await anyio.to_thread.run_sync(_hash_password_sync, password)


async def verify_password(password: str, hashed: str | None) -> bool:
    if not hashed:
        await anyio.to_thread.run_sync(_verify_password_sync, password, _DUMMY_HASH)
        return False
    return await anyio.to_thread.run_sync(_verify_password_sync, password, hashed)


def create_access_token(user_id: uuid.UUID, role: str, now: datetime | None = None) -> AccessToken:
    settings = get_settings()
    issued_at = now or datetime.now(timezone.utc)
    lifetime = timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": TOKEN_TYPE_ACCESS,
        "iat": int(issued_at.timestamp()),
        "exp": int((issued_at + lifetime).timestamp()),
        "jti": uuid.uuid4().hex,
    }
    token = jwt.encode(payload, settings.jwt_secret.get_secret_value(), algorithm=settings.jwt_algorithm)
    return AccessToken(token=token, expires_in=int(lifetime.total_seconds()))


def decode_access_token(token: str) -> uuid.UUID:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
            options={"require": ["sub", "exp", "iat", "type"]},
        )
    except jwt.PyJWTError as exc:
        raise InvalidTokenError("Invalid or expired token.") from exc
    if payload.get("type") != TOKEN_TYPE_ACCESS:
        raise InvalidTokenError("Wrong token type.")
    try:
        return uuid.UUID(str(payload["sub"]))
    except ValueError as exc:
        raise InvalidTokenError("Malformed token subject.") from exc

