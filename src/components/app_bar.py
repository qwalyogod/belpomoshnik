import flet as ft

from theme.app_theme import APP_COLORS, CENTER, border_bottom, padding_only, ts


def build_app_bar(title: str) -> ft.Container:
    return ft.Container(
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Row(
                    spacing=10,
                    expand=True,
                    controls=[
                        ft.Container(
                            width=38,
                            height=38,
                            border_radius=12,
                            bgcolor=APP_COLORS["blue"],
                            content=ft.Icon(ft.Icons.HEALTH_AND_SAFETY_OUTLINED, color=ft.Colors.WHITE, size=ts(22)),
                            alignment=CENTER,
                        ),
                        ft.Text(title, size=ts(21), weight=ft.FontWeight.BOLD, color=APP_COLORS["text"], expand=True, max_lines=2),
                    ],
                ),
                ft.IconButton(
                    icon=ft.Icons.NOTIFICATIONS_NONE_OUTLINED,
                    icon_color=APP_COLORS["blue"],
                    tooltip="Уведомления",
                    width=44,
                    height=44,
                ),
            ],
        ),
        padding=padding_only(left=18, right=10, top=12, bottom=10),
        bgcolor=APP_COLORS["screen"],
        border=border_bottom(APP_COLORS["stroke2"]),
    )
