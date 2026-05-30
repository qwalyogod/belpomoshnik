from __future__ import annotations

import flet as ft

from components.cards import app_card, badge, icon_circle
from components.layout import desktop_content
from theme.app_theme import (
    ANIM_FAST,
    APP_COLORS,
    APP_RADIUS,
    CENTER,
    GRADIENT_FUTUREWAFE,
    GRADIENT_MIDNIGHT_SURGE,
    SPACING,
    border_all,
    padding_symmetric,
)


AUTH_CARD_WIDTH = 460
MOBILE_AUTH_WIDTH = 340


# ---------------------------------------------------------------------------
# OAuth provider buttons (Google / Yandex)
# ---------------------------------------------------------------------------

def _google_glyph() -> ft.Container:
    """Multicolor 'G' built from stacked colored arcs (no external SVG)."""
    return ft.Container(
        width=22,
        height=22,
        alignment=CENTER,
        content=ft.Text("G", size=18, weight=ft.FontWeight.W_900, color="#4285F4"),
    )


def _yandex_glyph() -> ft.Container:
    return ft.Container(
        width=22,
        height=22,
        border_radius=11,
        bgcolor="#FC3F1D",
        alignment=CENTER,
        content=ft.Text("Я", size=14, weight=ft.FontWeight.W_900, color=ft.Colors.WHITE),
    )


def oauth_button(provider: str, on_oauth=None) -> ft.Container:
    if provider == "google":
        glyph = _google_glyph()
        label = "Google"
    else:
        glyph = _yandex_glyph()
        label = "Яндекс"

    btn = ft.Container(
        expand=True,
        height=50,
        border_radius=APP_RADIUS["button"],
        bgcolor=APP_COLORS["surface"],
        border=border_all(APP_COLORS["stroke2"]),
        alignment=CENTER,
        ink=True,
        animate=ft.Animation(ANIM_FAST, ft.AnimationCurve.EASE_OUT),
        on_click=lambda _: on_oauth(provider) if on_oauth else None,
        content=ft.Row(
            spacing=10,
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                glyph,
                ft.Text(label, size=15, weight=ft.FontWeight.W_800, color=APP_COLORS["text"]),
            ],
        ),
    )

    def _hover(e: ft.HoverEvent) -> None:
        btn.bgcolor = APP_COLORS["surface2"] if e.data == "true" else APP_COLORS["surface"]
        btn.border = border_all(APP_COLORS["blue"] if e.data == "true" else APP_COLORS["stroke2"])
        btn.update()

    btn.on_hover = _hover
    return btn


def oauth_row(on_oauth=None) -> ft.Row:
    return ft.Row(
        spacing=12,
        controls=[
            oauth_button("google", on_oauth),
            oauth_button("yandex", on_oauth),
        ],
    )


def oauth_divider() -> ft.Row:
    line = lambda: ft.Container(expand=True, height=1, bgcolor=APP_COLORS["stroke2"])
    return ft.Row(
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            line(),
            ft.Container(
                padding=padding_symmetric(horizontal=12, vertical=0),
                content=ft.Text("или", size=12, weight=ft.FontWeight.W_700, color=APP_COLORS["muted2"]),
            ),
            line(),
        ],
    )


def auth_logo() -> ft.Row:
    return ft.Row(
        spacing=12,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(
                width=42,
                height=42,
                border_radius=14,
                bgcolor=APP_COLORS["blue"],
                alignment=CENTER,
                content=ft.Icon(ft.Icons.NAVIGATION_ROUNDED, size=24, color=ft.Colors.WHITE),
            ),
            ft.Text("Белпомощник", size=22, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
        ],
    )


