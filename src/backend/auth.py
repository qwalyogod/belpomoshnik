"""
H2, H3, H4 — JWT-авторизация для «Белпомощник».

MVP: В `app_state.json` хранится упрощённый словарь пользователей.
Production: все пользователи в таблице `users`, пароли — bcrypt,
токены — JWT (HS256, exp 30 мин), refresh-токены в `refresh_tokens`.

Зависимости: bcrypt, python-jose[cryptography]
Установить: pip install bcrypt python-jose

Примечание: используем bcrypt напрямую (без passlib) — passlib 1.7.4
не поддерживает bcrypt 5.x (баг detect_wrap_bug) и не обновляется с 2020.
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

SECRET_KEY: str = os.getenv("BELPOMOSHNIK_SECRET_KEY", "change-me-in-production-use-256-bit-key")
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# bcrypt принимает максимум 72 байта; длинные пароли усекаются (стандартное поведение).
_BCRYPT_MAX_BYTES = 72


def hash_password(plain: str) -> str:
    """H4 — Захешировать пароль с bcrypt."""
    pwd = plain.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    return bcrypt.hashpw(pwd, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """H4 — Проверить пароль против bcrypt-хэша."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8")[:_BCRYPT_MAX_BYTES], hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """H3 — Создать JWT access-токен."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access", "jti": uuid.uuid4().hex})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """H3 — Создать JWT refresh-токен (7 дней)."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh", "jti": uuid.uuid4().hex})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """H3 — Декодировать и проверить JWT. Raises JWTError при невалидном токене."""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def get_token_payload(token: str) -> dict | None:
    """Безопасное декодирование — возвращает None при ошибке."""
    try:
        return decode_token(token)
    except JWTError:
        return None
