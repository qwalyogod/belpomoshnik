import flet as ft

from components.cards import app_card, badge, icon_circle, page_heading
from components.layout import desktop_content
from data.mock_data import ACHIEVEMENTS, LEARNING_CATEGORIES, LEARNING_STATS
from theme.app_theme import APP_COLORS


def _stat_card(label: str, value: str, icon) -> ft.Container:
    return app_card(
        ft.Row(
            spacing=14,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                icon_circle(icon, color=APP_COLORS["primary"], bgcolor=APP_COLORS["primary_light"], size=46),
                ft.Column(
                    spacing=3,
                    expand=True,
                    controls=[
                        ft.Text(value, size=24, weight=ft.FontWeight.BOLD, color=APP_COLORS["text"]),
                        ft.Text(label, size=13, color=APP_COLORS["muted"]),
                    ],
                ),
            ],
        ),
        padding=16,
    )


def _category_progress(item: dict) -> ft.Container:
    value = item["progress"] / 100
    return app_card(
        ft.Column(
            spacing=10,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(item["name"], size=15, weight=ft.FontWeight.W_600, color=APP_COLORS["text"]),
                        ft.Text(f"{item['progress']}%", size=13, weight=ft.FontWeight.BOLD, color=APP_COLORS["muted"]),
                    ],
                ),
                ft.ProgressBar(value=value, bar_height=8, border_radius=10, color=APP_COLORS["primary"], bgcolor=APP_COLORS["border_soft"]),
            ],
        ),
        padding=16,
    )


def _achievement_card(achievement: dict) -> ft.Container:
    earned = achievement.get("earned", False)
    return app_card(
        ft.Row(
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                icon_circle(
                    ft.Icons.EMOJI_EVENTS_OUTLINED,
                    color=APP_COLORS["primary"] if earned else APP_COLORS["muted"],
                    bgcolor=APP_COLORS["primary_light"] if earned else APP_COLORS["surface_alt"],
                    size=42,
                ),
                ft.Column(
                    spacing=5,
                    expand=True,
                    controls=[
                        ft.Row(
                            spacing=8,
                            controls=[
                                ft.Text(achievement["title"], size=15, weight=ft.FontWeight.BOLD, color=APP_COLORS["text"], expand=True),
                                badge("Получено" if earned else "TODO", "success" if earned else "default"),
                            ],
                        ),
                        ft.Text(achievement["desc"], size=12, color=APP_COLORS["muted"]),
                    ],
                ),
            ],
        ),
        padding=14,
    )


def _learning_content() -> ft.Column:
    return ft.Column(
        spacing=20,
        controls=[
            page_heading("Обучение", "Это дополнительный режим, который помогает закрепить знания по жизненным ситуациям."),
            ft.ResponsiveRow(
                columns=12,
                spacing=12,
                run_spacing=12,
                controls=[
                    ft.Container(col={"xs": 12, "sm": 4}, content=_stat_card("Прочитано материалов", str(LEARNING_STATS["read_materials"]), ft.Icons.MENU_BOOK_OUTLINED)),
                    ft.Container(col={"xs": 12, "sm": 4}, content=_stat_card("Пройдено тестов", str(LEARNING_STATS["completed_tests"]), ft.Icons.QUIZ_OUTLINED)),
                    ft.Container(col={"xs": 12, "sm": 4}, content=_stat_card("Средний результат", LEARNING_STATS["average_score"], ft.Icons.INSIGHTS_OUTLINED)),
                ],
            ),
            ft.Text("Прогресс по категориям", size=22, weight=ft.FontWeight.BOLD, color=APP_COLORS["text"]),
            ft.ResponsiveRow(
                columns=12,
                spacing=12,
                run_spacing=12,
                controls=[
                    ft.Container(col={"xs": 12, "sm": 6}, content=_category_progress(item))
                    for item in LEARNING_CATEGORIES
                ],
            ),
            ft.Text("Достижения", size=22, weight=ft.FontWeight.BOLD, color=APP_COLORS["text"]),
            ft.ResponsiveRow(
                columns=12,
                spacing=12,
                run_spacing=12,
                controls=[
                    ft.Container(col={"xs": 12, "sm": 6}, content=_achievement_card(achievement))
                    for achievement in ACHIEVEMENTS
                ],
            ),
        ],
    )


def build_learning_progress_page(is_desktop: bool = False) -> ft.Control:
    content = _learning_content()
    return desktop_content(content, width=900, top=54) if is_desktop else content
