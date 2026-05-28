from __future__ import annotations

import flet as ft

from components.cards import app_card, badge, icon_circle
from theme.app_theme import APP_COLORS, SPACING, border_all


def stage_step_card(
    title: str,
    description: str = "",
    steps: list[ft.Control] | None = None,
    selected: bool = False,
    locked: bool = False,
    order_label: str | None = None,
) -> ft.Container:
    border_color = APP_COLORS["blue"] if selected else APP_COLORS["stroke2"]
    stage_badge = badge("заблокировано", "locked") if locked else badge(order_label or "этап", "blue")
    icon = ft.Icons.LOCK_OUTLINE if locked else ft.Icons.ACCOUNT_TREE_OUTLINED
    content_controls: list[ft.Control] = [
        ft.Row(
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                icon_circle(icon, color=APP_COLORS["muted2"] if locked else APP_COLORS["blue"], size=44),
                ft.Column(
                    spacing=6,
                    expand=True,
                    controls=[
                        ft.Row(spacing=8, wrap=True, controls=[stage_badge]),
                        ft.Text(title, size=18, weight=ft.FontWeight.W_800, color=APP_COLORS["text"]),
                        ft.Text(description, size=14, color=APP_COLORS["muted"]) if description else ft.Container(),
                    ],
                ),
            ],
        )
    ]
    if steps:
        content_controls.append(
            ft.Container(
                margin=ft.Margin(left=54, top=4, right=0, bottom=0),
                content=ft.Column(spacing=10, controls=steps),
            )
        )
    card = app_card(
        ft.Column(spacing=SPACING["md"], controls=content_controls),
        padding=SPACING["xl"],
        border_color=border_color,
        animate=True,
    )
    if selected:
        card.border = border_all(APP_COLORS["blue"], width=2)
    return card


def step_row(title: str, completed: bool = False, locked: bool = False, on_change=None) -> ft.Container:
    checkbox = ft.Checkbox(
        value=completed,
        disabled=locked,
        active_color=APP_COLORS["green"],
        on_change=on_change,
    )
    return ft.Container(
        border_radius=16,
        padding=ft.Padding(left=10, top=8, right=12, bottom=8),
        bgcolor=APP_COLORS["surface2"],
        border=border_all(APP_COLORS["stroke2"]),
        content=ft.Row(
            spacing=8,
            controls=[
                checkbox,
                ft.Icon(ft.Icons.LOCK_OUTLINE, size=18, color=APP_COLORS["muted2"]) if locked else ft.Container(width=0),
                ft.Text(title, size=14, weight=ft.FontWeight.W_600, color=APP_COLORS["muted"] if locked else APP_COLORS["text"], expand=True),
            ],
        ),
    )
