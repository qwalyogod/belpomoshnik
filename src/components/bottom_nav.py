import flet as ft

from theme.app_theme import APP_COLORS, BOTTOM_NAV_HEIGHT, BOTTOM_NAV_SAFE_GAP, CENTER, border_top


NAV_ITEMS = [
    ("home", "Главная", ft.Icons.HOME_OUTLINED, ft.Icons.HOME),
    ("problems", "Проблемы", ft.Icons.ARTICLE_OUTLINED, ft.Icons.ARTICLE),
    ("situations", "Ситуации", ft.Icons.TASK_ALT_OUTLINED, ft.Icons.TASK_ALT),
    ("documents", "Док-ты", ft.Icons.DESCRIPTION_OUTLINED, ft.Icons.DESCRIPTION),
    ("profile", "Профиль", ft.Icons.PERSON_OUTLINE, ft.Icons.PERSON),
]


def _nav_button(key: str, label: str, icon, selected_icon, selected_key: str, on_select) -> ft.Container:
    selected = key == selected_key
    label_color = APP_COLORS["text"] if selected else APP_COLORS["muted"]
    return ft.Container(
        expand=True,
        ink=True,
        on_click=lambda _: on_select(key),
        padding=ft.Padding(left=0, top=6, right=0, bottom=4),
        content=ft.Column(
            spacing=2,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    width=40,
                    height=28,
                    border_radius=999,
                    bgcolor=APP_COLORS["primary_light"] if selected else None,
                    alignment=CENTER,
                    content=ft.Icon(
                        selected_icon if selected else icon,
                        size=22,
                        color=label_color,
                    ),
                ),
                ft.Text(
                    label,
                    size=9,
                    weight=ft.FontWeight.W_600,
                    color=label_color,
                    text_align=ft.TextAlign.CENTER,
                    max_lines=1,
                    no_wrap=True,
                ),
            ],
        ),
    )


def build_bottom_nav(selected_key: str, on_select) -> ft.Container:
    return ft.Container(
        width=340,
        height=BOTTOM_NAV_HEIGHT,
        bgcolor=APP_COLORS["surface"],
        border=border_top(APP_COLORS["stroke2"]),
        padding=ft.Padding(left=6, top=4, right=6, bottom=max(6, BOTTOM_NAV_SAFE_GAP // 2)),
        content=ft.Row(
            spacing=8,
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                _nav_button(key, label, icon, selected_icon, selected_key, on_select)
                for key, label, icon, selected_icon in NAV_ITEMS
            ],
        ),
    )
