"""
Модальное окно «Войдите или зарегистрируйтесь» для гостевого режима.

Открывается при попытке гостя выполнить защищённое действие
(добавить документ, создать ситуацию, отметить задачу и т.п.).
"""
from __future__ import annotations

import flet as ft

from components.buttons import primary_button, secondary_button
from theme.app_theme import APP_COLORS, border_all, padding_symmetric, ts


def build_guest_modal(
    page: ft.Page,
    on_login,
    on_register,
    title: str = "Войдите или зарегистрируйтесь",
    description: str = "Чтобы выполнить это действие, нужен аккаунт.",
) -> ft.AlertDialog:
    """Создаёт AlertDialog. Открыть через page.open(dialog) (Flet 0.85)."""

    def _close(_=None) -> None:
        try:
            page.close(dialog)
        except Exception:
            dialog.open = False
            page.update()

    def _login_clicked(_=None) -> None:
        _close()
        if on_login:
            on_login()

    def _register_clicked(_=None) -> None:
        _close()
        if on_register:
            on_register()

    header = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.START,
        controls=[
            ft.Column(
                spacing=8,
                expand=True,
                controls=[
                    ft.Row(
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Container(
                                width=42,
                                height=42,
                                bgcolor=APP_COLORS["active"],
                                border_radius=12,
                                alignment=ft.alignment.center,
                                content=ft.Icon(ft.Icons.LOCK_OUTLINE, color=APP_COLORS["blue"], size=ts(22)),
                            ),
                            ft.Text(title, size=ts(18), weight=ft.FontWeight.W_900, color=APP_COLORS["text"], expand=True),
                        ],
                    ),
                    ft.Text(description, size=ts(14), color=APP_COLORS["muted"]),
                ],
            ),
            ft.IconButton(
                icon=ft.Icons.CLOSE,
                icon_color=APP_COLORS["muted"],
                tooltip="Закрыть",
                on_click=_close,
            ),
        ],
    )

    actions = ft.Row(
        spacing=10,
        controls=[
            secondary_button("Регистрация", icon=ft.Icons.PERSON_ADD_OUTLINED, on_click=_register_clicked, expand=True),
            primary_button("Войти", icon=ft.Icons.LOGIN, on_click=_login_clicked, expand=True),
        ],
    )

    body = ft.Container(
        padding=padding_symmetric(horizontal=22, vertical=22),
        bgcolor=APP_COLORS["panel"],
        border_radius=18,
        border=border_all(APP_COLORS["stroke"]),
        content=ft.Column(
            spacing=22,
            controls=[header, actions],
            tight=True,
        ),
        width=460,
    )

    dialog = ft.AlertDialog(
        modal=False,  # клик вне закрывает
        content=body,
        bgcolor=ft.Colors.TRANSPARENT,
        shape=ft.RoundedRectangleBorder(radius=18),
        content_padding=0,
        inset_padding=padding_symmetric(horizontal=20, vertical=40),
    )
    return dialog


def open_guest_modal(
    page: ft.Page,
    go_to,
    description: str = "Чтобы выполнить это действие, нужен аккаунт.",
) -> None:
    """Хелпер: открыть модалку и навешать переходы на /login и /register."""
    dialog = build_guest_modal(
        page,
        on_login=lambda: go_to("/login"),
        on_register=lambda: go_to("/register"),
        description=description,
    )
    try:
        page.open(dialog)
    except Exception:
        page.dialog = dialog
        dialog.open = True
        page.update()
