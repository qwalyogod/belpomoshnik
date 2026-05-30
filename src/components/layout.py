import flet as ft

from data.mock_data import MOCK_USER
from theme.app_theme import (
    AI_CHAT_PANEL_WIDTH,
    ANIM_PAGE,
    APP_COLORS,
    BOTTOM_NAV_SAFE_GAP,
    DEBUG_LAYOUT,
    FLOATING_ACTION_BOTTOM_PADDING,
    IOS_SAFE_BOTTOM_FALLBACK,
    IOS_SAFE_TOP_FALLBACK,
    PAGE_BOTTOM_PADDING,
    PAGE_HORIZONTAL_PADDING,
    PAGE_TOP_PADDING,
    CENTER,
    border_all,
    border_bottom,
    border_top,
    padding_symmetric,
)


TOP_NAV = [
    ("home", "Главная", "/"),
    ("problems", "Проблемы", "/problems"),
    ("scenarios", "Сценарии", "/scenarios"),
    ("situations", "Мои ситуации", "/situations"),
    ("documents", "Документы", "/documents"),
    ("laws", "Законы", "/legal-updates"),
]


def _debug_border() -> ft.Border | None:
    return border_all(APP_COLORS["danger"]) if DEBUG_LAYOUT else None


def iphone_page_container(
    content: ft.Control,
    *,
    include_bottom_nav: bool = True,
    top_padding: int = PAGE_TOP_PADDING,
) -> ft.Container:
    """Common iPhone content padding: no hard width, no horizontal overflow."""
    bottom_padding = PAGE_BOTTOM_PADDING + (BOTTOM_NAV_SAFE_GAP if include_bottom_nav else FLOATING_ACTION_BOTTOM_PADDING)
    return ft.Container(
        content=content,
        expand=True,
        bgcolor=APP_COLORS["screen"],
        padding=ft.Padding(
            left=PAGE_HORIZONTAL_PADDING,
            top=top_padding,
            right=PAGE_HORIZONTAL_PADDING,
            bottom=bottom_padding,
        ),
        border=_debug_border(),
    )


def scrollable_mobile_page(content: ft.Control, *, include_bottom_nav: bool = True) -> ft.Container:
    return iphone_page_container(
        ft.Column(
            controls=[content],
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        ),
        include_bottom_nav=include_bottom_nav,
    )


def app_safe_area(content: ft.Control, *, expand: bool = True, include_bottom: bool = True) -> ft.SafeArea:
    return ft.SafeArea(
        content=content,
        expand=expand,
        avoid_intrusions_top=True,
        avoid_intrusions_left=True,
        avoid_intrusions_right=True,
        avoid_intrusions_bottom=include_bottom,
        minimum_padding=ft.Padding(
            left=0,
            top=IOS_SAFE_TOP_FALLBACK,
            right=0,
            bottom=IOS_SAFE_BOTTOM_FALLBACK if include_bottom else 0,
        ),
    )


def bottom_nav_safe_area(content: ft.Control) -> ft.SafeArea:
    return ft.SafeArea(
        content=content,
        avoid_intrusions_top=False,
        avoid_intrusions_left=True,
        avoid_intrusions_right=True,
        avoid_intrusions_bottom=True,
        minimum_padding=ft.Padding(left=0, top=0, right=0, bottom=IOS_SAFE_BOTTOM_FALLBACK),
    )


def mobile_page_layout(content: ft.Control, *, include_bottom_nav: bool = True) -> ft.SafeArea:
    return app_safe_area(
        scrollable_mobile_page(content, include_bottom_nav=include_bottom_nav),
        include_bottom=not include_bottom_nav,
    )


def desktop_content(content: ft.Control, width: int = 1120, top: int = 54, bottom: int = 80) -> ft.Row:
    return ft.Row(
        alignment=ft.MainAxisAlignment.CENTER,
        vertical_alignment=ft.CrossAxisAlignment.START,
        controls=[
            ft.Container(
                width=width,
                padding=ft.Padding(left=0, top=top, right=0, bottom=bottom),
                content=content,
            )
        ],
    )


def _logo() -> ft.Row:
    return ft.Row(
        spacing=10,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(
                width=34,
                height=34,
                border_radius=10,
                bgcolor=APP_COLORS["blue"],
                alignment=CENTER,
                content=ft.Text("Б", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            ),
            ft.Text("Белпомощник", size=20, weight=ft.FontWeight.BOLD, color=APP_COLORS["blue_text"]),
        ],
    )


def _nav_item(label: str, route: str, active: bool, go_to) -> ft.Container:
    return ft.Container(
        content=ft.Text(
            label,
            size=14,
            weight=ft.FontWeight.W_600,
            color=APP_COLORS["blue_text"] if active else APP_COLORS["muted"],
        ),
        padding=padding_symmetric(horizontal=18, vertical=10),
        border_radius=10,
        bgcolor=APP_COLORS["active"] if active else None,
        on_click=lambda _: go_to(route),
        ink=True,
    )


