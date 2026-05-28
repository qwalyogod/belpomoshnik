from __future__ import annotations

import flet as ft

from components.buttons import ghost_button, primary_button
from components.cards import app_card, badge, icon_circle
from components.layout import desktop_content
from components.placeholders import photo_placeholder
from theme.app_theme import (
    APP_COLORS,
    APP_RADIUS,
    CENTER,
    SPACING,
    border_all,
    padding_symmetric,
)


SLIDES = [
    {
        "title": "Найдите проблему",
        "description": "Опишите ситуацию или выберите готовую категорию.",
        "icon": ft.Icons.SEARCH,
        "badge": "01",
    },
    {
        "title": "Получите план",
        "description": "Белпомощник соберёт шаги, документы, сроки и куда обращаться.",
        "icon": ft.Icons.CHECK,
        "badge": "02",
    },
    {
        "title": "Следите за сроками",
        "description": "Напоминания помогут не пропустить задачи и документы.",
        "icon": ft.Icons.NOTIFICATIONS_ACTIVE_OUTLINED,
        "badge": "03",
    },
    {
        "title": "Ведите прогресс",
        "description": "Отмечайте выполненное и смотрите, как личная ситуация движется к завершению.",
        "icon": ft.Icons.TASK_ALT_OUTLINED,
        "badge": "04",
    },
]

MOBILE_CONTENT_WIDTH = 340


def _logo_row(is_desktop: bool) -> ft.Row:
    logo_size = 42 if is_desktop else 38
    return ft.Row(
        spacing=12,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(
                width=logo_size,
                height=logo_size,
                border_radius=14,
                bgcolor=APP_COLORS["blue"],
                alignment=CENTER,
                content=ft.Icon(ft.Icons.NAVIGATION_ROUNDED, size=24 if is_desktop else 22, color=ft.Colors.WHITE),
            ),
            ft.Text(
                "Белпомощник",
                size=22 if is_desktop else 20,
                weight=ft.FontWeight.W_900,
                color=APP_COLORS["text"],
            ),
        ],
    )


def _search_preview(is_desktop: bool, width: int | None = None) -> ft.Container:
    return ft.Container(
        width=width,
        height=58 if is_desktop else 56,
        border_radius=18,
        bgcolor=APP_COLORS["search"],
        border=border_all(APP_COLORS["stroke2"]),
        padding=padding_symmetric(horizontal=16, vertical=0),
        content=ft.Row(
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(ft.Icons.SEARCH, size=24, color=APP_COLORS["muted"]),
                ft.Text(
                    "Паспорт, ЖКХ, налоги, прописка...",
                    size=15 if is_desktop else 14,
                    color=APP_COLORS["muted2"],
                    expand=True,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
            ],
        ),
    )


def _slide_card(index: int, is_desktop: bool) -> ft.Container:
    item = SLIDES[index]
    return ft.Container(
        key=f"onboarding-slide-{index}",
        content=ft.Row(
            spacing=14,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                icon_circle(item["icon"], color=APP_COLORS["blue"], bgcolor=APP_COLORS["active"], size=50),
                ft.Column(
                    spacing=4,
                    expand=True,
                    controls=[
                        ft.Text(
                            item["title"],
                            size=17 if is_desktop else 16,
                            weight=ft.FontWeight.W_900,
                            color=APP_COLORS["text"],
                        ),
                        ft.Text(
                            item["description"],
                            size=13 if is_desktop else 12,
                            color=APP_COLORS["muted"],
                            max_lines=2,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                    ],
                ),
                ft.Text(item["badge"], size=18, weight=ft.FontWeight.W_900, color=APP_COLORS["muted2"]),
            ],
        ),
        padding=16,
        border_radius=18,
        bgcolor=APP_COLORS["surface"],
        border=border_all(APP_COLORS["stroke2"]),
    )


def _dot(index: int, current: int, on_click) -> ft.Container:
    active = index == current
    return ft.Container(
        width=26 if active else 9,
        height=9,
        border_radius=9,
        bgcolor=APP_COLORS["blue"] if active else APP_COLORS["stroke2"],
        on_click=on_click,
        ink=True,
    )


