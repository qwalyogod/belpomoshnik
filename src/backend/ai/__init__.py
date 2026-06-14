"""AI service layer (промпт 3).

Вынесена работа с провайдерскими ключами: резолвер (user/server/fallback),
строгий per-user резолвер для чата гражданина и проверка ключа.
"""
from .credentials import (
    DEFAULT_GROQ_MODEL,
    GROQ_URL,
    NEEDS_KEY_MESSAGE,
    ResolvedAI,
    describe_ai_status,
    resolve_ai,
    resolve_user_ai,
    verify_groq_key,
)

__all__ = [
    "DEFAULT_GROQ_MODEL",
    "GROQ_URL",
    "NEEDS_KEY_MESSAGE",
    "ResolvedAI",
    "describe_ai_status",
    "resolve_ai",
    "resolve_user_ai",
    "verify_groq_key",
]
