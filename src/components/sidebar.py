from __future__ import annotations

import flet as ft

from components.layout import avatar
from theme.app_theme import (
    APP_COLORS,
    ANIM_FAST,
    CENTER,
    SIDEBAR_WIDTH_DESKTOP,
    SIDEBAR_WIDTH_TABLET,
    border_all,
    border_top,
    padding_symmetric,
    ts,
)


_PRODUCT_ITEMS = [
    ("home", "Главная", ft.Icons.HOME_OUTLINED, "/"),
    ("problems", "Каталог", ft.Icons.SEARCH_OUTLINED, "/problems"),
    ("scenarios", "Сценарии", ft.Icons.ROUTE_OUTLINED, "/scenarios"),
    ("situations", "Мои ситуации", ft.Icons.TASK_ALT_OUTLINED, "/situations"),
    ("documents", "Документы", ft.Icons.ARTICLE_OUTLINED, "/documents"),
    ("notifications", "Уведомления", ft.Icons.NOTIFICATIONS_NONE_OUTLINED, "/notifications"),
    ("laws", "Новости", ft.Icons.NEWSPAPER_OUTLINED, "/legal-updates"),
]

_BASE_SERVICE_ITEMS = [
    ("utility", "ЖКХ-трекер", ft.Icons.HOME_WORK_OUTLINED, "/utility"),
    ("taxes", "Налоговый трекер", ft.Icons.RECEIPT_LONG_OUTLINED, "/taxes"),
    ("learning", "Обучение", ft.Icons.SCHOOL_OUTLINED, "/learning"),
]

_EDITOR_ITEM = ("admin", "Редакторская", ft.Icons.EDIT_NOTE_OUTLINED, "/admin")
_ADMIN_ITEM = ("admin", "Администрирование", ft.Icons.ADMIN_PANEL_SETTINGS_OUTLINED, "/admin")


def _service_items_for(role: str) -> list[tuple]:
    """Возвращает список сервисных пунктов sidebar в зависимости от роли."""
    items = list(_BASE_SERVICE_ITEMS)
    if role == "platform_admin":
        items.append(_ADMIN_ITEM)
    elif role == "content_editor":
        items.append(_EDITOR_ITEM)
    return items


# All items combined (for compatibility — default to citizen view, no admin item).
SIDEBAR_ITEMS = _PRODUCT_ITEMS + _BASE_SERVICE_ITEMS


def _section_label(text: str) -> ft.Container:
    return ft.Container(
        padding=ft.Padding(left=12, top=10, right=0, bottom=4),
        content=ft.Text(
            text,
            size=10,
            weight=ft.FontWeight.W_700,
            color=APP_COLORS["muted2"],
        ),
    )


def _sidebar_item(
    key: str,
    label: str,
    icon,
    route: str,
    active_key: str,
    go_to,
    *,
    tablet: bool = False,
    notification_count: int = 0,
) -> ft.Container:
    active = key == active_key
    icon_size = SIDEBAR_WIDTH_TABLET if tablet else SIDEBAR_WIDTH_DESKTOP
    icon_box_size = 30 if tablet else 32

    badge_control: list[ft.Control] = []
    if notification_count > 0:
        badge_control = [
            ft.Container(
                width=18, height=18, border_radius=9,
                bgcolor=APP_COLORS["blue"],
                alignment=CENTER,
                content=ft.Text(str(notification_count), size=ts(10), weight=ft.FontWeight.W_800, color=ft.Colors.WHITE),
            )
        ]

    container = ft.Container(
        ink=True,
        on_click=lambda _: go_to(route),
        border_radius=12,
        padding=ft.Padding(left=10, top=9, right=10, bottom=9),
        bgcolor=APP_COLORS["active"] if active else None,
        animate=ft.Animation(ANIM_FAST, ft.AnimationCurve.EASE_OUT),
        content=ft.Row(
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    width=icon_box_size, height=icon_box_size,
                    border_radius=icon_box_size // 2,
                    bgcolor=APP_COLORS["blue"] if active else APP_COLORS["surface2"],
                    alignment=CENTER,
                    animate=ft.Animation(ANIM_FAST, ft.AnimationCurve.EASE_OUT),
                    content=ft.Icon(
                        icon,
                        size=16,
                        color=ft.Colors.WHITE if active else APP_COLORS["muted"],
                    ),
                ),
                ft.Text(
                    label,
                    size=13 if tablet else 14,
                    weight=ft.FontWeight.W_700 if active else ft.FontWeight.W_500,
                    color=APP_COLORS["blue_text"] if active else APP_COLORS["text"],
                    expand=True,
                    max_lines=1,
                    no_wrap=True,
                ),
                *badge_control,
            ],
        ),
    )

    def _on_hover(e: ft.HoverEvent) -> None:
        if not active:
            container.bgcolor = APP_COLORS["surface2"] if e.data == "true" else None
            container.update()

    container.on_hover = _on_hover
    return container


