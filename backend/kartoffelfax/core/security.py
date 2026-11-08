"""Symmetric encryption for credentials stored in the database (Fernet)."""
from __future__ import annotations

import os

from cryptography.fernet import Fernet, InvalidToken

from kartoffelfax.config import settings

_KEY_FILENAME = "secret.key"


def _load_key() -> bytes:
    if settings.secret_key:
        return settings.secret_key.encode()

    key_path = settings.data_dir / _KEY_FILENAME
    if key_path.is_file():
        return key_path.read_bytes().strip()

    key = Fernet.generate_key()
    key_path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(key_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as fh:
        fh.write(key)
    return key


def encrypt(plaintext: str) -> str:
    return Fernet(_load_key()).encrypt(plaintext.encode()).decode()


def decrypt(token: str) -> str:
    try:
        return Fernet(_load_key()).decrypt(token.encode()).decode()
    except InvalidToken as exc:
        raise ValueError("Stored credential cannot be decrypted with the current secret key") from exc
