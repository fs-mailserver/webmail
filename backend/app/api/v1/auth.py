from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.core.security import create_access_token, hash_password, verify_password
from app.models import User
from app.schemas.auth import LoginRequest, PasswordChangeRequest, TokenResponse, UserRead
from app.schemas.common import ErrorResponse

router = APIRouter(prefix="/auth", tags=["auth"])

INVALID_CREDENTIALS = "Invalid email or password."


@router.post(
    "/login",
    response_model=TokenResponse,
    responses={status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse}},
)
async def login(payload: LoginRequest, session: DbSession) -> TokenResponse:
    user = await session.scalar(select(User).where(User.email == payload.email))
    password_ok = await verify_password(payload.password, user.hashed_password if user else None)
    if user is None or not password_ok or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_CREDENTIALS,
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(user.id, user.role)
    return TokenResponse(access_token=token.token, expires_in=token.expires_in)


@router.get("/me", response_model=UserRead, responses={status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse}})
async def me(user: CurrentUser) -> User:
    return user


@router.post(
    "/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse}},
)
async def change_password(payload: PasswordChangeRequest, user: CurrentUser, session: DbSession) -> None:
    if not await verify_password(payload.current_password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect.")
    user.hashed_password = await hash_password(payload.new_password)
    await session.commit()