def build_sidebar(
    active_key: str,
    go_to,
    on_toggle_theme=None,
    theme_mode: str = "light",
    user: dict | None = None,
    *,
    tablet: bool = False,
    on_open_ai_chat=None,
    notification_count: int = 0,
    role: str = "citizen",
) -> ft.Container:
    dark_mode = theme_mode == "dark"
    width = SIDEBAR_WIDTH_TABLET if tablet else SIDEBAR_WIDTH_DESKTOP

    # Logo block
    logo_block = ft.Row(
        spacing=10,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(
                width=40, height=40, border_radius=14,
                bgcolor=APP_COLORS["blue"],
                alignment=CENTER,
                content=ft.Text("Б", size=ts(22), weight=ft.FontWeight.W_900, color=ft.Colors.WHITE),
            ),
            ft.Column(
                spacing=1,
                controls=[
                    ft.Text("Белпомощник", size=ts(16) if tablet else 18, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                    ft.Text("личный помощник", size=ts(10), color=APP_COLORS["muted"]),
                ],
            ),
        ],
    )

    # User card
    user_card = ft.Container(
        padding=ft.Padding(left=12, top=10, right=12, bottom=10),
        border_radius=14,
        bgcolor=APP_COLORS["surface2"],
        content=ft.Row(
            spacing=10,
            controls=[
                avatar(radius=18),
                ft.Column(
                    spacing=2,
                    expand=True,
                    controls=[
                        ft.Text(
                            (user or {}).get("name", "Пользователь"),
                            size=13,
                            weight=ft.FontWeight.W_700,
                            color=APP_COLORS["text"],
                            max_lines=1,
                            no_wrap=True,
                        ),
                        ft.Text(
                            (user or {}).get("city", "Минск"),
                            size=11,
                            color=APP_COLORS["muted"],
                        ),
                    ],
                ),
            ],
        ),
    )

    # Nav sections
    product_items = [
        _sidebar_item(
            key, label, icon, route, active_key, go_to,
            tablet=tablet,
            notification_count=notification_count if key == "notifications" else 0,
        )
        for key, label, icon, route in _PRODUCT_ITEMS
    ]
    service_items = [
        _sidebar_item(key, label, icon, route, active_key, go_to, tablet=tablet)
        for key, label, icon, route in _service_items_for(role)
    ]

    # AI chat button
    ai_chat_btn = ft.Container(
        ink=True,
        on_click=on_open_ai_chat,
        border_radius=14,
        padding=ft.Padding(left=10, top=11, right=10, bottom=11),
        bgcolor=APP_COLORS["blue"],
        animate=ft.Animation(ANIM_FAST, ft.AnimationCurve.EASE_OUT),
        content=ft.Row(
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    width=32, height=32, border_radius=16,
                    bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
                    alignment=CENTER,
                    content=ft.Icon(ft.Icons.AUTO_AWESOME_OUTLINED, size=ts(16), color=ft.Colors.WHITE),
                ),
                ft.Column(
                    spacing=1,
                    expand=True,
                    controls=[
                        ft.Text("Спросить агента", size=ts(13), weight=ft.FontWeight.W_700, color=ft.Colors.WHITE),
                        ft.Text("ИИ-помощник, 24/7", size=ts(10), color=ft.Colors.with_opacity(0.75, ft.Colors.WHITE)),
                    ],
                ),
                ft.Icon(ft.Icons.CHAT_BUBBLE_OUTLINE_ROUNDED, size=ts(18), color=ft.Colors.with_opacity(0.75, ft.Colors.WHITE)),
            ],
        ),
    ) if on_open_ai_chat else ft.Container(height=0)

    # Theme toggle
    theme_section = ft.Container(
        padding=ft.Padding(left=10, top=10, right=10, bottom=10),
        border_radius=14,
        bgcolor=APP_COLORS["surface"],
        border=border_all(APP_COLORS["stroke2"]),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Row(
                    spacing=8,
                    controls=[
                        ft.Icon(
                            ft.Icons.DARK_MODE_OUTLINED if dark_mode else ft.Icons.LIGHT_MODE_OUTLINED,
                            size=18,
                            color=APP_COLORS["muted"],
                        ),
                        ft.Text("Тёмная тема", size=ts(13), color=APP_COLORS["muted"]),
                    ],
                ),
                ft.Switch(
                    value=dark_mode,
                    active_color=APP_COLORS["blue"],
                    on_change=on_toggle_theme,
                ),
            ],
        ),
    )

    return ft.Container(
        width=width,
        bgcolor=APP_COLORS["sidebar"],
        border=ft.Border(right=ft.BorderSide(1, APP_COLORS["stroke2"])),
        padding=ft.Padding(left=16, top=22, right=14, bottom=18),
        content=ft.Column(
            expand=True,
            spacing=0,
            controls=[
                logo_block,
                ft.Container(height=14),
                user_card,
                ft.Container(height=6),
                _section_label("ПРОДУКТ"),
                ft.Column(spacing=2, controls=product_items),
                _section_label("СЕРВИСЫ"),
                ft.Column(spacing=2, controls=service_items),
                ft.Container(expand=True),
                ai_chat_btn,
                ft.Container(height=10),
                theme_section,
                ft.Container(height=10),
                ft.Container(
                    border=border_top(APP_COLORS["stroke2"]),
                    padding=ft.Padding(left=2, top=8, right=2, bottom=0),
                    content=ft.Text("v0.1 beta", size=ts(11), color=APP_COLORS["muted2"]),
                ),
            ],
        ),
    )