def build_desktop_header(active_key: str, go_to, width: int = 1320) -> ft.Container:
    return ft.Container(
        height=78,
        bgcolor=APP_COLORS["surface"],
        border=border_bottom(APP_COLORS["stroke2"]),
        shadow=[
            ft.BoxShadow(
                blur_radius=6,
                spread_radius=0,
                color=ft.Colors.with_opacity(0.04, APP_COLORS["text"]),
                offset=ft.Offset(0, 2),
            )
        ],
        content=ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    width=width,
                    height=78,
                    padding=ft.Padding(left=0, top=0, right=0, bottom=0),
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Row(
                                spacing=48,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Container(content=_logo(), on_click=lambda _: go_to("/"), ink=True),
                                    ft.Row(
                                        spacing=8,
                                        controls=[
                                            _nav_item(label, route, key == active_key, go_to)
                                            for key, label, route in TOP_NAV
                                        ],
                                    ),
                                ],
                            ),
                            ft.Row(
                                spacing=22,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Container(
                                        width=40,
                                        height=40,
                                        border_radius=20,
                                        ink=True,
                                        on_click=lambda _: go_to("/notifications"),
                                        alignment=ft.Alignment(0, 0),
                                        content=ft.Stack(
                                            width=34,
                                            height=34,
                                            controls=[
                                                ft.Icon(ft.Icons.NOTIFICATIONS_NONE_OUTLINED, size=24, color=APP_COLORS["muted"]),
                                                ft.Container(width=7, height=7, border_radius=4, bgcolor=APP_COLORS["danger"], right=2, top=2),
                                            ],
                                        ),
                                    ),
                                    ft.Container(width=1, height=32, bgcolor=APP_COLORS["stroke2"]),
                                    ft.Container(
                                        on_click=lambda _: go_to("/profile"),
                                        ink=True,
                                        content=ft.Row(
                                            spacing=12,
                                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                            controls=[
                                                ft.Column(
                                                    spacing=0,
                                                    horizontal_alignment=ft.CrossAxisAlignment.END,
                                                    controls=[
                                                        ft.Text(MOCK_USER["name"], size=14, weight=ft.FontWeight.BOLD, color=APP_COLORS["text"]),
                                                        ft.Text("Профиль", size=12, color=APP_COLORS["muted"]),
                                                    ],
                                                ),
                                                avatar(radius=19),
                                            ],
                                        ),
                                    ),
                                ],
                            ),
                        ],
                    ),
                )
            ],
        ),
    )


def build_desktop_footer(go_to, width: int = 1120) -> ft.Container:
    return ft.Container(
        height=88,
        bgcolor=APP_COLORS["surface"],
        border=border_top(APP_COLORS["stroke2"]),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    width=width,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text("© 2026 Белпомощник. Информационная система для граждан РБ.", size=13, color=APP_COLORS["muted"]),
                            ft.Row(
                                spacing=22,
                                controls=[
                                    ft.TextButton("Админ-панель", on_click=lambda _: go_to("/admin"), style=ft.ButtonStyle(color=APP_COLORS["muted"])),
                                    ft.TextButton("О проекте", on_click=lambda _: go_to("/about"), style=ft.ButtonStyle(color=APP_COLORS["muted"])),
                                ],
                            ),
                        ],
                    ),
                )
            ],
        ),
    )


def app_shell(
    content: ft.Control,
    *,
    active_key: str,
    go_to,
    on_nav_change,
    is_desktop: bool,
    on_toggle_theme=None,
    theme_mode: str = "light",
    user: dict | None = None,
) -> ft.Control:
    """Redesign shell foundation: sidebar on desktop, topbar + bottom nav on mobile."""
    if is_desktop:
        from components.sidebar import build_sidebar

        return ft.Row(
            expand=True,
            spacing=0,
            controls=[
                build_sidebar(active_key, go_to, on_toggle_theme, theme_mode, user or MOCK_USER),
                ft.Container(
                    expand=True,
                    bgcolor=APP_COLORS["screen"],
                    content=ft.Column(
                        expand=True,
                        scroll=ft.ScrollMode.AUTO,
                        controls=[content],
                    ),
                ),
            ],
        )

    from components.mobile_topbar import build_mobile_topbar
    from components.bottom_nav import build_bottom_nav

    return ft.Column(
        expand=True,
        spacing=0,
        controls=[
            build_mobile_topbar("Белпомощник", go_to=go_to, user=user or MOCK_USER),
            mobile_page_layout(content, include_bottom_nav=True),
            bottom_nav_safe_area(build_bottom_nav(active_key, on_nav_change)),
        ],
    )


def avatar(radius: int = 20) -> ft.CircleAvatar:
    image_src = MOCK_USER.get("avatar_url")
    return ft.CircleAvatar(
        radius=radius,
        background_image_src=image_src,
        content=None if image_src else ft.Text("ИИ", size=max(10, radius - 4), weight=ft.FontWeight.BOLD),
        bgcolor=APP_COLORS["active"],
        color=APP_COLORS["blue_text"],
    )
