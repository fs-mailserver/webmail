"""Management commands.

    python -m app.cli bootstrap-admin            # from WEBMAIL_BOOTSTRAP_ADMIN_EMAIL/PASSWORD, idempotent
    python -m app.cli create-user EMAIL [--admin] [--name NAME]   # password read from stdin/prompt
    python -m app.cli generate-fernet-key
    python -m app.cli rotate-credentials         # re-encrypt all mailbox passwords with the primary key
"""

import argparse
import asyncio
import getpass
import os
import sys

from cryptography.fernet import Fernet
from sqlalchemy import select

from app.core.crypto import get_credential_cipher
from app.core.db import dispose_engine, get_sessionmaker
from app.core.security import BCRYPT_MAX_BYTES, hash_password
from app.models import Account, User, UserRole

MIN_PASSWORD_LENGTH = 10


def _validate_password(password: str) -> None:
    if len(password) < MIN_PASSWORD_LENGTH or len(password.encode("utf-8")) > BCRYPT_MAX_BYTES:
        raise SystemExit(f"Password must be {MIN_PASSWORD_LENGTH}..{BCRYPT_MAX_BYTES} bytes long.")


async def _create_user(email: str, password: str, full_name: str | None, role: str, *, skip_existing: bool) -> None:
    email = email.strip().lower()
    _validate_password(password)
    async with get_sessionmaker()() as session:
        existing = await session.scalar(select(User).where(User.email == email))
        if existing is not None:
            if skip_existing:
                print(f"User {email} already exists, skipping.")
                return
            raise SystemExit(f"User {email} already exists.")
        session.add(User(email=email, hashed_password=await hash_password(password), full_name=full_name, role=role))
        await session.commit()
    print(f"Created {role} user {email}.")


async def _rotate_credentials() -> None:
    cipher = get_credential_cipher()
    async with get_sessionmaker()() as session:
        accounts = list(await session.scalars(select(Account)))
        for account in accounts:
            account.encrypted_password = cipher.rotate(account.encrypted_password)
        await session.commit()
    print(f"Re-encrypted {len(accounts)} account credential(s).")


async def _run(coro_factory) -> None:  # type: ignore[no-untyped-def]
    try:
        await coro_factory()
    finally:
        await dispose_engine()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("bootstrap-admin")
    create = sub.add_parser("create-user")
    create.add_argument("email")
    create.add_argument("--admin", action="store_true")
    create.add_argument("--name", default=None)
    sub.add_parser("generate-fernet-key")
    sub.add_parser("rotate-credentials")
    args = parser.parse_args(argv)

    if args.command == "generate-fernet-key":
        print(Fernet.generate_key().decode("ascii"))
    elif args.command == "bootstrap-admin":
        email = os.environ.get("WEBMAIL_BOOTSTRAP_ADMIN_EMAIL", "")
        password = os.environ.get("WEBMAIL_BOOTSTRAP_ADMIN_PASSWORD", "")
        if not email or not password:
            raise SystemExit("WEBMAIL_BOOTSTRAP_ADMIN_EMAIL and WEBMAIL_BOOTSTRAP_ADMIN_PASSWORD are required.")
        asyncio.run(_run(lambda: _create_user(email, password, "Administrator", UserRole.ADMIN.value, skip_existing=True)))
    elif args.command == "create-user":
        password = sys.stdin.readline().rstrip("\n") if not sys.stdin.isatty() else getpass.getpass("Password: ")
        role = UserRole.ADMIN.value if args.admin else UserRole.USER.value
        asyncio.run(_run(lambda: _create_user(args.email, password, args.name, role, skip_existing=False)))
    elif args.command == "rotate-credentials":
        asyncio.run(_run(_rotate_credentials))


if __name__ == "__main__":
    main()

