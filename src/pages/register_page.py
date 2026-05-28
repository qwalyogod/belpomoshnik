from __future__ import annotations

import flet as ft

from components.auth_forms import (
    AUTH_CARD_WIDTH,
    auth_logo,
    auth_shell,
    auth_tabs,
    auth_text_field,
    form_footer,
    set_field_error,
)
from components.buttons import primary_button
from components.cards import app_card, hint_card
from theme.app_theme import APP_COLORS, SPACING


def _register_card(is_desktop: bool, on_register=None, go_to=None) -> ft.Container:
    name_field = auth_text_field("Имя и фамилия", hint="Анна Петрова", prefix_icon=ft.Icons.PERSON_OUTLINE)
    email_field = auth_text_field(
        "Email",
        hint="name@example.by",
        prefix_icon=ft.Icons.MAIL_OUTLINE,
        keyboard_type=ft.KeyboardType.EMAIL,
    )
    city_field = auth_text_field("Город", value="Минск", prefix_icon=ft.Icons.LOCATION_CITY_OUTLINED)
    region_field = auth_text_field("Регион", value="Минская область", prefix_icon=ft.Icons.MAP_OUTLINED)
    password_field = auth_text_field("Пароль", prefix_icon=ft.Icons.LOCK_OUTLINE, password=True)
    confirm_field = auth_text_field("Повторите пароль", prefix_icon=ft.Icons.LOCK_RESET_OUTLINED, password=True)
    terms = ft.Checkbox(
        label="Согласен с условиями демо-MVP",
        value=True,
        active_color=APP_COLORS["blue"],
        check_color=ft.Colors.WHITE,
        label_style=ft.TextStyle(size=14, color=APP_COLORS["muted"], weight=ft.FontWeight.W_700),
    )
    terms_error = ft.Text("", size=12, color=APP_COLORS["red"], weight=ft.FontWeight.W_600, visible=False)

    fields = [name_field, email_field, city_field, region_field, password_field, confirm_field]

    def clear_errors(_=None) -> None:
        for field in fields:
            set_field_error(field, None)
        terms_error.visible = False
        if terms_error.page:
            terms_error.update()

    for field in fields:
        field.on_change = clear_errors
    terms.on_change = clear_errors

    def submit(_=None) -> None:
        name = (name_field.value or "").strip()
        email = (email_field.value or "").strip()
        city = (city_field.value or "").strip()
        region = (region_field.value or "").strip()
        password = password_field.value or ""
        confirm = confirm_field.value or ""
        errors = [
            (name_field, "Введите имя и фамилию." if len(name) < 2 else None),
            (email_field, "Введите корректный email." if "@" not in email else None),
            (city_field, "Укажите город." if not city else None),
            (region_field, "Укажите регион." if not region else None),
            (password_field, "Пароль должен быть не короче 6 символов." if len(password) < 6 else None),
            (confirm_field, "Пароли не совпадают." if password != confirm else None),
        ]
        has_error = False
        for field, message in errors:
            set_field_error(field, message)
            has_error = has_error or bool(message)
        if not terms.value:
            terms_error.value = "Подтвердите условия демо-профиля."
            terms_error.visible = True
            has_error = True
        else:
            terms_error.visible = False
        if terms_error.page:
            terms_error.update()
        if has_error:
            return
        if on_register:
            on_register(name, email, city, region, password, confirm, bool(terms.value))

    confirm_field.on_submit = submit

    location_controls: ft.Control
    if is_desktop:
        location_controls = ft.Row(
            spacing=10,
            controls=[
                ft.Container(content=region_field, expand=True),
                ft.Container(content=city_field, expand=True),
            ],
        )
    else:
        location_controls = ft.Column(spacing=10, controls=[region_field, city_field])

    controls: list[ft.Control] = [
        auth_logo(),
        auth_tabs("register", go_to),
        ft.Column(
            spacing=6,
            controls=[
                ft.Text("Создать аккаунт", size=28, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                ft.Text(
                    "Укажите минимум данных, чтобы подсказки были релевантными.",
                    size=14,
                    color=APP_COLORS["muted"],
                ),
            ],
        ),
        name_field,
        email_field,
        location_controls,
        password_field,
        confirm_field,
        ft.Column(spacing=0, controls=[terms, terms_error]),
        primary_button("Создать аккаунт", icon=ft.Icons.PERSON_ADD_ALT_1_OUTLINED, on_click=submit, expand=True),
        form_footer("Уже есть аккаунт?", "Войти", "/login", go_to),
        hint_card("Данные сохраняются локально в демо-версии. Production потребует серверной защиты.", icon=ft.Icons.SHIELD_OUTLINED),
    ]
    return app_card(
        ft.Column(
            spacing=14,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=controls,
        ),
        padding=SPACING["xl"] if is_desktop else 22,
        width=AUTH_CARD_WIDTH if is_desktop else None,
    )


def build_register_page(is_desktop: bool = False, on_register=None, go_to=None) -> ft.Control:
    card = _register_card(is_desktop, on_register, go_to)
    return auth_shell(
        card,
        is_desktop=is_desktop,
        title="Создайте профиль, чтобы получать персональные подсказки",
        subtitle="Регион и город нужны для учреждений, сроков и релевантных закон-апдейтов.",
    )
