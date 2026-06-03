"""
Выпадающее меню пользователя в header: «Профиль», «Настройки», «Выйти».

Клик по аватарке открывает popup. Закрытие — клик вне.
"""
from __future__ import annotations

import flet as ft

from theme.app_theme import APP_COLORS, ANIM_FAST, CENTER, border_all, padding_symmetric, ts


def build_user_menu(
    page: ft.Page,
    user: dict | None,
    on_profile,
    on_settings,
    on_logout,
    avatar_url: str | None = None,
    size: int = 40,
) -> ft.Control:
    """Аватарка + popup-меню. Не показывает текстовую подпись «Профиль»."""
    user = user or {}
    initials = _initials(user.get("name", ""))

    avatar_ctrl: ft.Control
    if avatar_url:
        avatar_ctrl = ft.Container(
            width=size, height=size, border_radius=size // 2,
            content=ft.Image(src=avatar_url, width=size, height=size, fit=ft.ImageFit.COVER, border_radius=size // 2),
            border=border_all(APP_COLORS["stroke2"]),
        )
    else:
        avatar_ctrl = ft.Container(
            width=size, height=size, border_radius=size // 2,
            bgcolor=APP_COLORS["surface2"],
            alignment=CENTER,
            content=ft.Text(initials or "•", size=ts(15), weight=ft.FontWeight.W_900, color=APP_COLORS["blue"]),
            border=border_all(APP_COLORS["stroke2"]),
        )

    # Menu items
    def _item(icon, label, on_click, danger: bool = False) -> ft.Control:
        text_color = APP_COLORS["red"] if danger else APP_COLORS["text"]
        icon_color = APP_COLORS["red"] if danger else APP_COLORS["muted"]
        row = ft.Container(
            ink=True,
            on_click=lambda _e: (_close_menu(), on_click() if on_click else None),
            padding=padding_symmetric(horizontal=14, vertical=11),
            border_radius=10,
            content=ft.Row(
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(icon, size=ts(18), color=icon_color),
                    ft.Text(label, size=ts(13), weight=ft.FontWeight.W_700, color=text_color),
                ],
            ),
        )

        def _hover(e: ft.HoverEvent) -> None:
            row.bgcolor = APP_COLORS["surface2"] if e.data == "true" else None
            try:
                row.update()
            except Exception:
                pass

        row.on_hover = _hover
        return row

    header_block = ft.Container(
        padding=padding_symmetric(horizontal=14, vertical=12),
        content=ft.Row(
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    width=36, height=36, border_radius=18,
                    bgcolor=APP_COLORS["active"],
                    alignment=CENTER,
                    content=ft.Text(initials or "•", size=ts(14), weight=ft.FontWeight.W_900, color=APP_COLORS["blue"]),
                ),
                ft.Column(
                    spacing=1,
                    expand=True,
                    controls=[
                        ft.Text(user.get("name", "Пользователь"), size=ts(13), weight=ft.FontWeight.W_900, color=APP_COLORS["text"], max_lines=1, no_wrap=True),
                        ft.Text(user.get("email", ""), size=ts(11), color=APP_COLORS["muted"], max_lines=1, no_wrap=True),
                    ],
                ),
            ],
        ),
    )

    menu_card = ft.Container(
        bgcolor=APP_COLORS["panel"],
        border_radius=14,
        border=border_all(APP_COLORS["stroke"]),
        shadow=ft.BoxShadow(blur_radius=24, color=ft.Colors.with_opacity(0.15, ft.Colors.BLACK)),
        width=260,
        padding=padding_symmetric(horizontal=6, vertical=6),
        content=ft.Column(
            spacing=2,
            tight=True,
            controls=[
                header_block,
                ft.Divider(height=1, color=APP_COLORS["stroke2"]),
                _item(ft.Icons.PERSON_OUTLINE, "Профиль", on_profile),
                _item(ft.Icons.SETTINGS_OUTLINED, "Настройки", on_settings),
                ft.Divider(height=1, color=APP_COLORS["stroke2"]),
                _item(ft.Icons.LOGOUT, "Выйти", on_logout, danger=True),
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

    return ft.Container(
        ink=True,
        border_radius=size // 2,
        on_click=_open_menu,
        content=avatar_ctrl,
        tooltip="Меню пользователя",
        animate=ft.Animation(ANIM_FAST, ft.AnimationCurve.EASE_OUT),
    )


def _initials(name: str) -> str:
    if not name:
        return "•"
    parts = name.strip().split()
    if len(parts) == 1:
        return parts[0][0].upper()
    return (parts[0][0] + parts[-1][0]).upper()
