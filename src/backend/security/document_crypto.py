"""
Шифрование чувствительных полей и сканов личных документов (промпт 1).

Использует cryptography.Fernet (AES-128-CBC + HMAC-SHA256). Ключ берётся из
переменной окружения BELPOMOSHNIK_DOCUMENT_MASTER_KEY (32-байтный urlsafe-base64).

В тестах допускается monkeypatch ключа через env. В production отсутствие ключа
вызывает DocumentCryptoError при первой же операции (не при импорте — чтобы
старые миграции и read-only запуски не падали).
"""
from __future__ import annotations

import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

ENV_KEY = "BELPOMOSHNIK_DOCUMENT_MASTER_KEY"
# Префикс — лёгкая страховка от случайного смешения plain/encrypted строк.
# Для строковых полей формат: "enc1:<urlsafe-fernet>".
FIELD_PREFIX = "enc1:"


class DocumentCryptoError(RuntimeError):
    """Поднимается при попытке шифрования без настроенного ключа."""


@lru_cache(maxsize=1)
def _build_fernet() -> Optional[Fernet]:
    raw = os.getenv(ENV_KEY, "").strip()
    if not raw:
        return None
    try:
        return Fernet(raw.encode("ascii"))
    except (ValueError, TypeError) as exc:
        # Битый ключ — это конфигурационная ошибка, говорим явно.
        raise DocumentCryptoError(
            f"{ENV_KEY} задан, но не является валидным Fernet-ключом: {exc}"
        ) from exc


def get_document_crypto() -> Fernet:
    """Вернуть Fernet-экземпляр или поднять DocumentCryptoError."""
    cipher = _build_fernet()
    if cipher is None:
        raise DocumentCryptoError(
            f"Переменная {ENV_KEY} не задана. Сгенерируйте ключ: "
            "python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    return cipher


def is_crypto_configured() -> bool:
    """True если ключ настроен (используется для health/диагностики)."""
    try:
        return _build_fernet() is not None
    except DocumentCryptoError:
        return False


def reset_cache() -> None:
    """Сбросить кэш (для тестов с monkeypatch ключа)."""
    _build_fernet.cache_clear()


# ─────────────────────────────────────────────────────────────────────────────
# Поля (строки)
# ─────────────────────────────────────────────────────────────────────────────

def encrypt_field(value: str | None) -> str:
    """Зашифровать строку. Пустая строка/None → пустая строка (не шифруем)."""
    if not value:
        return ""
    cipher = get_document_crypto()
    token = cipher.encrypt(value.encode("utf-8")).decode("ascii")
    return FIELD_PREFIX + token


def decrypt_field(value: str | None) -> str:
    """Расшифровать строку. Не зашифрованное (без префикса) возвращаем как есть
    — это backward-compat с уже сохранёнными plain-полями."""
    if not value:
        return ""
    if not value.startswith(FIELD_PREFIX):
        return value
    cipher = get_document_crypto()
    try:
        return cipher.decrypt(value[len(FIELD_PREFIX):].encode("ascii")).decode("utf-8")
    except InvalidToken:
        logger.warning("decrypt_field: invalid token, returning empty")
        return ""


# ─────────────────────────────────────────────────────────────────────────────
# Файлы
# ─────────────────────────────────────────────────────────────────────────────

def encrypt_file(plaintext: bytes) -> bytes:
    """Зашифровать содержимое файла. Возвращает blob для сохранения на диск."""
    if not plaintext:
        raise ValueError("encrypt_file: empty input")
    cipher = get_document_crypto()
    return cipher.encrypt(plaintext)


def decrypt_file(ciphertext: bytes) -> bytes:
    """Расшифровать содержимое файла."""
    if not ciphertext:
        raise ValueError("decrypt_file: empty input")
    cipher = get_document_crypto()
    try:
        return cipher.decrypt(ciphertext)
    except InvalidToken as exc:
        raise DocumentCryptoError("Не удалось расшифровать файл (неверный ключ?)") from exc


def encrypt_file_to_path(plaintext: bytes, target: Path) -> int:
    """Зашифровать и записать в `target`. Возвращает количество байт исходного файла."""
    target.parent.mkdir(parents=True, exist_ok=True)
    blob = encrypt_file(plaintext)
    target.write_bytes(blob)
    return len(plaintext)


def decrypt_file_from_path(source: Path) -> bytes:
    """Прочитать и расшифровать файл по пути."""
    if not source.exists() or not source.is_file():
        raise FileNotFoundError(str(source))
    return decrypt_file(source.read_bytes())
