"""
Гвард авторизации и ролей на клиенте.

Backend RBAC (require_role) уже защищает API. Этот модуль защищает UI:
- скрывает пункты меню по роли
- блокирует мутирующие действия для гостя (через guest_modal)
- проверяет доступ к маршрутам типа /admin
"""
from __future__ import annotations

from typing import Any, Callable

ROLE_RANK: dict[str, int] = {
    "guest": -1,
    "citizen": 0,
    "content_editor": 1,
    "platform_admin": 2,
}


def is_guest(auth_state: dict[str, Any]) -> bool:
    """True если пользователь не авторизован."""
    return not bool(auth_state.get("logged_in"))


def current_role(auth_state: dict[str, Any]) -> str:
    """Текущая роль: 'guest' если не залогинен, иначе значение из auth_state."""
    if is_guest(auth_state):
        return "guest"
    return str(auth_state.get("role") or "citizen")


def has_role(auth_state: dict[str, Any], required: str) -> bool:
    """True если у пользователя роль >= required по иерархии."""
    user_rank = ROLE_RANK.get(current_role(auth_state), -1)
    required_rank = ROLE_RANK.get(required, 99)
    return user_rank >= required_rank


def require_auth(auth_state: dict[str, Any], on_blocked: Callable[[], None] | None = None) -> bool:
    """
    Защита для мутирующих действий.

    Возвращает True если пользователь авторизован. Иначе вызывает on_blocked
    (обычно открывает guest_modal) и возвращает False.

    Usage:
        if not require_auth(auth_state, open_guest_modal):
            return
        # ... мутирующее действие
    """
    if not is_guest(auth_state):
        return True
    if on_blocked is not None:
        on_blocked()
    return False


def require_role(
    auth_state: dict[str, Any],
    required_role: str,
    on_denied: Callable[[], None] | None = None,
) -> bool:
    """Защита для ролевых действий. Возвращает True если роль >= required."""
    if has_role(auth_state, required_role):
        return True
    if on_denied is not None:
        on_denied()
    return False


def can_see_admin(auth_state: dict[str, Any]) -> bool:
    """Полный admin-раздел видит только platform_admin."""
    return has_role(auth_state, "platform_admin")


def can_see_editor_tools(auth_state: dict[str, Any]) -> bool:
    """Редакторские разделы видит content_editor и выше."""
    return has_role(auth_state, "content_editor")
