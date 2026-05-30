from __future__ import annotations

import flet as ft

from components.layout import avatar
from theme.app_theme import APP_COLORS, ANIM_FAST, CENTER, border_bottom


def build_mobile_topbar(
    title: str,
    go_to=None,
    user: dict | None = None,
    on_open_ai_chat=None,
) -> ft.Container:
    ai_btn = ft.Container(
        width=38,
        height=38,
        border_radius=19,
        bgcolor=APP_COLORS["active"],
        alignment=CENTER,
        ink=True,
        on_click=on_open_ai_chat,
        tooltip="ИИ-помощник",
        animate=ft.Animation(ANIM_FAST, ft.AnimationCurve.EASE_OUT),
        content=ft.Icon(ft.Icons.AUTO_AWESOME_OUTLINED, size=18, color=APP_COLORS["blue"]),
    ) if on_open_ai_chat else ft.Container(width=0)

    return ft.Container(
        height=58,
        bgcolor=APP_COLORS["screen"],
        border=border_bottom(APP_COLORS["stroke2"]),
        padding=ft.Padding(left=18, top=6, right=14, bottom=6),
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
                            width=34,
                            height=34,
                            border_radius=12,
                            bgcolor=APP_COLORS["blue"],
                            alignment=CENTER,
                            content=ft.Text("Б", size=18, weight=ft.FontWeight.W_900, color=ft.Colors.WHITE),
                        ),
                        ft.Text(
                            title,
                            size=20,
                            weight=ft.FontWeight.W_900,
                            color=APP_COLORS["text"],
                            max_lines=1,
                        ),
                    ],
                ),
                ft.Row(
                    spacing=4,
                    controls=[
                        ai_btn,
                        ft.IconButton(
                            icon=ft.Icons.SEARCH,
                            icon_color=APP_COLORS["muted"],
                            tooltip="Поиск",
                            width=40,
                            height=40,
                            on_click=lambda _: go_to("/search") if go_to else None,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.NOTIFICATIONS_NONE_OUTLINED,
                            icon_color=APP_COLORS["muted"],
                            tooltip="Уведомления",
                            width=40,
                            height=40,
                            on_click=lambda _: go_to("/notifications") if go_to else None,
                        ),
                        ft.Container(
                            content=avatar(radius=17),
                            on_click=lambda _: go_to("/profile") if go_to else None,
                            ink=True,
                            border_radius=17,
                        ),
                    ],
                ),
            ],
        ),
    )
