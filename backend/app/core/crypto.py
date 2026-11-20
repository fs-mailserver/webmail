"""Fernet encryption for stored IMAP/SMTP credentials.

Values are stored as ``fernet:v1:<token>`` (same format the legacy Django mailadmin used,
so existing keys and exported values stay compatible). ``MAILBOX_CREDENTIAL_ENCRYPTION_KEY``
may contain several comma-separated keys: the first encrypts, all of them decrypt.
"""

from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken, MultiFernet

from app.core.config import get_settings

ENCRYPTED_VALUE_PREFIX = "fernet:v1:"


class CredentialEncryptionError(ValueError):
    """Raised when a credential cannot be encrypted/decrypted. Never contains the secret."""


class CredentialCipher:
    def __init__(self, keys: str) -> None:
        key_list = [key.strip() for key in keys.split(",") if key.strip()]
        if not key_list:
            raise CredentialEncryptionError("MAILBOX_CREDENTIAL_ENCRYPTION_KEY is required.")
        try:
            self._fernet = MultiFernet([Fernet(key.encode("ascii")) for key in key_list])
        except (TypeError, ValueError) as exc:
            raise CredentialEncryptionError("MAILBOX_CREDENTIAL_ENCRYPTION_KEY must contain valid Fernet keys.") from exc

    @staticmethod
    def is_encrypted(value: str | None) -> bool:
        return isinstance(value, str) and value.startswith(ENCRYPTED_VALUE_PREFIX)

    def encrypt(self, plaintext: str) -> str:
        token = self._fernet.encrypt(plaintext.encode("utf-8")).decode("ascii")
        return f"{ENCRYPTED_VALUE_PREFIX}{token}"

    def decrypt(self, value: str, label: str = "Credential") -> str:
        if not self.is_encrypted(value):
            raise CredentialEncryptionError(f"{label} is not encrypted.")
        token = value.removeprefix(ENCRYPTED_VALUE_PREFIX)
        try:
            return self._fernet.decrypt(token.encode("ascii")).decode("utf-8")
        except (InvalidToken, UnicodeDecodeError) as exc:
            raise CredentialEncryptionError(f"{label} could not be decrypted.") from exc

    def rotate(self, value: str) -> str:
        """Re-encrypt a stored value with the primary (first) key."""
        if not self.is_encrypted(value):
            raise CredentialEncryptionError("Credential is not encrypted.")
        token = value.removeprefix(ENCRYPTED_VALUE_PREFIX)
        try:
            rotated = self._fernet.rotate(token.encode("ascii")).decode("ascii")
        except InvalidToken as exc:
            raise CredentialEncryptionError("Credential could not be rotated.") from exc
        return f"{ENCRYPTED_VALUE_PREFIX}{rotated}"


@lru_cache
def get_credential_cipher() -> CredentialCipher:
    return CredentialCipher(get_settings().mailbox_credential_encryption_key.get_secret_value())


def encrypt_mailbox_password(plaintext: str) -> str:
    return get_credential_cipher().encrypt(plaintext)


def decrypt_mailbox_password(value: str) -> str:
    return get_credential_cipher().decrypt(value, label="Mailbox password")

