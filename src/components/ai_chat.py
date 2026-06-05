"""AI assistant chat panel — floating on desktop, fullscreen on mobile/tablet."""
from __future__ import annotations

import flet as ft

from components.ai_section_card import build_ai_section_card
from services.ai_helper import IntentResult, detect_intent
from theme.app_theme import (
    AI_CHAT_PANEL_HEIGHT,
    AI_CHAT_PANEL_WIDTH,
    ANIM_FAST,
    ANIM_NORMAL,
    APP_COLORS,
    APP_RADIUS,
    CENTER,
    border_all,
    padding_symmetric,
    ts,
)

INITIAL_MESSAGES: list[dict] = [
    {
        "role": "assistant",
        "text": "Здравствуйте! Я ИИ-помощник Белпомощника.\n\nНапишите, что хотите найти или сделать, а я подскажу подходящий раздел.",
    }
]


def _bubble(text: str, role: str) -> ft.Container:
    is_user = role == "user"
    return ft.Container(
        content=ft.Text(
            text,
            size=ts(14),
            color=ft.Colors.WHITE if is_user else APP_COLORS["text"],
            selectable=True,
        ),
        padding=padding_symmetric(horizontal=14, vertical=10),
        border_radius=ft.BorderRadius(
            top_left=16,
            top_right=16,
            bottom_left=4 if is_user else 16,
            bottom_right=16 if is_user else 4,
        ),
        bgcolor=APP_COLORS["blue"] if is_user else APP_COLORS["surface2"],
        margin=ft.Margin(
            left=48 if is_user else 0,
            right=0 if is_user else 48,
            top=0,
            bottom=0,
        ),
    )


def _message_control(message: dict, on_section_click=None) -> ft.Control:
    controls: list[ft.Control] = [_bubble(str(message.get("text", "")), str(message.get("role", "assistant")))]
    intent = message.get("intent")
    if isinstance(intent, IntentResult):
        warning = None
        if intent.requires_auth_warning:
            warning = "Для личного действия понадобится вход или регистрация."
        controls.append(
            ft.Container(
                margin=ft.Margin(left=0, top=2, right=48, bottom=0),
                content=build_ai_section_card(
                    intent.section,
                    on_click=on_section_click,
                    warning=warning,
                ),
            )
        )
    return ft.Column(spacing=6, controls=controls)


def _messages_list(messages: list[dict], on_section_click=None) -> ft.Column:
    message_controls: list[ft.Control] = []
    for message in messages:
        message_controls.append(_message_control(message, on_section_click))
    return ft.Column(
        spacing=8,
        scroll=ft.ScrollMode.AUTO,
        auto_scroll=True,
        expand=True,
        controls=message_controls,
    )


def _input_area(
    messages: list[dict],
    on_update,
    *,
    role: str,
    is_guest: bool,
    on_section_click=None,
) -> ft.Container:
    field = ft.TextField(
        hint_text="Например: хочу добавить паспорт",
        expand=True,
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color=ft.Colors.TRANSPARENT,
        cursor_color=APP_COLORS["blue"],
        color=APP_COLORS["text"],
        text_size=ts(14),
        hint_style=ft.TextStyle(color=APP_COLORS["muted2"]),
        multiline=True,
        max_lines=3,
        min_lines=1,
    )

    send_button = ft.IconButton(
        icon=ft.Icons.SEND_ROUNDED,
        icon_color=APP_COLORS["blue"],
        icon_size=22,
        tooltip="Отправить",
    )

    def _send(_e=None) -> None:
        text = (field.value or "").strip()
        if not text:
            return
        send_button.disabled = True
        messages.append({"role": "user", "text": text})
        intent = detect_intent(text, role=role, is_guest=is_guest)
        messages.append({
            "role": "assistant",
            "text": intent.response_text,
            "intent": intent,
        })
        field.value = ""
        send_button.disabled = False
        on_update()

    field.on_submit = lambda _: _send()
    send_button.on_click = lambda _: _send()

    return ft.Container(
        padding=ft.Padding(left=12, top=8, right=8, bottom=8),
        border_radius=14,
        bgcolor=APP_COLORS["surface2"],
        border=border_all(APP_COLORS["stroke2"]),
        content=ft.Row(
            spacing=6,
            vertical_alignment=ft.CrossAxisAlignment.END,
            controls=[
                field,
                send_button,
            ],
        ),
    )


# ---------------------------------------------------------------------------
# Public builders
# ---------------------------------------------------------------------------

def build_ai_chat_fab(on_click, *, compact: bool = False) -> ft.Container:
    """Floating assistant button."""
    if compact:
        width = 54
        content = ft.Icon(ft.Icons.AUTO_AWESOME_OUTLINED, size=24, color=ft.Colors.WHITE)
    else:
        width = 172
        content = ft.Row(
            spacing=8,
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                ft.Icon(ft.Icons.AUTO_AWESOME_OUTLINED, size=20, color=ft.Colors.WHITE),
                ft.Text("Спросить помощника", size=ts(13), weight=ft.FontWeight.W_800, color=ft.Colors.WHITE),
            ],
        )

    btn = ft.Container(
        width=width,
        height=54,
        border_radius=27,
        bgcolor=APP_COLORS["blue"],
        shadow=[ft.BoxShadow(blur_radius=20, offset=ft.Offset(0, 8), color="#5519A3E8")],
        alignment=CENTER,
        ink=True,
        on_click=on_click,
        tooltip="ИИ-помощник",
        animate=ft.Animation(ANIM_FAST, ft.AnimationCurve.EASE_OUT),
        content=content,
    )

    def _hover(e: ft.HoverEvent) -> None:
        is_hovered = e.data == "true"
        btn.bgcolor = APP_COLORS["blue_text"] if is_hovered else APP_COLORS["blue"]
        btn.scale = 1.03 if is_hovered else 1
        btn.update()

    btn.on_hover = _hover
    return btn


