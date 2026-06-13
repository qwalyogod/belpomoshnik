"""Настройки каналов уведомлений пользователя.

In-app центр включён всегда. Остальные каналы работают только после явного
разрешения пользователя и сохраняются в ``users.settings.notifications``.
"""
from __future__ import annotations

import json
from typing import Any

from backend.models import User


DEFAULT_NOTIFICATION_PREFERENCES: dict[str, Any] = {
    "system_notifications_enabled": False,
    "local_notifications_enabled": False,
    "native_push_enabled": False,
    "browser_notifications_enabled": False,
    "doc_expiry_enabled": True,
    "task_deadline_enabled": True,
    "utility_enabled": True,
    "tax_enabled": True,
    "law_updates_enabled": True,
    "security_enabled": True,
    "quiet_hours_enabled": False,
    "quiet_hours_from": "22:00",
    "quiet_hours_to": "08:00",
}


def get_user_settings(user: User) -> dict[str, Any]:
    try:
        value = json.loads(user.settings or "{}")
    except (TypeError, json.JSONDecodeError):
        value = {}
    return value if isinstance(value, dict) else {}


def get_notification_preferences(user: User) -> dict[str, Any]:
    settings = get_user_settings(user)
    raw = settings.get("notifications", {})
    if not isinstance(raw, dict):
        raw = {}
    return {**DEFAULT_NOTIFICATION_PREFERENCES, **raw}


def notification_type_enabled(preferences: dict[str, Any], notification_type: str) -> bool:
    key_by_type = {
        "doc_expiry": "doc_expiry_enabled",
        "document_expiry": "doc_expiry_enabled",
        "task_due": "task_deadline_enabled",
        "utility_due": "utility_enabled",
        "utility_readings": "utility_enabled",
        "tax_due": "tax_enabled",
        "legal_update": "law_updates_enabled",
        "law_update": "law_updates_enabled",
        "security": "security_enabled",
    }
    key = key_by_type.get(notification_type)
    return True if key is None else bool(preferences.get(key, True))
