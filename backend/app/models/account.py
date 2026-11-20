import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, false, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.mail import Folder
    from app.models.user import User


class Account(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A mailbox (IMAP/SMTP account) assigned to exactly one user."""

    __tablename__ = "accounts"
    __table_args__ = (
        UniqueConstraint("user_id", "email", name="uq_accounts_user_id_email"),
        CheckConstraint("sync_status IN ('idle', 'syncing', 'error')", name="sync_status_valid"),
        CheckConstraint("imap_port BETWEEN 1 AND 65535 AND smtp_port BETWEEN 1 AND 65535", name="ports_valid"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255))
    color_code: Mapped[str] = mapped_column(String(16), nullable=False, default="#3b82f6", server_default="#3b82f6")

    imap_host: Mapped[str] = mapped_column(String(255), nullable=False)
    imap_port: Mapped[int] = mapped_column(Integer, nullable=False, default=993, server_default="993")
    imap_use_ssl: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=true())
    smtp_host: Mapped[str] = mapped_column(String(255), nullable=False)
    smtp_port: Mapped[int] = mapped_column(Integer, nullable=False, default=587, server_default="587")
    smtp_use_tls: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=true())

    # Always "fernet:v1:<token>" — never plaintext. See app.core.crypto.
    encrypted_password: Mapped[str] = mapped_column(Text, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=true())
    sync_status: Mapped[str] = mapped_column(String(32), nullable=False, default="idle", server_default="idle")
    sync_error: Mapped[str | None] = mapped_column(Text)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="accounts")
    folders: Mapped[list["Folder"]] = relationship(back_populates="account", cascade="all, delete-orphan", passive_deletes=True)
    signatures: Mapped[list["AccountSignature"]] = relationship(
        back_populates="account", cascade="all, delete-orphan", passive_deletes=True
    )

    def __repr__(self) -> str:  # never include the encrypted password
        return f"<Account {self.email}>"


class AccountSignature(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "account_signatures"

    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    content_html: Mapped[str] = mapped_column(Text, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=false())

    account: Mapped["Account"] = relationship(back_populates="signatures")

