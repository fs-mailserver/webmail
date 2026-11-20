import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, Field, StringConstraints

from app.core.security import BCRYPT_MAX_BYTES


def _lower(value: str) -> str:
    return value.strip().lower()


def _password_bytes_limit(value: str) -> str:
    if len(value.encode("utf-8")) > BCRYPT_MAX_BYTES:
        raise ValueError(f"Password must be at most {BCRYPT_MAX_BYTES} bytes.")
    return value


NormalizedEmail = Annotated[EmailStr, AfterValidator(_lower)]
NewPassword = Annotated[str, StringConstraints(min_length=10, max_length=BCRYPT_MAX_BYTES), AfterValidator(_password_bytes_limit)]
UserRoleLiteral = Literal["admin", "user"]


class LoginRequest(BaseModel):
    email: NormalizedEmail
    password: Annotated[str, StringConstraints(min_length=1, max_length=256)]


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int = Field(description="Token lifetime in seconds.")


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str | None
    role: UserRoleLiteral
    is_active: bool
    created_at: datetime


class UserCreate(BaseModel):
    email: NormalizedEmail
    password: NewPassword
    full_name: Annotated[str, StringConstraints(strip_whitespace=True, max_length=255)] | None = None
    role: UserRoleLiteral = "user"


class UserUpdate(BaseModel):
    full_name: Annotated[str, StringConstraints(strip_whitespace=True, max_length=255)] | None = None
    role: UserRoleLiteral | None = None
    is_active: bool | None = None
    password: NewPassword | None = None


class PasswordChangeRequest(BaseModel):
    current_password: Annotated[str, StringConstraints(min_length=1, max_length=256)]
    new_password: NewPassword

