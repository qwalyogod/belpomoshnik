from __future__ import annotations

import flet as ft

from components.layout import avatar
from theme.app_theme import APP_COLORS, CENTER, border_all, border_top, padding_symmetric


SIDEBAR_ITEMS = [
    ("home", "Главная", ft.Icons.HOME_OUTLINED, "/"),
    ("problems", "Каталог проблем", ft.Icons.SEARCH_OUTLINED, "/problems"),
    ("scenarios", "Сценарии", ft.Icons.ROUTE_OUTLINED, "/scenarios"),
    ("situations", "Мои ситуации", ft.Icons.TASK_ALT_OUTLINED, "/situations"),
    ("documents", "Документы", ft.Icons.ARTICLE_OUTLINED, "/documents"),
    ("utility", "ЖКХ-трекер", ft.Icons.HOME_WORK_OUTLINED, "/utility"),
    ("taxes", "Налоговый трекер", ft.Icons.RECEIPT_LONG_OUTLINED, "/taxes"),
    ("notifications", "Уведомления", ft.Icons.NOTIFICATIONS_NONE_OUTLINED, "/notifications"),
    ("laws", "Закон-апдейты", ft.Icons.BALANCE_OUTLINED, "/legal-updates"),
    ("learning", "Обучение", ft.Icons.SCHOOL_OUTLINED, "/learning"),
    ("admin", "Админка", ft.Icons.ADMIN_PANEL_SETTINGS_OUTLINED, "/admin"),
]


def _sidebar_item(key: str, label: str, icon, route: str, active_key: str, go_to) -> ft.Container:
    active = key == active_key
    return ft.Container(
        ink=True,
        on_click=lambda _: go_to(route),
        border_radius=18,
        padding=padding_symmetric(horizontal=14, vertical=12),
        bgcolor=APP_COLORS["active"] if active else None,
        content=ft.Row(
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    width=34,
                    height=34,
                    border_radius=17,
                    bgcolor=APP_COLORS["blue"] if active else APP_COLORS["surface2"],
                    alignment=CENTER,
                    content=ft.Icon(icon, size=18, color=ft.Colors.WHITE if active else APP_COLORS["muted"]),
                ),
                ft.Text(
                    label,
                    size=18,
                    weight=ft.FontWeight.W_800 if active else ft.FontWeight.W_600,
                    color=APP_COLORS["blue_text"] if active else APP_COLORS["text"],
                ),
            ],
        ),
    )


def build_sidebar(active_key: str, go_to, on_toggle_theme=None, theme_mode: str = "light", user: dict | None = None) -> ft.Container:
    dark_mode = theme_mode == "dark"
    return ft.Container(
        width=350,
        expand=True,
        bgcolor=APP_COLORS["sidebar"],
        border=ft.Border(right=ft.BorderSide(1, APP_COLORS["stroke2"])),
        padding=ft.Padding(left=28, top=30, right=20, bottom=24),
        content=ft.Column(
            expand=True,
            spacing=24,
            controls=[
                ft.Row(
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Container(
                            width=60,
                            height=60,
                            border_radius=22,
                            bgcolor=APP_COLORS["blue"],
                            alignment=CENTER,
                            content=ft.Text("Б", size=30, weight=ft.FontWeight.W_900, color=ft.Colors.WHITE),
                        ),
                        ft.Column(
                            spacing=2,
                            controls=[
                                ft.Text("Белпомощник", size=25, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                                ft.Text("личный помощник гражданина", size=13, color=APP_COLORS["muted"]),
                            ],
                        ),
                    ],
                ),
                ft.Container(
                    padding=16,
                    border_radius=22,
                    bgcolor=APP_COLORS["surface"],
                    border=border_all(APP_COLORS["stroke2"]),
                    content=ft.Row(
                        spacing=12,
                        controls=[
                            avatar(radius=24),
                            ft.Column(
                                spacing=3,
                                expand=True,
                                controls=[
                                    ft.Text((user or {}).get("name", "Пользователь"), size=16, weight=ft.FontWeight.W_800, color=APP_COLORS["text"]),
                                    ft.Text((user or {}).get("city", "Минск"), size=13, color=APP_COLORS["muted"]),
                                ],
                            ),
                        ],
                    ),
                ),
                ft.Column(
                    spacing=8,
                    controls=[
                        _sidebar_item(key, label, icon, route, active_key, go_to)
                        for key, label, icon, route in SIDEBAR_ITEMS
                    ],
                ),
                ft.Container(expand=True),
                ft.Container(
                    padding=16,
                    border_radius=22,
                    bgcolor=APP_COLORS["surface"],
                    border=border_all(APP_COLORS["stroke2"]),
                    content=ft.Column(
                        spacing=12,
                        controls=[
                            ft.Row(
                                spacing=10,
                                controls=[
                                    ft.Icon(ft.Icons.INFO_OUTLINE, size=20, color=APP_COLORS["blue"]),
                                    ft.Text("Режим интерфейса", size=15, weight=ft.FontWeight.W_800, color=APP_COLORS["text"]),
                                ],
                            ),
                            ft.Container(height=1, bgcolor=APP_COLORS["stroke2"]),
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text("Тёмная тема", size=14, color=APP_COLORS["muted"]),
                                    ft.Switch(value=dark_mode, active_color=APP_COLORS["blue"], on_change=on_toggle_theme),
                                ],
                            ),
                        ],
                    ),
                ),
                ft.Container(height=1, border=border_top(APP_COLORS["stroke2"])),
                ft.Text("0.1 beta · справочная версия", size=12, color=APP_COLORS["muted2"]),
            ],
        ),
    )
