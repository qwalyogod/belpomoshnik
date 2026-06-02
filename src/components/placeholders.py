from __future__ import annotations

import flet as ft

from theme.app_theme import APP_COLORS, APP_RADIUS, CENTER, border_all, ts


def photo_placeholder(
    label: str,
    width: int | float | None = None,
    height: int | float | None = 180,
    aspect_ratio: float | None = None,
) -> ft.Container:
    text = f"здесь будет фото: {label}"
    inner = ft.Container(
        expand=True,
        alignment=CENTER,
        border_radius=max(10, APP_RADIUS["card"] - 4),
        border=border_all(APP_COLORS["stroke2"]),
        content=ft.Text(
            text,
            size=13,
            color=APP_COLORS["muted"],
            text_align=ft.TextAlign.CENTER,
        ),
    )
    computed_height = height
    if aspect_ratio and isinstance(width, (int, float)):
        computed_height = int(float(width) / aspect_ratio)
    return ft.Container(
        width=width,
        height=computed_height,
        padding=6,
        border_radius=APP_RADIUS["card"],
        bgcolor=APP_COLORS["surface2"],
        border=border_all(APP_COLORS["stroke"]),
        content=inner,
    )
