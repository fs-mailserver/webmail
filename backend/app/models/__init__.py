"""Import every model here so Alembic autogenerate sees the full metadata."""

from app.models.account import Account, AccountSignature
from app.models.admin import BlocklistApplyLog, DeviceRegistration, SenderBlocklistRule
from app.models.base import Base
from app.models.mail import Attachment, Folder, Message, Thread
from app.models.user import User, UserRole

__all__ = [
    "Account",
    "AccountSignature",
    "Attachment",
    "Base",
    "BlocklistApplyLog",
    "DeviceRegistration",
    "Folder",
    "Message",
    "SenderBlocklistRule",
    "Thread",
    "User",
    "UserRole",
]