def auth_tabs(active: str, go_to=None) -> ft.Container:
    def tab(label: str, key: str, route: str) -> ft.Container:
        selected = active == key
        return ft.Container(
            expand=True,
            height=44,
            alignment=CENTER,
            border_radius=APP_RADIUS["button"],
            bgcolor=APP_COLORS["blue"] if selected else None,
            content=ft.Text(
                label,
                size=14,
                weight=ft.FontWeight.W_900,
                color=ft.Colors.WHITE if selected else APP_COLORS["muted"],
                text_align=ft.TextAlign.CENTER,
            ),
            on_click=lambda _: go_to(route) if go_to else None,
            ink=not selected,
        )

    return ft.Container(
        padding=4,
        border_radius=18,
        bgcolor=APP_COLORS["surface2"],
        border=border_all(APP_COLORS["stroke2"]),
        content=ft.Row(
            spacing=4,
            controls=[
                tab("Вход", "login", "/login"),
                tab("Регистрация", "register", "/register"),
            ],
        ),
    )


def auth_text_field(
    label: str,
    value: str = "",
    hint: str = "",
    prefix_icon=None,
    keyboard_type: ft.KeyboardType = ft.KeyboardType.TEXT,
    password: bool = False,
) -> ft.TextField:
    return ft.TextField(
        label=label,
        value=value,
        hint_text=hint,
        prefix_icon=prefix_icon,
        keyboard_type=keyboard_type,
        password=password,
        can_reveal_password=password,
        border_radius=APP_RADIUS["input"],
        border_color=APP_COLORS["stroke2"],
        focused_border_color=APP_COLORS["blue"],
        border_width=1,
        focused_border_width=1.5,
        bgcolor=APP_COLORS["search"],
        filled=True,
        fill_color=APP_COLORS["search"],
        cursor_color=APP_COLORS["blue"],
        color=APP_COLORS["text"],
        label_style=ft.TextStyle(color=APP_COLORS["muted"], weight=ft.FontWeight.W_700),
        hint_style=ft.TextStyle(color=APP_COLORS["muted2"]),
        text_style=ft.TextStyle(size=16, weight=ft.FontWeight.W_500),
        content_padding=ft.Padding(left=14, top=14, right=14, bottom=14),
        error_style=ft.TextStyle(size=12, color=APP_COLORS["red"], weight=ft.FontWeight.W_600),
        error_max_lines=2,
    )


def set_field_error(field: ft.TextField, message: str | None) -> None:
    has_error = bool(message)
    field.error = message or None
    field.border_color = APP_COLORS["red"] if has_error else APP_COLORS["stroke2"]
    field.focused_border_color = APP_COLORS["red"] if has_error else APP_COLORS["blue"]
    if field.page:
        field.update()


def form_footer(text: str, action_text: str, route: str, go_to=None) -> ft.Row:
    return ft.Row(
        alignment=ft.MainAxisAlignment.CENTER,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=6,
        wrap=True,
        controls=[
            ft.Text(text, size=13, color=APP_COLORS["muted"]),
            ft.Container(
                content=ft.Text(action_text, size=13, weight=ft.FontWeight.W_900, color=APP_COLORS["blue_text"]),
                on_click=lambda _: go_to(route) if go_to else None,
                ink=True,
            ),
        ],
    )


def _gradient_blob(size: int, colors: list[str], left=None, top=None, right=None, bottom=None) -> ft.Container:
    return ft.Container(
        width=size,
        height=size,
        left=left,
        top=top,
        right=right,
        bottom=bottom,
        border_radius=size // 2,
        gradient=ft.LinearGradient(begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1), colors=colors),
        opacity=0.5,
        animate_scale=ft.Animation(2600, ft.AnimationCurve.EASE_IN_OUT),
        animate_opacity=ft.Animation(2600, ft.AnimationCurve.EASE_IN_OUT),
        scale=1.0,
    )


