"""
Переключатель тестовых аккаунтов в правом верхнем углу.

Круглая аватарка с hover-«булька»-анимацией. Клик открывает popup со
списком тестовых аккаунтов (из /api/auth/test-accounts). Выбор аккаунта
выполняет быстрый login без формы.
"""
from __future__ import annotations

import flet as ft

from theme.app_theme import APP_COLORS, ANIM_FAST, border_all, padding_symmetric, ts


_ROLE_LABELS: dict[str, tuple[str, str]] = {
    "citizen": ("Гражданин", APP_COLORS["green"]),
    "content_editor": ("Редактор", APP_COLORS["blue"]),
    "platform_admin": ("Администратор", APP_COLORS["purple"]),
}


def _role_meta(role_id: str) -> tuple[str, str]:
    return _ROLE_LABELS.get(role_id, (role_id, APP_COLORS["muted"]))


def _initials(name: str) -> str:
    if not name:
        return "•"
    parts = name.strip().split()
    if len(parts) == 1:
        return parts[0][0].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def build_role_switcher(
    page: ft.Page,
    current_role: str,
    accounts: list[dict],
    on_switch,
    size: int = 40,
) -> ft.Control:
    """
    Круглая аватарка-переключатель.

    accounts: список {email, name, role} от /api/auth/test-accounts.
    on_switch(email): вызывается при выборе аккаунта.
    """
    if not accounts:
        return ft.Container(width=0, height=0)

    avatar_label, avatar_color = _role_meta(current_role)
    avatar_letter = avatar_label[0] if avatar_label else "•"

    # ── Круглая аватарка с hover-bubble ───────────────────────────────────
    avatar_inner = ft.Container(
        width=size,
        height=size,
        border_radius=size // 2,
        bgcolor=avatar_color,
        alignment=ft.alignment.center,
        animate=ft.Animation(ANIM_FAST, ft.AnimationCurve.EASE_OUT),
        animate_scale=ft.Animation(ANIM_FAST, ft.AnimationCurve.EASE_OUT),
        content=ft.Text(avatar_letter, size=ts(16), weight=ft.FontWeight.W_900, color=ft.Colors.WHITE),
        scale=ft.Scale(1.0),
        tooltip="Быстрый вход",
        border=border_all(APP_COLORS["panel"], width=2),
    )

    def _on_hover(e: ft.HoverEvent) -> None:
        avatar_inner.scale = ft.Scale(1.08 if e.data == "true" else 1.0)
        try:
            avatar_inner.update()
        except Exception:
            pass

    # ── Список аккаунтов в попапе ─────────────────────────────────────────
    def _account_row(account: dict) -> ft.Control:
        role = account.get("role", "")
        label, color = _role_meta(role)
        active = role == current_role
        dot = ft.Container(width=10, height=10, border_radius=5, bgcolor=color)
        title = ft.Text(label, size=ts(13), weight=ft.FontWeight.W_700, color=APP_COLORS["text"])
        email = ft.Text(account.get("email", ""), size=ts(11), color=APP_COLORS["muted"], max_lines=1, no_wrap=True)
        right = ft.Icon(ft.Icons.CHECK_CIRCLE if active else ft.Icons.LOGIN, size=ts(16),
                        color=color if active else APP_COLORS["muted"])

        def _click(_=None) -> None:
            _close_menu()
            if on_switch:
                on_switch(account.get("email", ""), account.get("name", ""), role)

        row = ft.Container(
            ink=True,
            on_click=_click,
            padding=padding_symmetric(horizontal=14, vertical=10),
            border_radius=10,
            bgcolor=APP_COLORS["active"] if active else None,
            content=ft.Row(
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    dot,
                    ft.Column(spacing=1, expand=True, controls=[title, email]),
                    right,
                ],
            ),
        )

        def _row_hover(e: ft.HoverEvent) -> None:
            if not active:
                row.bgcolor = APP_COLORS["surface2"] if e.data == "true" else None
                try:
                    row.update()
                except Exception:
                    pass

        row.on_hover = _row_hover
        return row

    menu_card = ft.Container(
        padding=padding_symmetric(horizontal=8, vertical=8),
        bgcolor=APP_COLORS["panel"],
        border_radius=14,
        border=border_all(APP_COLORS["stroke"]),
        shadow=ft.BoxShadow(blur_radius=24, color=ft.Colors.with_opacity(0.15, ft.Colors.BLACK)),
        width=260,
        content=ft.Column(
            spacing=2,
            tight=True,
            controls=[
                ft.Container(
                    padding=padding_symmetric(horizontal=14, vertical=6),
                    content=ft.Text("Быстрый вход", size=ts(11), weight=ft.FontWeight.W_700, color=APP_COLORS["muted2"]),
                ),
                *[_account_row(a) for a in accounts],
            ],
        ),
    )

    menu_dialog = ft.AlertDialog(
        modal=False,
        content=menu_card,
        bgcolor=ft.Colors.TRANSPARENT,
        content_padding=0,
        inset_padding=padding_symmetric(horizontal=10, vertical=10),
        shape=ft.RoundedRectangleBorder(radius=14),
    )

    def _close_menu() -> None:
        try:
            page.close(menu_dialog)
        except Exception:
            menu_dialog.open = False
            page.update()

    def _open_menu(_=None) -> None:
        try:
            page.open(menu_dialog)
        except Exception:
            page.dialog = menu_dialog
            menu_dialog.open = True
            page.update()

    avatar_inner.on_hover = _on_hover

    clickable = ft.Container(
        ink=True,
        border_radius=size // 2,
        on_click=_open_menu,
        content=avatar_inner,
        tooltip="Быстрый вход",
    )
    return clickable
