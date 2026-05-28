"""
I1 — Демо-экран предпросмотра сформированного email-уведомления.

Показывает, как выглядит письмо, которое в production будет отправлено через SMTP.
В MVP отправка недоступна — только визуальный предпросмотр.
"""
from __future__ import annotations

import flet as ft

from components.buttons import ghost_button, primary_button
from components.cards import app_card, icon_circle
from components.layout import desktop_content
from theme.app_theme import APP_COLORS, border_all, padding_symmetric


def _email_header_row(label: str, value: str) -> ft.Row:
    return ft.Row(
        spacing=8,
        controls=[
            ft.Text(label, size=13, color=APP_COLORS["muted"], width=70),
            ft.Text(value, size=13, color=APP_COLORS["text"], expand=True, selectable=True),
        ],
    )


def _email_preview_card(email_data: dict, desktop: bool) -> ft.Control:
    subject = email_data.get("subject", "Уведомление о документах")
    recipient = email_data.get("recipient", "пользователь@example.com")
    body_lines: list[str] = email_data.get("body_lines", [])

    header_block = ft.Container(
        content=ft.Column(
            spacing=6,
            controls=[
                _email_header_row("От:", "noreply@belpomoshnik.by"),
                _email_header_row("Кому:", recipient),
                _email_header_row("Тема:", subject),
            ],
        ),
        padding=padding_symmetric(horizontal=20, vertical=14),
        border=ft.Border(bottom=ft.BorderSide(1, APP_COLORS["border_soft"])),
    )

    body_controls: list[ft.Control] = []
    for line in body_lines:
        if line.startswith("##"):
            body_controls.append(
                ft.Text(
                    line[2:].strip(),
                    size=17 if desktop else 15,
                    weight=ft.FontWeight.BOLD,
                    color=APP_COLORS["text"],
                )
            )
        elif line.startswith("---"):
            body_controls.append(ft.Divider(height=1, color=APP_COLORS["border_soft"]))
        elif line == "":
            body_controls.append(ft.Container(height=8))
        else:
            body_controls.append(
                ft.Text(line, size=14 if desktop else 13, color=APP_COLORS["text"])
            )

    footer_text = (
        "Вы получаете это письмо, так как включены email-уведомления в профиле «Белпомощник». "
        "Для отписки откройте Профиль → Настройки → Email-уведомления."
    )
    footer = ft.Container(
        content=ft.Text(footer_text, size=12, color=APP_COLORS["muted"]),
        padding=padding_symmetric(horizontal=20, vertical=12),
        border=ft.Border(top=ft.BorderSide(1, APP_COLORS["border_soft"])),
    )

    return app_card(
        ft.Column(
            spacing=0,
            controls=[
                header_block,
                ft.Container(
                    content=ft.Column(spacing=8, controls=body_controls),
                    padding=padding_symmetric(horizontal=20, vertical=16),
                ),
                footer,
            ],
        ),
        padding=0,
    )


def _mvp_badge() -> ft.Container:
    return ft.Container(
        content=ft.Row(
            spacing=8,
            controls=[
                ft.Icon(ft.Icons.INFO_OUTLINE, size=16, color=APP_COLORS["warning"]),
                ft.Text(
                    "MVP: письмо не отправляется. В production — SMTP через backend.",
                    size=13,
                    color=APP_COLORS["warning"],
                    expand=True,
                ),
            ],
        ),
        padding=padding_symmetric(horizontal=14, vertical=10),
        border_radius=10,
        bgcolor=APP_COLORS["warning_light"],
        border=border_all(APP_COLORS["warning"]),
    )


def _build_content(email_data: dict, desktop: bool, on_close=None, on_send_demo=None) -> ft.Control:
    title_row = ft.Row(
        spacing=12,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            icon_circle(ft.Icons.MARK_EMAIL_UNREAD_OUTLINED, size=46 if desktop else 40),
            ft.Column(
                spacing=2,
                expand=True,
                controls=[
                    ft.Text(
                        "Предпросмотр email-уведомления",
                        size=26 if desktop else 22,
                        weight=ft.FontWeight.BOLD,
                        color=APP_COLORS["text"],
                    ),
                    ft.Text(
                        "Так выглядит письмо, которое будет отправлено пользователю.",
                        size=14 if desktop else 13,
                        color=APP_COLORS["muted"],
                    ),
                ],
            ),
        ],
    )

    actions = ft.Row(
        spacing=10,
        controls=[
            primary_button(
                "Отправить сейчас (demo)",
                icon=ft.Icons.SEND_OUTLINED,
                on_click=on_send_demo,
            ),
            ghost_button("Закрыть", on_click=on_close),
        ],
    )

    return ft.Column(
        spacing=20,
        controls=[
            title_row,
            _mvp_badge(),
            _email_preview_card(email_data, desktop),
            actions,
        ],
    )


def build_email_preview_page(
    email_data: dict | None = None,
    is_desktop: bool = False,
    on_close=None,
    on_send_demo=None,
) -> ft.Control:
    """
    I1 — Страница предпросмотра email.

    email_data — словарь с ключами:
        subject (str): тема письма
        recipient (str): адрес получателя
        body_lines (list[str]): строки тела, ## = заголовок, --- = разделитель
    """
    data = email_data or _default_email_data()
    content = _build_content(data, is_desktop, on_close=on_close, on_send_demo=on_send_demo)
    return desktop_content(content, width=760, top=40) if is_desktop else content


def build_doc_expiry_email_data(
    recipient: str,
    doc_titles: list[str],
    app_name: str = "Белпомощник",
) -> dict:
    """
    I1/I3 — Формирует словарь данных письма об истекающих документах.
    Используется как в UI (предпросмотр), так и в backend (SMTP-отправка).
    """
    docs_list = "\n".join(f"  • {t}" for t in doc_titles)
    body_lines = [
        f"Здравствуйте!",
        "",
        f"## Напоминание о документах",
        "---",
        "Следующие ваши документы истекают в ближайшее время:",
        "",
        *[f"  • {t}" for t in doc_titles],
        "",
        "Рекомендуем заранее подготовить необходимые материалы для продления.",
        "",
        "Для просмотра сроков и статусов перейдите в раздел «Мои документы» приложения.",
        "",
        "С уважением,",
        f"Команда {app_name}",
    ]
    return {
        "subject": f"Напоминание: истекают документы — {app_name}",
        "recipient": recipient,
        "body_lines": body_lines,
    }


def _default_email_data() -> dict:
    return build_doc_expiry_email_data(
        recipient="пользователь@example.com",
        doc_titles=["Паспорт гражданина РБ", "Медицинский страховой полис"],
    )
