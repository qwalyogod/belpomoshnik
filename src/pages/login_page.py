from __future__ import annotations

import flet as ft

from components.auth_forms import (
    AUTH_CARD_WIDTH,
    auth_logo,
    auth_shell,
    auth_tabs,
    auth_text_field,
    form_footer,
    oauth_divider,
    oauth_row,
    set_field_error,
)
from components.buttons import primary_button
from components.cards import app_card, hint_card
from theme.app_theme import APP_COLORS, SPACING, ts


def _login_card(is_desktop: bool, on_login=None, go_to=None, on_oauth=None) -> ft.Container:
    email_field = auth_text_field(
        "Email",
        value="ivan@example.by",
        hint="ivan@example.by",
        prefix_icon=ft.Icons.MAIL_OUTLINE,
        keyboard_type=ft.KeyboardType.EMAIL,
    )
    password_field = auth_text_field(
        "Пароль",
        value="123456",
        prefix_icon=ft.Icons.LOCK_OUTLINE,
        password=True,
    )
    remember = ft.Checkbox(
        label="Запомнить",
        value=True,
        active_color=APP_COLORS["blue"],
        check_color=ft.Colors.WHITE,
        label_style=ft.TextStyle(size=ts(14), color=APP_COLORS["muted"], weight=ft.FontWeight.W_700),
    )

    def clear_email_error(_=None) -> None:
        set_field_error(email_field, None)

    def clear_password_error(_=None) -> None:
        set_field_error(password_field, None)

    email_field.on_change = clear_email_error
    password_field.on_change = clear_password_error

    def submit(_=None) -> None:
        email = (email_field.value or "").strip()
        password = password_field.value or ""
        email_error = None
        password_error = None
        if "@" not in email:
            email_error = "Введите корректный email."
        if not password:
            password_error = "Введите пароль."
        set_field_error(email_field, email_error)
        set_field_error(password_field, password_error)
        if email_error or password_error:
            return
        if on_login:
            on_login(email, password, bool(remember.value))

    password_field.on_submit = submit

    controls: list[ft.Control] = [
        auth_logo(),
        auth_tabs("login", go_to),
        ft.Column(
            spacing=6,
            controls=[
                ft.Text("Войти в аккаунт", size=ts(28), weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                ft.Text(
                    "Продолжите работу с планами, задачами и сохранёнными документами.",
                    size=ts(14),
                    color=APP_COLORS["muted"],
                ),
            ],
        ),
        email_field,
        password_field,
        ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                remember,
                ft.Text("Забыли?", size=ts(14), weight=ft.FontWeight.W_900, color=APP_COLORS["blue_text"]),
            ],
        ),
        primary_button("Войти", icon=ft.Icons.LOGIN_ROUNDED, on_click=submit, expand=True),
        oauth_divider(),
        oauth_row(on_oauth),
        form_footer("Нет аккаунта?", "Создать аккаунт", "/register", go_to),
        hint_card("Демо-доступ: ivan@example.by / 123456", icon=ft.Icons.INFO_OUTLINE),
    ]
    return app_card(
        ft.Column(
            spacing=18,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=controls,
        ),
        padding=SPACING["xl"] if is_desktop else 22,
        width=AUTH_CARD_WIDTH if is_desktop else None,
    )


def build_login_page(is_desktop: bool = False, on_login=None, go_to=None, on_oauth=None, page=None) -> ft.Control:
    card = _login_card(is_desktop, on_login, go_to, on_oauth)
    return auth_shell(
        card,
        is_desktop=is_desktop,
        title="Входите, чтобы сохранить личные ситуации и сроки",
        subtitle="Личный кабинет хранит планы, задачи, документы и показывает только важные напоминания.",
        page=page,
    )
