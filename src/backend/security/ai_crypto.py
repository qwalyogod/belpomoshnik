"""
Шифрование пользовательских API-ключей AI-провайдеров (промпт 3, пункт 3).

Отдельный от document_crypto мастер-ключ: BELPOMOSHNIK_AI_KEYS_MASTER_KEY.
Разделение ключей шифрования документов и ключей AI — намеренное: компрометация
одного не раскрывает другое. Шифрование — cryptography.Fernet.

Полный API-ключ хранится только в зашифрованном виде и расшифровывается
исключительно в момент запроса к провайдеру. На frontend полный ключ не уходит
никогда — только masked-форма (gsk_...abcd).
"""
from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

ENV_KEY = "BELPOMOSHNIK_AI_KEYS_MASTER_KEY"


class AICryptoError(RuntimeError):
    """Поднимается при попытке шифрования без настроенного мастер-ключа."""


@lru_cache(maxsize=1)
def _build_fernet() -> Optional[Fernet]:
    raw = os.getenv(ENV_KEY, "").strip()
    if not raw:
        return None
    try:
        return Fernet(raw.encode("ascii"))
    except (ValueError, TypeError) as exc:
        raise AICryptoError(
            f"{ENV_KEY} задан, но не является валидным Fernet-ключом: {exc}"
        ) from exc


def get_ai_crypto() -> Fernet:
    """Вернуть Fernet-экземпляр или поднять AICryptoError."""
    cipher = _build_fernet()
    if cipher is None:
        raise AICryptoError(
            f"Переменная {ENV_KEY} не задана. Сгенерируйте ключ: "
            "python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    return cipher


def is_ai_crypto_configured() -> bool:
    """True если мастер-ключ настроен (для health/диагностики и гейтинга UI)."""
    try:
        return _build_fernet() is not None
    except AICryptoError:
        return False


def reset_cache() -> None:
    """Сбросить кэш (для тестов с monkeypatch ключа)."""
    _build_fernet.cache_clear()


def encrypt_api_key(value: str) -> str:
    """Зашифровать API-ключ. Пустое значение запрещено."""
    value = (value or "").strip()
    if not value:
        raise ValueError("encrypt_api_key: empty input")
    cipher = get_ai_crypto()
    return cipher.encrypt(value.encode("utf-8")).decode("ascii")


def decrypt_api_key(token: str | None) -> str:
    """Расшифровать API-ключ. Битый токен → пустая строка (ключ непригоден)."""
    if not token:
        return ""
    cipher = get_ai_crypto()
    try:
        return cipher.decrypt(token.encode("ascii")).decode("utf-8")
    except InvalidToken:
        logger.warning("decrypt_api_key: invalid token, returning empty")
        return ""


def mask_api_key(value: str) -> str:
    """Безопасная для показа форма ключа: gsk_...abcd (середина не раскрывается)."""
    value = (value or "").strip()
    if not value:
        return ""
    tail = value[-4:]
    head = value[:4] if len(value) > 8 else ""
    return f"{head}...{tail}" if head else f"...{tail}"
