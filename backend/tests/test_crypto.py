import pytest
from cryptography.fernet import Fernet

from app.core.crypto import ENCRYPTED_VALUE_PREFIX, CredentialCipher, CredentialEncryptionError


def test_roundtrip_and_prefix() -> None:
    cipher = CredentialCipher(Fernet.generate_key().decode())
    encrypted = cipher.encrypt("s3cr3t-ćčž")
    assert encrypted.startswith(ENCRYPTED_VALUE_PREFIX)
    assert "s3cr3t" not in encrypted
    assert cipher.decrypt(encrypted) == "s3cr3t-ćčž"


def test_legacy_django_format_is_readable() -> None:
    key = Fernet.generate_key()
    legacy_value = "fernet:v1:" + Fernet(key).encrypt(b"legacy-pass").decode()
    assert CredentialCipher(key.decode()).decrypt(legacy_value) == "legacy-pass"


def test_wrong_key_raises_without_leaking() -> None:
    encrypted = CredentialCipher(Fernet.generate_key().decode()).encrypt("topsecret")
    with pytest.raises(CredentialEncryptionError) as exc:
        CredentialCipher(Fernet.generate_key().decode()).decrypt(encrypted)
    assert "topsecret" not in str(exc.value)


def test_plaintext_rejected() -> None:
    cipher = CredentialCipher(Fernet.generate_key().decode())
    with pytest.raises(CredentialEncryptionError):
        cipher.decrypt("plain-password")


def test_key_rotation() -> None:
    old_key, new_key = Fernet.generate_key().decode(), Fernet.generate_key().decode()
    stored = CredentialCipher(old_key).encrypt("rotate-me")
    rotating = CredentialCipher(f"{new_key},{old_key}")
    assert rotating.decrypt(stored) == "rotate-me"
    rotated = rotating.rotate(stored)
    assert CredentialCipher(new_key).decrypt(rotated) == "rotate-me"


@pytest.mark.parametrize("bad", ["", " , ", "not-a-fernet-key"])
def test_invalid_keys(bad: str) -> None:
    with pytest.raises(CredentialEncryptionError):
        CredentialCipher(bad)

