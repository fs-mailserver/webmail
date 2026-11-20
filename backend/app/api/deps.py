"""Shared FastAPI dependencies: DB session, current user, role guards."""

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db_session
from app.core.security import InvalidTokenError, decode_access_token
from app.models import Account, User

_bearer = HTTPBearer(auto_error=False, description="JWT access token from POST /api/v1/auth/login")

DbSession = Annotated[AsyncSession, Depends(get_db_session)]


def _unauthorized(detail: str = "Not authenticated.") -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail, headers={"WWW-Authenticate": "Bearer"})


async def get_current_user(
    session: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized()
    try:
        user_id = decode_access_token(credentials.credentials)
    except InvalidTokenError:
        raise _unauthorized("Invalid or expired token.") from None
    user = await session.get(User, user_id)
    if user is None or not user.is_active:
        raise _unauthorized("User is inactive or no longer exists.")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def require_admin(user: CurrentUser) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator role required.")
    return user


AdminUser = Annotated[User, Depends(require_admin)]


async def get_owned_account(account_id: uuid.UUID, session: DbSession, user: CurrentUser) -> Account:
    """Load an account the current user may access (owner, or any account for admins).

    Returns 404 (not 403) for foreign accounts so account IDs cannot be probed.
    """
    account = await session.get(Account, account_id)
    if account is None or (account.user_id != user.id and not user.is_admin):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found.")
    return account


OwnedAccount = Annotated[Account, Depends(get_owned_account)]

