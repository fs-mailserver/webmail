"""Folder / Thread / Message / Attachment — the local mail index (source of truth stays IMAP)."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    Computed,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    false,
    text,
    true,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.account import Account
from app.models.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin

# 'simple' config: no language-specific stemming (Croatian is not shipped with PostgreSQL),
# but works predictably across hr/en/de mail. Subject > sender > body weighting.
MESSAGE_SEARCH_VECTOR_SQL = (
    "setweight(to_tsvector('simple', coalesce(subject, '')), 'A') || "
    "setweight(to_tsvector('simple', coalesce(sender_name, '') || ' ' || coalesce(sender_email, '')), 'B') || "
    "setweight(to_tsvector('simple', left(coalesce(body_plain, ''), 200000)), 'C')"
)

SPECIAL_USE_VALUES = ("inbox", "sent", "drafts", "trash", "spam", "archive")


class Folder(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "folders"
    __table_args__ = (UniqueConstraint("account_id", "path", name="uq_folders_account_id_path"),)

    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    path: Mapped[str] = mapped_column(String(255), nullable=False)
    delimiter: Mapped[str] = mapped_column(String(8), nullable=False, default="/", server_default="/")
    special_use: Mapped[str | None] = mapped_column(String(32))
    uid_validity: Mapped[int | None] = mapped_column(BigInteger)
    uid_next: Mapped[int | None] = mapped_column(BigInteger)
    highest_modseq: Mapped[int | None] = mapped_column(BigInteger)
    unread_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    total_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    is_subscribed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=true())

    account: Mapped[Account] = relationship(back_populates="folders")


class Thread(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "threads"
    __table_args__ = (
        Index("ix_threads_account_id_last_message_at", "account_id", text("last_message_at DESC")),
        Index("ix_threads_account_id_is_unread", "account_id", "is_unread"),
        Index("ix_threads_account_id_normalized_subject", "account_id", "normalized_subject"),
    )

    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    first_message_id: Mapped[str | None] = mapped_column(String(998))
    subject: Mapped[str | None] = mapped_column(Text)
    normalized_subject: Mapped[str | None] = mapped_column(Text)
    snippet: Mapped[str | None] = mapped_column(Text)
    last_message_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    message_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    is_unread: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=true())
    is_starred: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=false())
    has_attachments: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=false())

    messages: Mapped[list["Message"]] = relationship(
        back_populates="thread", cascade="all, delete-orphan", passive_deletes=True, order_by="Message.date"
    )


class Message(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "messages"
    __table_args__ = (
        UniqueConstraint("folder_id", "uid", name="uq_messages_folder_id_uid"),
        Index("ix_messages_search_vector", "search_vector", postgresql_using="gin"),
        Index("ix_messages_thread_id_date", "thread_id", "date"),
        Index("ix_messages_account_id_message_id", "account_id", "message_id"),
        Index("ix_messages_folder_id_date", "folder_id", text("date DESC")),
        Index("ix_messages_sender_email", "sender_email"),
    )

    thread_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("threads.id", ondelete="CASCADE"), nullable=False)
    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    folder_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("folders.id", ondelete="CASCADE"), nullable=False)
    uid: Mapped[int] = mapped_column(BigInteger, nullable=False)

    message_id: Mapped[str] = mapped_column(String(998), nullable=False)
    in_reply_to: Mapped[str | None] = mapped_column(String(998))
    references_header: Mapped[str | None] = mapped_column(Text)

    sender_name: Mapped[str | None] = mapped_column(String(255))
    sender_email: Mapped[str] = mapped_column(String(320), nullable=False)
    to_recipients: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    cc_recipients: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    bcc_recipients: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    reply_to: Mapped[str | None] = mapped_column(String(320))

    subject: Mapped[str | None] = mapped_column(Text)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    snippet: Mapped[str | None] = mapped_column(Text)
    body_plain: Mapped[str | None] = mapped_column(Text)
    body_html: Mapped[str | None] = mapped_column(Text)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    has_attachments: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=false())
    eml_storage_path: Mapped[str | None] = mapped_column(String(512))

    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=false())
    is_starred: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=false())
    is_draft: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=false())
    flags: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))

    search_vector: Mapped[str | None] = mapped_column(TSVECTOR, Computed(MESSAGE_SEARCH_VECTOR_SQL, persisted=True))

    thread: Mapped[Thread] = relationship(back_populates="messages")
    attachments: Mapped[list["Attachment"]] = relationship(
        back_populates="message", cascade="all, delete-orphan", passive_deletes=True
    )


class Attachment(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "attachments"

    message_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str] = mapped_column(String(255), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    content_id: Mapped[str | None] = mapped_column(String(255))
    is_inline: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=false())
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    message: Mapped[Message] = relationship(back_populates="attachments")

