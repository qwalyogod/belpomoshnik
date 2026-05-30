"""AI Agent chat panel — floating on desktop, fullscreen on mobile/tablet."""
from __future__ import annotations

import flet as ft

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
)

_DEMO_MESSAGES: list[dict] = [
    {
        "role": "assistant",
        "text": "Здравствуйте! Я ИИ-помощник Белпомощника.\n\nЗадайте вопрос о правах, документах или жизненных ситуациях — разберёмся вместе.",
    }
]


def _bubble(text: str, role: str) -> ft.Container:
    is_user = role == "user"
    return ft.Container(
        content=ft.Text(
            text,
            size=14,
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


def _messages_list(messages: list[dict]) -> ft.Column:
    return ft.Column(
        spacing=8,
        scroll=ft.ScrollMode.AUTO,
        auto_scroll=True,
        expand=True,
        controls=[_bubble(m["text"], m["role"]) for m in messages],
    )


def _input_area(messages: list[dict], on_update) -> ft.Container:
    field = ft.TextField(
        hint_text="Спросите о правах, документах...",
        expand=True,
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color=ft.Colors.TRANSPARENT,
        cursor_color=APP_COLORS["blue"],
        color=APP_COLORS["text"],
        text_size=14,
        hint_style=ft.TextStyle(color=APP_COLORS["muted2"]),
        multiline=True,
        max_lines=3,
        min_lines=1,
    )

    def _send(_e=None) -> None:
        text = (field.value or "").strip()
        if not text:
            return
        messages.append({"role": "user", "text": text})
        field.value = ""
        # Demo auto-reply
        messages.append({
            "role": "assistant",
            "text": "Понял вас. Сейчас это демо-режим — подключение к реальному агенту появится в следующей версии.",
        })
        on_update()

    field.on_submit = lambda _: _send()

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
                ft.IconButton(
                    icon=ft.Icons.SEND_ROUNDED,
                    icon_color=APP_COLORS["blue"],
                    icon_size=22,
                    on_click=lambda _: _send(),
                    tooltip="Отправить",
                ),
            ],
        ),
    )


# ---------------------------------------------------------------------------
# Public builders
# ---------------------------------------------------------------------------

def build_ai_chat_fab(on_click) -> ft.Container:
    """Floating AI button for mobile bottom-right."""
    btn = ft.Container(
        width=54,
        height=54,
        border_radius=27,
        bgcolor=APP_COLORS["blue"],
        shadow=[ft.BoxShadow(blur_radius=20, offset=ft.Offset(0, 8), color="#5519A3E8")],
        alignment=CENTER,
        ink=True,
        on_click=on_click,
        tooltip="ИИ-помощник",
        animate=ft.Animation(ANIM_FAST, ft.AnimationCurve.EASE_OUT),
        content=ft.Icon(ft.Icons.AUTO_AWESOME_OUTLINED, size=24, color=ft.Colors.WHITE),
    )

    def _hover(e: ft.HoverEvent) -> None:
        btn.bgcolor = APP_COLORS["blue_text"] if e.data == "true" else APP_COLORS["blue"]
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
                        width=30, height=30, border_radius=15,
                        bgcolor=ft.Colors.with_opacity(0.20, ft.Colors.WHITE),
                        alignment=CENTER,
                        content=ft.Icon(ft.Icons.AUTO_AWESOME, size=16, color=ft.Colors.WHITE),
                    ),
                    ft.Column(
                        spacing=0,
                        expand=True,
                        controls=[
                            ft.Text("ИИ-помощник", size=14, weight=ft.FontWeight.W_800, color=ft.Colors.WHITE),
                            ft.Text("Белпомощник • 24/7", size=10, color=ft.Colors.with_opacity(0.75, ft.Colors.WHITE)),
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
            content=_messages_list(messages),
        )

    def _chat_footer() -> ft.Container:
        return ft.Container(
            padding=ft.Padding(left=12, top=8, right=12, bottom=12),
            bgcolor=APP_COLORS["surface"],
            border=ft.Border(top=ft.BorderSide(1, APP_COLORS["stroke2"])),
            border_radius=ft.BorderRadius(
                top_left=0, top_right=0,
                bottom_left=APP_RADIUS["card"] if not fullscreen else 0,
                bottom_right=APP_RADIUS["card"] if not fullscreen else 0,
            ),
            content=_input_area(messages, _on_update),
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
        # Caller embeds panel directly in layout — return panel only
        return panel

    if fullscreen:
        # Full-screen backdrop
        return ft.Container(
            expand=True,
            bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.BLACK),
            content=ft.Column(
                expand=True,
                spacing=0,
                controls=[panel],
            ),
        )

    # Desktop mini — positioned bottom-right via Stack overlay
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
