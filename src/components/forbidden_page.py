"""Страница «Доступ запрещён» (403) для маршрутов, недоступных по роли."""
from __future__ import annotations

import flet as ft

from components.buttons import primary_button, secondary_button
from components.cards import app_card, icon_circle
from components.layout import desktop_content
from theme.app_theme import APP_COLORS, padding_symmetric, ts


def build_forbidden_page(
    go_to,
    is_desktop: bool = False,
    title: str = "Доступ запрещён",
    description: str = "У вашей роли нет прав на просмотр этого раздела.",
    home_route: str = "/",
) -> ft.Control:
    body = ft.Column(
        spacing=22,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            icon_circle(
                ft.Icons.LOCK_OUTLINE,
                size=72,
                color=APP_COLORS["red"],
                bgcolor=APP_COLORS["surface2"],
            ),
            ft.Text(title, size=ts(24), weight=ft.FontWeight.W_900, color=APP_COLORS["text"], text_align=ft.TextAlign.CENTER),
            ft.Text(description, size=ts(14), color=APP_COLORS["muted"], text_align=ft.TextAlign.CENTER),
            ft.Row(
                spacing=10,
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[
                    secondary_button("На главную", icon=ft.Icons.HOME_OUTLINED, on_click=lambda _: go_to(home_route)),
                    primary_button("Войти под другой ролью", icon=ft.Icons.LOGIN, on_click=lambda _: go_to("/login")),
                ],
            ),
        ],
    )
    card = app_card(
        ft.Container(
            content=body,
            padding=padding_symmetric(horizontal=28, vertical=36),
            alignment=ft.alignment.center,
        ),
        width=520 if is_desktop else None,
    )
    return desktop_content(card, width=720, top=80) if is_desktop else ft.Container(
        padding=padding_symmetric(horizontal=18, vertical=24),
        content=card,
    )
