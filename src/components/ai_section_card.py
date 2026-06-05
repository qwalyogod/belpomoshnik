from __future__ import annotations

import flet as ft

from services.ai_helper import SectionInfo
from theme.app_theme import APP_COLORS, APP_RADIUS, ANIM_FAST, CENTER, border_all, padding_symmetric, ts


def build_ai_section_card(
    section: SectionInfo,
    *,
    on_click=None,
    warning: str | None = None,
) -> ft.Container:
    """Compact transition card shown under assistant answer."""
    card = ft.Container(
        ink=True,
        on_click=lambda _: on_click(section.route) if on_click else None,
        border_radius=APP_RADIUS["card"],
        bgcolor=APP_COLORS["surface"],
        border=border_all(APP_COLORS["stroke2"]),
        padding=ft.Padding(left=12, top=12, right=12, bottom=12),
        animate=ft.Animation(ANIM_FAST, ft.AnimationCurve.EASE_OUT),
        content=ft.Column(
            spacing=8,
            controls=[
                ft.Row(
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Container(
                            width=32,
                            height=32,
                            border_radius=12,
                            bgcolor=APP_COLORS["active"],
                            alignment=CENTER,
                            content=ft.Icon(ft.Icons.ARROW_OUTWARD_ROUNDED, size=ts(18), color=APP_COLORS["blue"]),
                        ),
                        ft.Column(
                            spacing=1,
                            expand=True,
                            controls=[
                                ft.Text(section.title, size=ts(14), weight=ft.FontWeight.W_800, color=APP_COLORS["text"]),
                                ft.Text(section.description, size=ts(11), color=APP_COLORS["muted"], max_lines=2),
                            ],
                        ),
                    ],
                ),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(
                            warning or "Открыть раздел",
                            size=ts(11),
                            color=APP_COLORS["warning"] if warning else APP_COLORS["muted2"],
                            max_lines=2,
                            expand=True,
                        ),
                        ft.Text("Перейти →", size=ts(12), weight=ft.FontWeight.W_800, color=APP_COLORS["blue"]),
                    ],
                ),
            ],
        ),
    )

    def _hover(e: ft.HoverEvent) -> None:
        card.bgcolor = APP_COLORS["surface2"] if e.data == "true" else APP_COLORS["surface"]
        card.update()

    card.on_hover = _hover
    return card
