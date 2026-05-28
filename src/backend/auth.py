"""
H2, H3, H4 — JWT-авторизация для «Белпомощник».

MVP: В `app_state.json` хранится упрощённый словарь пользователей.
Production: все пользователи в таблице `users`, пароли — bcrypt,
токены — JWT (HS256, exp 30 мин), refresh-токены в `refresh_tokens`.

Зависимости: passlib[bcrypt], python-jose[cryptography]
Установить: pip install passlib bcrypt python-jose
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

SECRET_KEY: str = os.getenv("BELPOMOSHNIK_SECRET_KEY", "change-me-in-production-use-256-bit-key")
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """H4 — Захешировать пароль с bcrypt."""
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """H4 — Проверить пароль против bcrypt-хэша."""
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """H3 — Создать JWT access-токен."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """H3 — Создать JWT refresh-токен (7 дней)."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
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