def build_ai_chat_overlay(
    messages: list[dict],
    on_close,
    on_toggle_fullscreen,
    on_toggle_dock,
    *,
    fullscreen: bool = False,
    docked: bool = False,
    desktop: bool = False,
    role: str = "guest",
    is_guest: bool = True,
    on_section_click=None,
) -> ft.Container:
    """
    Returns the full overlay container for the AI chat.

    - mobile/tablet fullscreen: covers entire screen with dark backdrop
    - desktop mini: floating panel bottom-right, no backdrop
    - desktop docked: rendered inline (caller handles layout)
    """

    def _on_update() -> None:
        panel_column.controls[:] = [
            _chat_header(),
            _chat_body(),
            _chat_footer(),
        ]
        panel_column.update()

    def _chat_header() -> ft.Container:
        return ft.Container(
            height=58,
            padding=ft.Padding(left=16, top=0, right=6, bottom=0),
            bgcolor=APP_COLORS["blue"],
            border_radius=ft.BorderRadius(
                top_left=APP_RADIUS["card"] if not fullscreen else 0,
                top_right=APP_RADIUS["card"] if not fullscreen else 0,
                bottom_left=0,
                bottom_right=0,
            ),
            content=ft.Row(
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        width=30,
                        height=30,
                        border_radius=15,
                        bgcolor=ft.Colors.with_opacity(0.20, ft.Colors.WHITE),
                        alignment=CENTER,
                        content=ft.Icon(ft.Icons.AUTO_AWESOME, size=16, color=ft.Colors.WHITE),
                    ),
                    ft.Column(
                        spacing=0,
                        expand=True,
                        controls=[
                            ft.Text("ИИ-помощник", size=14, weight=ft.FontWeight.W_800, color=ft.Colors.WHITE),
                            ft.Text("ориентир по разделам", size=10, color=ft.Colors.with_opacity(0.75, ft.Colors.WHITE)),
                        ],
                    ),
                    ft.Row(
                        spacing=0,
                        controls=[
                            ft.IconButton(
                                icon=ft.Icons.CLOSE_FULLSCREEN if fullscreen else ft.Icons.OPEN_IN_FULL,
                                icon_color=ft.Colors.with_opacity(0.85, ft.Colors.WHITE),
                                icon_size=18,
                                tooltip="Свернуть" if fullscreen else "На весь экран",
                                on_click=on_toggle_fullscreen,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.VERTICAL_SPLIT_OUTLINED,
                                icon_color=ft.Colors.with_opacity(0.85, ft.Colors.WHITE),
                                icon_size=18,
                                tooltip="Закрепить справа",
                                on_click=on_toggle_dock,
                            ) if desktop and not fullscreen else ft.Container(width=0),
                            ft.IconButton(
                                icon=ft.Icons.CLOSE_ROUNDED,
                                icon_color=ft.Colors.with_opacity(0.85, ft.Colors.WHITE),
                                icon_size=18,
                                tooltip="Закрыть",
                                on_click=on_close,
                            ),
                        ],
                    ),
                ],
            ),
        )

    def _chat_body() -> ft.Container:
        return ft.Container(
            expand=True,
            padding=ft.Padding(left=14, top=12, right=14, bottom=6),
            bgcolor=APP_COLORS["screen"],
            content=_messages_list(messages, on_section_click),
        )

    def _chat_footer() -> ft.Container:
        return ft.Container(
            padding=ft.Padding(left=12, top=8, right=12, bottom=12),
            bgcolor=APP_COLORS["surface"],
            border=ft.Border(top=ft.BorderSide(1, APP_COLORS["stroke2"])),
            border_radius=ft.BorderRadius(
                top_left=0,
                top_right=0,
                bottom_left=APP_RADIUS["card"] if not fullscreen else 0,
                bottom_right=APP_RADIUS["card"] if not fullscreen else 0,
            ),
            content=_input_area(
                messages,
                _on_update,
                role=role,
                is_guest=is_guest,
                on_section_click=on_section_click,
            ),
        )

    panel_column = ft.Column(
        expand=True,
        spacing=0,
        controls=[_chat_header(), _chat_body(), _chat_footer()],
    )

    panel = ft.Container(
        expand=fullscreen or docked,
        width=None if (fullscreen or docked) else AI_CHAT_PANEL_WIDTH,
        height=None if fullscreen else (None if docked else AI_CHAT_PANEL_HEIGHT),
        border_radius=0 if fullscreen else APP_RADIUS["card"],
        shadow=[] if fullscreen else [ft.BoxShadow(blur_radius=40, offset=ft.Offset(0, 20), color="#40000000")],
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        animate=ft.Animation(ANIM_NORMAL, ft.AnimationCurve.EASE_OUT),
        content=panel_column,
    )

    if docked:
        return panel

    if fullscreen:
        return ft.Container(
            expand=True,
            bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.BLACK),
            content=ft.Column(
                expand=True,
                spacing=0,
                controls=[panel],
            ),
        )

    return ft.Container(
        expand=True,
        bgcolor=None,
        content=ft.Stack(
            expand=True,
            controls=[
                ft.Container(
                    content=panel,
                    right=20,
                    bottom=20,
                ),
            ],
        ),
    )