def _onboarding_steps(is_desktop: bool) -> ft.Column:
    active_index = {"value": 0}
    switcher = ft.AnimatedSwitcher(
        content=_slide_card(0, is_desktop),
        duration=220,
        reverse_duration=220,
        switch_in_curve=ft.AnimationCurve.EASE_OUT,
        switch_out_curve=ft.AnimationCurve.EASE_OUT,
        transition=ft.AnimatedSwitcherTransition.FADE,
    )
    dots = ft.Row(spacing=8, alignment=ft.MainAxisAlignment.CENTER)

    def set_slide(new_index: int) -> None:
        active_index["value"] = new_index % len(SLIDES)
        switcher.content = _slide_card(active_index["value"], is_desktop)
        dots.controls = _dot_controls()
        if switcher.page:
            switcher.update()
        if dots.page:
            dots.update()

    def _dot_controls() -> list[ft.Control]:
        controls: list[ft.Control] = []
        for index in range(len(SLIDES)):
            controls.append(_dot(index, active_index["value"], lambda _, value=index: set_slide(value)))
        return controls

    dots.controls = _dot_controls()

    controls: list[ft.Control] = [
        ft.Container(height=96 if is_desktop else 108, content=switcher),
        ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
            controls=[
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK_ROUNDED,
                    icon_color=APP_COLORS["muted"],
                    tooltip="Предыдущий шаг",
                    on_click=lambda _: set_slide(active_index["value"] - 1),
                ),
                dots,
                ft.IconButton(
                    icon=ft.Icons.ARROW_FORWARD_ROUNDED,
                    icon_color=APP_COLORS["muted"],
                    tooltip="Следующий шаг",
                    on_click=lambda _: set_slide(active_index["value"] + 1),
                ),
            ],
        ),
    ]
    return ft.Column(spacing=8, controls=controls)


def _cta_buttons(on_start, is_desktop: bool) -> ft.Control:
    if is_desktop:
        return ft.Row(
            spacing=12,
            controls=[
                primary_button("Начать", on_click=on_start, width=180),
                ghost_button("У меня уже есть аккаунт", on_click=on_start),
            ],
        )
    return ft.Column(
        spacing=10,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        controls=[
            primary_button("Начать", on_click=on_start, expand=True),
            ft.Container(
                alignment=CENTER,
                content=ghost_button("У меня уже есть аккаунт", on_click=on_start),
            ),
        ],
    )


def _desktop_hero(on_start) -> ft.Container:
    title = "Помощник, который превращает проблему в понятный план"
    description = "Найдите жизненную ситуацию, получите чек-лист, сроки, документы и напоминания без канцелярита."
    content = ft.Column(
        spacing=18,
        controls=[
            _logo_row(True),
            photo_placeholder("персонаж на фоне Минска", height=132),
            badge("mobile-first · РБ", "blue"),
            ft.Text(title, size=40, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
            ft.Text(description, size=17, color=APP_COLORS["muted"]),
            _search_preview(True),
            _onboarding_steps(True),
            _cta_buttons(on_start, True),
        ],
    )
    return app_card(
        content,
        padding=28,
        bgcolor=APP_COLORS["panel"],
        border_color=APP_COLORS["stroke"],
        width=560,
    )


def _mobile_hero(on_start) -> ft.Container:
    title = "Проблема → понятный план"
    description = "Выберите ситуацию, получите шаги, документы и напоминания."
    controls: list[ft.Control] = [
        _logo_row(False),
        photo_placeholder("персонаж на фоне Минска", width=MOBILE_CONTENT_WIDTH, height=148),
        badge("mobile-first · РБ", "blue"),
        ft.Text(title, size=30, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
        ft.Text(description, size=15, color=APP_COLORS["muted"]),
        _search_preview(False, width=MOBILE_CONTENT_WIDTH),
        _cta_buttons(on_start, False),
        _onboarding_steps(False),
    ]
    return ft.Container(
        width=MOBILE_CONTENT_WIDTH,
        content=ft.Column(
            spacing=20,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=controls,
        ),
    )


def build_onboarding_page(on_start=None, is_desktop: bool = False) -> ft.Control:
    if is_desktop:
        return desktop_content(_desktop_hero(on_start), width=620, top=24)
    return _mobile_hero(on_start)
