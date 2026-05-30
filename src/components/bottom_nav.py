import flet as ft

from theme.app_theme import (
    ANIM_FAST,
    APP_COLORS,
    BOTTOM_NAV_HEIGHT,
    BOTTOM_NAV_SAFE_GAP,
    CENTER,
    border_top,
)


# Documents removed — accessible via Profile
NAV_ITEMS = [
    ("home", "Главная", ft.Icons.HOME_OUTLINED, ft.Icons.HOME),
    ("problems", "Каталог", ft.Icons.ARTICLE_OUTLINED, ft.Icons.ARTICLE),
    ("situations", "Ситуации", ft.Icons.TASK_ALT_OUTLINED, ft.Icons.TASK_ALT),
    ("profile", "Профиль", ft.Icons.PERSON_OUTLINE, ft.Icons.PERSON),
]


def _nav_button(key: str, label: str, icon, selected_icon, selected_key: str, on_select) -> ft.Container:
    selected = key == selected_key

    indicator = ft.Container(
        width=40,
        height=28,
        border_radius=14,
        bgcolor=APP_COLORS["active"] if selected else None,
        alignment=CENTER,
        animate=ft.Animation(ANIM_FAST, ft.AnimationCurve.EASE_OUT),
        content=ft.Icon(
            selected_icon if selected else icon,
            size=21,
            color=APP_COLORS["blue_text"] if selected else APP_COLORS["muted"],
        ),
    )

    return ft.Container(
        expand=True,
        ink=True,
        on_click=lambda _: on_select(key),
        padding=ft.Padding(left=0, top=8, right=0, bottom=4),
        content=ft.Column(
            spacing=3,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                indicator,
                ft.Text(
                    label,
                    size=9,
                    weight=ft.FontWeight.W_600 if selected else ft.FontWeight.W_500,
                    color=APP_COLORS["blue_text"] if selected else APP_COLORS["muted"],
                    text_align=ft.TextAlign.CENTER,
                    max_lines=1,
                    no_wrap=True,
                ),
            ],
        ),
    )


def _ai_center_button(on_open_ai_chat) -> ft.Container:
    """Center AI FAB — sits in nav row at same height as other items."""
    btn = ft.Container(
        width=48,
        height=48,
        border_radius=24,
        bgcolor=APP_COLORS["blue"],
        alignment=CENTER,
        ink=True,
        on_click=on_open_ai_chat,
        tooltip="ИИ-помощник",
        shadow=[ft.BoxShadow(blur_radius=12, offset=ft.Offset(0, 4), color="#3319A3E8")],
        animate=ft.Animation(ANIM_FAST, ft.AnimationCurve.EASE_OUT),
        content=ft.Icon(ft.Icons.AUTO_AWESOME_OUTLINED, size=22, color=ft.Colors.WHITE),
    )

    def _hover(e: ft.HoverEvent) -> None:
        btn.bgcolor = APP_COLORS["blue_text"] if e.data == "true" else APP_COLORS["blue"]
        btn.update()

    btn.on_hover = _hover
    return btn


def build_bottom_nav(
    selected_key: str,
    on_select,
    on_open_ai_chat=None,
) -> ft.Container:
    left_items = NAV_ITEMS[:2]
    right_items = NAV_ITEMS[2:]

    left_controls = [
        _nav_button(key, label, icon, sel_icon, selected_key, on_select)
        for key, label, icon, sel_icon in left_items
    ]
    right_controls = [
        _nav_button(key, label, icon, sel_icon, selected_key, on_select)
        for key, label, icon, sel_icon in right_items
    ]

    center = (
        ft.Container(
            width=64,
            alignment=CENTER,
            content=_ai_center_button(on_open_ai_chat),
        )
        if on_open_ai_chat
        else ft.Container(width=0)
    )

    return ft.Container(
        height=BOTTOM_NAV_HEIGHT,
        bgcolor=APP_COLORS["surface"],
        border=border_top(APP_COLORS["stroke2"]),
        padding=ft.Padding(left=4, top=0, right=4, bottom=max(4, BOTTOM_NAV_SAFE_GAP // 2)),
        content=ft.Row(
            spacing=0,
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[*left_controls, center, *right_controls],
        ),
    )
