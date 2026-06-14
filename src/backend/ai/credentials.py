"""Резолвер AI-провайдерских ключей (промпт 3, п.3).

Два режима:
- `resolve_ai` — user-ключ → серверный `GROQ_API_KEY` → local fallback
  (используется редакторским AI, где серверный ключ допустим).
- `resolve_user_ai` — ТОЛЬКО личный ключ пользователя, без серверного fallback.
  Используется чатом помощника-гражданина: по требованию каждый пользователь
  работает на своём ключе, без ключа — инструкция как его получить.

Полный ключ расшифровывается только здесь и только перед запросом к провайдеру.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

import httpx
from sqlalchemy.orm import Session

from backend.models import User, UserAIProviderCredential
from backend.security.ai_crypto import decrypt_api_key, is_ai_crypto_configured

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_GROQ_MODEL = "llama-3.1-8b-instant"

MODE_SERVER = "server_key"
MODE_USER = "user_key"
MODE_FALLBACK = "local_fallback"
MODE_NEEDS_KEY = "needs_key"

# Инструкция, которую помощник выдаёт пользователю без личного Groq-ключа.
NEEDS_KEY_MESSAGE = (
    "Чтобы AI-помощник заработал, нужен ваш личный ключ Groq API:\n\n"
    "1. Откройте https://console.groq.com (groq.com) и войдите или зарегистрируйтесь.\n"
    "2. В разделе «API Keys» нажмите «Create API Key» и скопируйте ключ (gsk_...).\n"
    "3. Откройте «Настройки» → «AI-помощник» и вставьте ключ, затем сохраните.\n\n"
    "После этого вернитесь в чат — помощник будет отвечать на ваши вопросы."
)


@dataclass
class ResolvedAI:
    api_key: str
    model: str
    mode: str  # server_key | user_key | local_fallback | needs_key
    provider: str = "groq"

    @property
    def has_key(self) -> bool:
        return bool(self.api_key)


def _server_key() -> str:
    return os.getenv("GROQ_API_KEY", "").strip()


def _server_model() -> str:
    return os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL).strip() or DEFAULT_GROQ_MODEL


def _user_credential(db: Session, user: Optional[User]) -> Optional[UserAIProviderCredential]:
    if user is None or not is_ai_crypto_configured():
        return None
    return (
        db.query(UserAIProviderCredential)
        .filter(
            UserAIProviderCredential.user_id == user.id,
            UserAIProviderCredential.provider == "groq",
        )
        .first()
    )


def _user_key(db: Session, user: Optional[User]) -> tuple[str, str]:
    """Вернуть (api_key, model) личного ключа пользователя или ('','')."""
    cred = _user_credential(db, user)
    if cred is not None and cred.is_enabled and cred.encrypted_api_key:
        key = decrypt_api_key(cred.encrypted_api_key)
        if key:
            return key, (cred.model or _server_model())
    return "", ""


def resolve_user_ai(db: Session, user: Optional[User]) -> ResolvedAI:
    """ТОЛЬКО личный ключ. Нет ключа → mode='needs_key' (без серверного fallback)."""
    key, model = _user_key(db, user)
    if key:
        return ResolvedAI(api_key=key, model=model, mode=MODE_USER)
    return ResolvedAI(api_key="", model=_server_model(), mode=MODE_NEEDS_KEY)


def resolve_ai(db: Session, user: Optional[User]) -> ResolvedAI:
    """user-ключ → серверный ключ → local fallback (для редакторского AI)."""
    key, model = _user_key(db, user)
    if key:
        return ResolvedAI(api_key=key, model=model, mode=MODE_USER)
    server = _server_key()
    if server:
        return ResolvedAI(api_key=server, model=_server_model(), mode=MODE_SERVER)
    return ResolvedAI(api_key="", model=_server_model(), mode=MODE_FALLBACK)


def describe_ai_status(db: Session, user: Optional[User]) -> dict:
    """Payload для GET /api/user/ai-settings (без полного ключа).

    effective_mode описывает чат помощника-гражданина (per-user): user_key, если
    личный ключ есть, иначе needs_key."""
    cred = _user_credential(db, user)
    user_key_configured = bool(cred and cred.is_enabled and cred.encrypted_api_key)
    return {
        "server_provider_available": bool(_server_key()),
        "user_key_configured": user_key_configured,
        "key_storage_available": is_ai_crypto_configured(),
        "masked_key": (cred.masked_key if cred else ""),
        "model": (cred.model if (cred and cred.model) else _server_model()),
        "effective_mode": MODE_USER if user_key_configured else MODE_NEEDS_KEY,
        "last_checked_at": (cred.last_checked_at.isoformat() if (cred and cred.last_checked_at) else None),
    }


def verify_groq_key(api_key: str, model: str) -> tuple[bool, str]:
    """Короткий тестовый запрос к Groq. Возвращает (ok, дружелюбное сообщение)."""
    api_key = (api_key or "").strip()
    if not api_key:
        return False, "Ключ не задан."
    model = (model or DEFAULT_GROQ_MODEL).strip() or DEFAULT_GROQ_MODEL
    try:
        resp = httpx.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": "ping"}],
                "max_tokens": 1,
                "temperature": 0,
            },
            timeout=15.0,
        )
    except httpx.HTTPError:
        return False, "Сервер Groq недоступен. Попробуйте позже."
    if resp.status_code == 200:
        return True, "Ключ работает — AI подключён."
    if resp.status_code in (401, 403):
        return False, "Ключ недействителен или не имеет доступа."
    if resp.status_code == 429:
        return False, "Превышен лимит запросов к Groq. Попробуйте позже."
    if resp.status_code == 404:
        return False, "Модель не найдена. Проверьте название модели."
    return False, f"Groq вернул ошибку {resp.status_code}."
