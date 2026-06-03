"""
Standalone-страница «Настройки».

Использует уже существующие компоненты _settings_card и _reminders_card
из profile_page для DRY. Полная страница уровня /settings: основные
настройки интерфейса, темы, режима обучения, напоминаний.
"""
from __future__ import annotations

import flet as ft

from components.cards import page_heading
from components.layout import desktop_content
from pages.profile_page import _reminders_card, _settings_card
from theme.app_theme import APP_COLORS, padding_symmetric, ts


def build_settings_page(
    settings: dict | None = None,
    on_setting_change=None,
    is_desktop: bool = False,
    go_back=None,
) -> ft.Control:
    settings = settings or {}

    back_button = ft.IconButton(
        icon=ft.Icons.ARROW_BACK,
        icon_color=APP_COLORS["muted"],
        on_click=go_back,
        tooltip="Назад",
    ) if go_back else ft.Container(width=0)

    header = ft.Row(
        spacing=10,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            back_button,
            ft.Container(
                expand=True,
                content=page_heading("Настройки", "Управление интерфейсом, темой и уведомлениями."),
            ),
        ],
    )

    cards = ft.Column(
        spacing=18,
        controls=[
            _settings_card(settings, on_setting_change, desktop=is_desktop),
            _reminders_card(settings, on_setting_change, desktop=is_desktop),
        ],
    )

    if is_desktop:
        return desktop_content(
            ft.Column(spacing=22, controls=[header, cards]),
            width=900,
            top=40,
        )
    return ft.Container(
        padding=padding_symmetric(horizontal=16, vertical=22),
        content=ft.Column(spacing=18, controls=[header, cards]),
    )
