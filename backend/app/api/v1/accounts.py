"""Mailbox accounts. Admins assign/configure mailboxes; users only see their own and may tweak cosmetics."""

import uuid

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.api.deps import AdminUser, CurrentUser, DbSession, OwnedAccount
from app.core.config import get_settings
from app.core.crypto import encrypt_mailbox_password
from app.models import Account, User
from app.schemas.account import AccountCreate, AccountRead, AccountUpdate
from app.schemas.common import ErrorResponse

router = APIRouter(prefix="/accounts", tags=["accounts"])

USER_EDITABLE_FIELDS = frozenset({"display_name", "color_code"})
NULLABLE_FIELDS = frozenset({"display_name"})


@router.get("", response_model=list[AccountRead])
async def list_accounts(
    user: CurrentUser,
    session: DbSession,
    user_id: uuid.UUID | None = Query(default=None, description="Admin only: list accounts of another user."),
    all_users: bool = Query(default=False, description="Admin only: list accounts of every user."),
) -> list[Account]:
    stmt = select(Account).order_by(Account.email)
    if user.is_admin and all_users:
        pass
    elif user.is_admin and user_id is not None:
        stmt = stmt.where(Account.user_id == user_id)
    else:
        stmt = stmt.where(Account.user_id == user.id)
    return list(await session.scalars(stmt))


@router.post(
    "",
    response_model=AccountRead,
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorResponse}, status.HTTP_409_CONFLICT: {"model": ErrorResponse}},
)
async def create_account(payload: AccountCreate, admin: AdminUser, session: DbSession) -> Account:
    settings = get_settings()
    owner_id = payload.user_id or admin.id
    if await session.get(User, owner_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Owner user not found.")
    account = Account(
        user_id=owner_id,
        email=payload.email,
        display_name=payload.display_name,
        color_code=payload.color_code,
        imap_host=payload.imap_host or settings.mail_imap_host,
        imap_port=payload.imap_port,
        imap_use_ssl=payload.imap_use_ssl,
        smtp_host=payload.smtp_host or settings.mail_smtp_host,
        smtp_port=payload.smtp_port,
        smtp_use_tls=payload.smtp_use_tls,
        encrypted_password=encrypt_mailbox_password(payload.password),
    )
    session.add(account)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This user already has this mailbox.") from None
    await session.refresh(account)
    return account


@router.get("/{account_id}", response_model=AccountRead, responses={status.HTTP_404_NOT_FOUND: {"model": ErrorResponse}})
async def get_account(account: OwnedAccount) -> Account:
    return account


@router.patch(
    "/{account_id}",
    response_model=AccountRead,
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorResponse}, status.HTTP_403_FORBIDDEN: {"model": ErrorResponse}},
)
async def update_account(payload: AccountUpdate, account: OwnedAccount, user: CurrentUser, session: DbSession) -> Account:
    changes = payload.model_dump(exclude_unset=True)
    if not user.is_admin and not set(changes) <= USER_EDITABLE_FIELDS:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only display name and color can be changed.")
    password = changes.pop("password", None)
    if password is not None:
        account.encrypted_password = encrypt_mailbox_password(password)
    for field, value in changes.items():
        if value is None and field not in NULLABLE_FIELDS:
            continue
        setattr(account, field, value)
    await session.commit()
    await session.refresh(account)
    return account


@router.delete(
    "/{account_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorResponse}},
)
async def delete_account(account: OwnedAccount, _: AdminUser, session: DbSession) -> None:
    await session.delete(account)
    await session.commit()

