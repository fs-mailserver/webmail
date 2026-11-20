import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.schemas.auth import NormalizedEmail

HexColor = Annotated[str, StringConstraints(pattern=r"^#[0-9a-fA-F]{6}$")]
Hostname = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255, pattern=r"^[A-Za-z0-9.\-]+$")]
Port = Annotated[int, Field(ge=1, le=65535)]
MailboxPassword = Annotated[str, StringConstraints(min_length=1, max_length=1024)]
DisplayName = Annotated[str, StringConstraints(strip_whitespace=True, max_length=255)]


class AccountBase(BaseModel):
    display_name: DisplayName | None = None
    color_code: HexColor = "#3b82f6"


class AccountCreate(AccountBase):
    """Create a mailbox account. Server defaults (MAIL_IMAP_HOST/MAIL_SMTP_HOST) are used when hosts are omitted."""

    email: NormalizedEmail
    password: MailboxPassword = Field(description="IMAP/SMTP password. Stored Fernet-encrypted, never returned.")
    user_id: uuid.UUID | None = Field(default=None, description="Owner (admin only). Defaults to the current user.")
    imap_host: Hostname | None = None
    imap_port: Port = 993
    imap_use_ssl: bool = True
    smtp_host: Hostname | None = None
    smtp_port: Port = 587
    smtp_use_tls: bool = True


class AccountUpdate(BaseModel):
    display_name: DisplayName | None = None
    color_code: HexColor | None = None
    password: MailboxPassword | None = Field(default=None, description="New IMAP/SMTP password (re-encrypted).")
    imap_host: Hostname | None = None
    imap_port: Port | None = None
    imap_use_ssl: bool | None = None
    smtp_host: Hostname | None = None
    smtp_port: Port | None = None
    smtp_use_tls: bool | None = None
    is_active: bool | None = None


class AccountRead(AccountBase):
    """Public account representation — intentionally has no password field."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    email: str
    color_code: str
    imap_host: str
    imap_port: int
    imap_use_ssl: bool
    smtp_host: str
    smtp_port: int
    smtp_use_tls: bool
    is_active: bool
    sync_status: Literal["idle", "syncing", "error"]
    last_synced_at: datetime | None
    created_at: datetime

