"""Admin-side tables: Postfix sender blocklist and FCM device registrations."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, String, Text, UniqueConstraint, true
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin


class SenderBlocklistRule(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "sender_blocklist_rules"
    __table_args__ = (
        UniqueConstraint("kind", "value", name="uq_sender_blocklist_rules_kind_value"),
        CheckConstraint("kind IN ('sender_email', 'sender_domain')", name="kind_valid"),
    )

    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    value: Mapped[str] = mapped_column(String(255), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=true())
    note: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))


class BlocklistApplyLog(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "blocklist_apply_logs"
    __table_args__ = (CheckConstraint("status IN ('success', 'error')", name="status_valid"),)

    status: Mapped[str] = mapped_column(String(16), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    applied_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))


class DeviceRegistration(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "device_registrations"
    __table_args__ = (
        Index("ix_device_registrations_account_email_enabled", "account_email", "enabled"),
        CheckConstraint("platform IN ('android', 'ios', 'web', 'unknown')", name="platform_valid"),
    )

    account_email: Mapped[str] = mapped_column(String(255), nullable=False)
    fcm_token: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    platform: Mapped[str] = mapped_column(String(32), nullable=False, default="unknown", server_default="unknown")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=true())
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
