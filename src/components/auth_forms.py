from __future__ import annotations

import flet as ft

from components.cards import app_card, badge, icon_circle
from components.layout import desktop_content
from theme.app_theme import (
    APP_COLORS,
    APP_RADIUS,
    CENTER,
    SPACING,
    border_all,
    padding_symmetric,
)


AUTH_CARD_WIDTH = 460
MOBILE_AUTH_WIDTH = 340


def auth_logo() -> ft.Row:
    return ft.Row(
        spacing=12,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(
                width=42,
                height=42,
                border_radius=14,
                bgcolor=APP_COLORS["blue"],
                alignment=CENTER,
                content=ft.Icon(ft.Icons.NAVIGATION_ROUNDED, size=24, color=ft.Colors.WHITE),
            ),
            ft.Text("Белпомощник", size=22, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
        ],
    )


def auth_tabs(active: str, go_to=None) -> ft.Container:
    def tab(label: str, key: str, route: str) -> ft.Container:
        selected = active == key
        return ft.Container(
            expand=True,
            height=44,
            alignment=CENTER,
            border_radius=APP_RADIUS["button"],
            bgcolor=APP_COLORS["blue"] if selected else None,
            content=ft.Text(
                label,
                size=14,
                weight=ft.FontWeight.W_900,
                color=ft.Colors.WHITE if selected else APP_COLORS["muted"],
                text_align=ft.TextAlign.CENTER,
            ),
            on_click=lambda _: go_to(route) if go_to else None,
            ink=not selected,
        )

    return ft.Container(
        padding=4,
        border_radius=18,
        bgcolor=APP_COLORS["surface2"],
        border=border_all(APP_COLORS["stroke2"]),
        content=ft.Row(
            spacing=4,
            controls=[
                tab("Вход", "login", "/login"),
                tab("Регистрация", "register", "/register"),
            ],
        ),
    )


def auth_text_field(
    label: str,
    value: str = "",
    hint: str = "",
    prefix_icon=None,
    keyboard_type: ft.KeyboardType = ft.KeyboardType.TEXT,
    password: bool = False,
) -> ft.TextField:
    return ft.TextField(
        label=label,
        value=value,
        hint_text=hint,
        prefix_icon=prefix_icon,
        keyboard_type=keyboard_type,
        password=password,
        can_reveal_password=password,
        border_radius=APP_RADIUS["input"],
        border_color=APP_COLORS["stroke2"],
        focused_border_color=APP_COLORS["blue"],
        border_width=1,
        focused_border_width=1.5,
        bgcolor=APP_COLORS["search"],
        filled=True,
        fill_color=APP_COLORS["search"],
        cursor_color=APP_COLORS["blue"],
        color=APP_COLORS["text"],
        label_style=ft.TextStyle(color=APP_COLORS["muted"], weight=ft.FontWeight.W_700),
        hint_style=ft.TextStyle(color=APP_COLORS["muted2"]),
        text_style=ft.TextStyle(size=16, weight=ft.FontWeight.W_500),
        content_padding=ft.Padding(left=14, top=14, right=14, bottom=14),
        error_style=ft.TextStyle(size=12, color=APP_COLORS["red"], weight=ft.FontWeight.W_600),
        error_max_lines=2,
    )


def set_field_error(field: ft.TextField, message: str | None) -> None:
    has_error = bool(message)
    field.error = message or None
    field.border_color = APP_COLORS["red"] if has_error else APP_COLORS["stroke2"]
    field.focused_border_color = APP_COLORS["red"] if has_error else APP_COLORS["blue"]
    if field.page:
        field.update()


def form_footer(text: str, action_text: str, route: str, go_to=None) -> ft.Row:
    return ft.Row(
        alignment=ft.MainAxisAlignment.CENTER,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=6,
        wrap=True,
        controls=[
            ft.Text(text, size=13, color=APP_COLORS["muted"]),
            ft.Container(
                content=ft.Text(action_text, size=13, weight=ft.FontWeight.W_900, color=APP_COLORS["blue_text"]),
                on_click=lambda _: go_to(route) if go_to else None,
                ink=True,
            ),
        ],
    )


def auth_shell(
    card: ft.Control,
    *,
    is_desktop: bool,
    title: str,
    subtitle: str,
) -> ft.Control:
    if not is_desktop:
        return ft.Container(width=MOBILE_AUTH_WIDTH, content=card)

    side = ft.Column(
        spacing=22,
        controls=[
            icon_circle(ft.Icons.NAVIGATION_ROUNDED, color=ft.Colors.WHITE, bgcolor=APP_COLORS["blue"], size=68),
            ft.Text(title, size=36, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
            ft.Text(subtitle, size=16, color=APP_COLORS["muted"]),
            ft.Row(
                spacing=8,
                wrap=True,
                controls=[
                    badge("Проблема → план", "blue"),
                    badge("Напоминания", "gray"),
                    badge("Локальные данные", "cyan"),
                ],
            ),
            app_card(
                ft.Column(
                    spacing=10,
                    controls=[
                        ft.Text("Сегодня важно", size=18, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                        _important_row("1", "Истекает медкнижка", "через 12 дней"),
                        _important_row("2", "Новый апдейт по ЖКХ", "для вашего профиля"),
                        _important_row("3", "План “Переезд”", "2 задачи сегодня"),
                    ],
                ),
                padding=20,
                bgcolor=APP_COLORS["surface"],
            ),
        ],
    )
    content = ft.Row(
        spacing=34,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(width=430, content=side),
            ft.Container(width=AUTH_CARD_WIDTH, content=card),
        ],
    )
    return desktop_content(content, width=960, top=52, bottom=80)


def _important_row(index: str, title: str, subtitle: str) -> ft.Row:
    return ft.Row(
        spacing=10,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(
                width=30,
                height=30,
                border_radius=15,
                alignment=CENTER,
                bgcolor=APP_COLORS["active"],
                content=ft.Text(index, size=13, weight=ft.FontWeight.W_900, color=APP_COLORS["blue_text"]),
            ),
            ft.Column(
                spacing=1,
                expand=True,
                controls=[
                    ft.Text(title, size=14, weight=ft.FontWeight.W_800, color=APP_COLORS["text"]),
                    ft.Text(subtitle, size=12, color=APP_COLORS["muted"]),
                ],
            ),
        ],
    )
