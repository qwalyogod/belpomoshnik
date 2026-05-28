from __future__ import annotations

import flet as ft

from components.layout import avatar
from theme.app_theme import APP_COLORS, CENTER, border_bottom


def build_mobile_topbar(title: str, go_to=None, user: dict | None = None) -> ft.Container:
    return ft.Container(
        height=58,
        bgcolor=APP_COLORS["screen"],
        border=border_bottom(APP_COLORS["stroke2"]),
        padding=ft.Padding(left=20, top=6, right=16, bottom=6),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Row(
                    spacing=10,
                    expand=True,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Container(
                            width=36,
                            height=36,
                            border_radius=14,
                            bgcolor=APP_COLORS["blue"],
                            alignment=CENTER,
                            content=ft.Text("Б", size=20, weight=ft.FontWeight.W_900, color=ft.Colors.WHITE),
                        ),
                        ft.Text(title, size=22, weight=ft.FontWeight.W_900, color=APP_COLORS["text"], max_lines=1),
                    ],
                ),
                ft.Row(
                    spacing=6,
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.SEARCH,
                            icon_color=APP_COLORS["muted"],
                            tooltip="Поиск",
                            width=42,
                            height=42,
                            on_click=lambda _: go_to("/search") if go_to else None,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.NOTIFICATIONS_NONE_OUTLINED,
                            icon_color=APP_COLORS["muted"],
                            tooltip="Уведомления",
                            width=42,
                            height=42,
                            on_click=lambda _: go_to("/notifications") if go_to else None,
                        ),
                        ft.Container(
                            content=avatar(radius=18),
                            on_click=lambda _: go_to("/profile") if go_to else None,
                            ink=True,
                        ),
                    ],
                ),
            ],
        ),
    )
