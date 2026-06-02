"""
AES-128-CBC (Fernet) шифрование файлов-сканов документов.

Ключ выводится из SECRET_KEY через PBKDF2-HMAC-SHA256 — один ключ
на всё приложение, хранится только в памяти.

Зависимость: cryptography (через python-jose[cryptography]).

Использование:
    from services.file_crypto import encrypt_bytes, decrypt_bytes, ENCRYPTED_SUFFIX

    # Запись
    destination = uploads_dir / f"{ts}-{name}{ENCRYPTED_SUFFIX}"
    destination.write_bytes(encrypt_bytes(raw_bytes))

    # Чтение
    raw = decrypt_bytes(destination.read_bytes())
"""
from __future__ import annotations

import base64
import hashlib
import os

ENCRYPTED_SUFFIX = ".enc"

_SECRET = os.getenv("BELPOMOSHNIK_SECRET_KEY", "change-me-in-production-use-256-bit-key")
_SALT = b"belpomoshnik-file-v1"


def _fernet_key() -> bytes:
    raw = hashlib.pbkdf2_hmac("sha256", _SECRET.encode(), _SALT, iterations=100_000, dklen=32)
    return base64.urlsafe_b64encode(raw)


def _get_fernet():
    try:
        from cryptography.fernet import Fernet
        return Fernet(_fernet_key())
    except ImportError as exc:
        raise RuntimeError(
            "Установите пакет cryptography: pip install cryptography"
        ) from exc


def encrypt_bytes(data: bytes) -> bytes:
    return _get_fernet().encrypt(data)


def decrypt_bytes(data: bytes) -> bytes:
    return _get_fernet().decrypt(data)


def is_encrypted_path(path: str) -> bool:
    return str(path).endswith(ENCRYPTED_SUFFIX)
