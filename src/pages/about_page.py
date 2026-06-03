import flet as ft

from components.buttons import secondary_button
from components.cards import app_card, badge, hint_card, page_heading
from components.layout import desktop_content
from data.mock_data import CONTENT_DISCLAIMER
from theme.app_theme import APP_COLORS, ts


IMPLEMENTED_FEATURES = [
    "каталог жизненных сценариев",
    "создание личной ситуации из шаблона",
    "задачи, документы и прогресс",
    "локальное хранение и backup",
    "дашборд пользователя",
    "уведомления по задачам",
    "профиль и обучающий модуль",
    "базовая админ-панель",
]

PLANNED_FEATURES = [
    "полное подключение мобильного приложения к API",
    "production-авторизация и роли",
    "расширенная админ-панель",
    "проверенные юридические источники для всех сценариев",
    "реальные push-уведомления",
    "сборки Android и iOS",
]


def _bullet_list(items: list[str]) -> ft.Column:
    return ft.Column(
        spacing=9,
        controls=[
            ft.Row(
                spacing=9,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, size=ts(18), color=APP_COLORS["primary"]),
                    ft.Text(item, size=ts(14), color=APP_COLORS["text"], expand=True),
                ],
            )
            for item in items
        ],
    )


def _content(go_back=None, is_desktop: bool = False) -> ft.Column:
    return ft.Column(
        spacing=18,
        controls=[
            ft.Row(
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=APP_COLORS["muted"], on_click=go_back),
                    ft.Container(expand=True, content=page_heading("О приложении", "Beta-версия.")),
                ],
            ),
            app_card(
                ft.Column(
                    spacing=14,
                    controls=[
                        ft.Row(
                            wrap=True,
                            spacing=8,
                            run_spacing=8,
                            controls=[badge("Белпомощник", "success"), badge("0.1 beta", "blue")],
                        ),
                        ft.Text(
                            "Белпомощник",
                            size=ts(30) if is_desktop else 26,
                            weight=ft.FontWeight.BOLD,
                            color=APP_COLORS["text"],
                        ),
                        ft.Text(
                            "Мобильное приложение для жителей Республики Беларусь, которое помогает пройти жизненную ситуацию пошагово: от выбора сценария до задач, документов, сроков и прогресса.",
                            size=ts(15),
                            color=APP_COLORS["muted"],
                        ),
                    ],
                ),
                padding=20,
            ),
            app_card(
                ft.Column(
                    spacing=12,
                    controls=[
                        ft.Text("Для кого", size=ts(20), weight=ft.FontWeight.BOLD, color=APP_COLORS["text"]),
                        ft.Text(
                            "Для граждан, которым нужно быстро понять порядок действий в бытовых и административных ситуациях: документы, семья, работа, жильё, налоги и социальная поддержка.",
                            size=ts(14),
                            color=APP_COLORS["muted"],
                        ),
                    ],
                ),
                padding=18,
            ),
            app_card(
                ft.Column(
                    spacing=12,
                    controls=[
                        ft.Text("Что уже реализовано", size=ts(20), weight=ft.FontWeight.BOLD, color=APP_COLORS["text"]),
                        _bullet_list(IMPLEMENTED_FEATURES),
                    ],
                ),
                padding=18,
            ),
            app_card(
                ft.Column(
                    spacing=12,
                    controls=[
                        ft.Text("Что будет добавлено позже", size=ts(20), weight=ft.FontWeight.BOLD, color=APP_COLORS["text"]),
                        _bullet_list(PLANNED_FEATURES),
                    ],
                ),
                padding=18,
            ),
            hint_card(CONTENT_DISCLAIMER, ft.Icons.INFO_OUTLINE),
            secondary_button("Назад", icon=ft.Icons.ARROW_BACK, on_click=go_back, expand=True),
        ],
    )


def build_about_page(go_back=None, is_desktop: bool = False) -> ft.Control:
    content = _content(go_back, is_desktop)
    return desktop_content(content, width=820, top=54) if is_desktop else content
