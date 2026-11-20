"""Admin-only user management (multi-tenant: admins assign mailboxes to users)."""

import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.api.deps import AdminUser, DbSession
from app.core.security import hash_password
from app.models import User
from app.schemas.auth import UserCreate, UserRead, UserUpdate
from app.schemas.common import ErrorResponse

router = APIRouter(prefix="/users", tags=["users"])


async def _get_user_or_404(session: DbSession, user_id: uuid.UUID) -> User:
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return user


@router.get("", response_model=list[UserRead])
async def list_users(_: AdminUser, session: DbSession) -> list[User]:
    result = await session.scalars(select(User).order_by(User.email))
    return list(result)


@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_409_CONFLICT: {"model": ErrorResponse}},
)
async def create_user(payload: UserCreate, _: AdminUser, session: DbSession) -> User:
    user = User(
        email=payload.email,
        hashed_password=await hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role,
    )
    session.add(user)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A user with this email already exists.") from None
    await session.refresh(user)
    return user


@router.patch(
    "/{user_id}",
    response_model=UserRead,
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorResponse}, status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse}},
)
async def update_user(user_id: uuid.UUID, payload: UserUpdate, admin: AdminUser, session: DbSession) -> User:
    user = await _get_user_or_404(session, user_id)
    changes = payload.model_dump(exclude_unset=True)
    if user.id == admin.id and (changes.get("role") == "user" or changes.get("is_active") is False):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot demote or deactivate yourself.")
    password = changes.pop("password", None)
    if password is not None:
        user.hashed_password = await hash_password(password)
    for field, value in changes.items():
        if value is not None or field == "full_name":
            setattr(user, field, value)
    await session.commit()
    await session.refresh(user)
    return user


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorResponse}, status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse}},
)
async def delete_user(user_id: uuid.UUID, admin: AdminUser, session: DbSession) -> None:
    if user_id == admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot delete yourself.")
    user = await _get_user_or_404(session, user_id)
    await session.delete(user)
    await session.commit()

