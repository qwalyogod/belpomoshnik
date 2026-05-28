import flet as ft

from theme.app_theme import APP_COLORS, APP_RADIUS, padding_symmetric


def primary_button(text: str, on_click=None, icon=None, expand: bool = False, width: int | None = None, height: int = 50) -> ft.Button:
    return ft.Button(
        content=text,
        icon=icon,
        on_click=on_click,
        height=height,
        width=width,
        expand=expand,
        style=ft.ButtonStyle(
            bgcolor=APP_COLORS["blue"],
            color=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=APP_RADIUS["button"]),
            elevation=0,
            padding=padding_symmetric(horizontal=18, vertical=12),
            text_style=ft.TextStyle(weight=ft.FontWeight.W_800),
        ),
    )


def secondary_button(text: str, on_click=None, icon=None, expand: bool = False, width: int | None = None, height: int = 48) -> ft.Button:
    return ft.Button(
        content=text,
        icon=icon,
        on_click=on_click,
        height=height,
        width=width,
        expand=expand,
        style=ft.ButtonStyle(
            color=APP_COLORS["text"],
            bgcolor=APP_COLORS["surface"],
            side=ft.BorderSide(1, APP_COLORS["stroke2"]),
            shape=ft.RoundedRectangleBorder(radius=APP_RADIUS["button"]),
            padding=padding_symmetric(horizontal=16, vertical=12),
            text_style=ft.TextStyle(weight=ft.FontWeight.W_800),
        ),
    )


def ghost_button(
    text: str,
    on_click=None,
    icon=None,
    width: int | None = None,
    expand: bool = False,
    height: int = 44,
) -> ft.Button:
    return ft.Button(
        content=text,
        icon=icon,
        on_click=on_click,
        height=height,
        width=width,
        expand=expand,
        style=ft.ButtonStyle(
            color=APP_COLORS["blue_text"],
            bgcolor=APP_COLORS["surface2"],
            side=ft.BorderSide(1, APP_COLORS["stroke2"]),
            shape=ft.RoundedRectangleBorder(radius=APP_RADIUS["button"]),
            padding=padding_symmetric(horizontal=16, vertical=10),
            text_style=ft.TextStyle(weight=ft.FontWeight.W_800),
        ),
    )