def animated_auth_background(page, *, content: ft.Control, mobile: bool = False) -> ft.Control:
    """Full-bleed animated gradient background with floating, pulsing blobs."""
    import math

    blob_a = _gradient_blob(360, GRADIENT_FUTUREWAFE, left=-90, top=-60)
    blob_b = _gradient_blob(300, GRADIENT_MIDNIGHT_SURGE, right=-70, top=120)
    blob_c = _gradient_blob(260, GRADIENT_FUTUREWAFE, left=40, bottom=-90)
    blobs = [blob_a, blob_b, blob_c]

    async def _pulse_loop() -> None:
        import asyncio
        t = 0.0
        while True:
            t += 0.06
            try:
                for i, b in enumerate(blobs):
                    phase = t + i * 2.1
                    b.scale = 1.0 + 0.16 * math.sin(phase)
                    b.opacity = 0.42 + 0.16 * (0.5 + 0.5 * math.sin(phase * 0.8))
                    b.update()
            except Exception:
                return  # blobs detached (navigated away) → stop cleanly
            await asyncio.sleep(0.06)

    # Restart guard — only one loop alive at a time
    if not getattr(page, "_auth_anim_token", None):
        page._auth_anim_token = 0
    page._auth_anim_token += 1
    page.run_task(_pulse_loop)

    return ft.Container(
        expand=True,
        bgcolor=APP_COLORS["canvas_start"],
        content=ft.Stack(
            expand=True,
            controls=[
                blob_a,
                blob_b,
                blob_c,
                # Frosted overlay to soften blobs
                ft.Container(
                    expand=True,
                    bgcolor=ft.Colors.with_opacity(0.55, APP_COLORS["screen"]),
                    blur=ft.Blur(40, 40, ft.BlurTileMode.CLAMP),
                ),
                # Centered content
                ft.Container(
                    expand=True,
                    alignment=CENTER,
                    padding=ft.Padding(left=16, top=24, right=16, bottom=24),
                    content=content,
                ),
            ],
        ),
    )


def auth_shell(
    card: ft.Control,
    *,
    is_desktop: bool,
    title: str,
    subtitle: str,
    page=None,
) -> ft.Control:
    if not is_desktop:
        body = ft.Container(width=MOBILE_AUTH_WIDTH, content=card)
        if page is not None:
            return animated_auth_background(page, content=body, mobile=True)
        return body

    side = ft.Column(
        spacing=22,
        controls=[
            ft.Container(
                width=68, height=68, border_radius=22,
                gradient=ft.LinearGradient(begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1), colors=GRADIENT_MIDNIGHT_SURGE),
                alignment=CENTER,
                content=ft.Icon(ft.Icons.SHIELD_OUTLINED, size=34, color=ft.Colors.WHITE),
            ),
            ft.Text(title, size=36, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
            ft.Text(subtitle, size=16, color=APP_COLORS["muted"]),
            ft.Row(
                spacing=8,
                wrap=True,
                controls=[
                    badge("Проблема → план", "blue"),
                    badge("Напоминания", "gray"),
                    badge("Локальные данные", "cyan"),
                ],
            ),
            app_card(
                ft.Column(
                    spacing=10,
                    controls=[
                        ft.Text("Сегодня важно", size=18, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                        _important_row("1", "Истекает медкнижка", "через 12 дней"),
                        _important_row("2", "Новый апдейт по ЖКХ", "для вашего профиля"),
                        _important_row("3", "План “Переезд”", "2 задачи сегодня"),
                    ],
                ),
                padding=20,
                bgcolor=APP_COLORS["surface"],
            ),
        ],
    )
    content = ft.Row(
        spacing=34,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(width=430, content=side),
            ft.Container(width=AUTH_CARD_WIDTH, content=card),
        ],
    )
    if page is not None:
        return animated_auth_background(page, content=content)
    return desktop_content(content, width=960, top=52, bottom=80)


def _important_row(index: str, title: str, subtitle: str) -> ft.Row:
    return ft.Row(
        spacing=10,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(
                width=30,
                height=30,
                border_radius=15,
                alignment=CENTER,
                bgcolor=APP_COLORS["active"],
                content=ft.Text(index, size=13, weight=ft.FontWeight.W_900, color=APP_COLORS["blue_text"]),
            ),
            ft.Column(
                spacing=1,
                expand=True,
                controls=[
                    ft.Text(title, size=14, weight=ft.FontWeight.W_800, color=APP_COLORS["text"]),
                    ft.Text(subtitle, size=12, color=APP_COLORS["muted"]),
                ],
            ),
        ],
    )
