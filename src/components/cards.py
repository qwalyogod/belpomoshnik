from __future__ import annotations

import flet as ft

from theme.app_theme import (
    ANIM_FAST,
    APP_COLORS,
    APP_RADIUS,
    CENTER,
    SPACING,
    border_all,
    card_shadow,
    get_badge_palette,
    padding_symmetric,
)


BADGE_VARIANT_ALIASES = {
    "default": "gray",
    "success": "green",
    "error": "red",
    "danger": "red",
    "warning": "orange",
    "dark": "gray",
    "draft": "orange",
    "published": "green",
    "active": "blue",
    "locked": "gray",
    "urgent": "red",
    "new": "cyan",
    "beta": "purple",
}


def _badge_colors(variant: str) -> tuple[str, str]:
    palette = get_badge_palette()
    color_key = BADGE_VARIANT_ALIASES.get(variant, variant)
    return palette.get(color_key, palette["gray"])


def section_title(title: str, subtitle: str | None = None, centered: bool = False) -> ft.Column:
    align = ft.CrossAxisAlignment.CENTER if centered else ft.CrossAxisAlignment.START
    text_align = ft.TextAlign.CENTER if centered else ft.TextAlign.START
    controls: list[ft.Control] = [
        ft.Text(
            title,
            size=24,
            weight=ft.FontWeight.W_900,
            color=APP_COLORS["text"],
            text_align=text_align,
        )
    ]
    if subtitle:
        controls.append(ft.Text(subtitle, size=14, color=APP_COLORS["muted"], text_align=text_align))
    return ft.Column(spacing=6, horizontal_alignment=align, controls=controls)


def page_heading(title: str, subtitle: str | None = None, actions: list[ft.Control] | None = None) -> ft.Control:
    text_controls: list[ft.Control] = [
        ft.Text(title, size=40, weight=ft.FontWeight.W_900, color=APP_COLORS["text"])
    ]
    if subtitle:
        text_controls.append(ft.Text(subtitle, size=16, color=APP_COLORS["muted"]))
    title_block = ft.Column(spacing=8, expand=True, controls=text_controls)
    if actions:
        return ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[title_block, ft.Row(spacing=8, controls=actions)],
        )
    return title_block


def app_card(
    content: ft.Control,
    padding: int = SPACING["xl"],
    bgcolor: str | None = None,
    border_color: str | None = None,
    width: int | float | None = None,
    height: int | float | None = None,
    animate: bool = False,
    hover: bool = False,
) -> ft.Container:
    animation = ft.Animation(ANIM_FAST, ft.AnimationCurve.EASE_OUT)
    base_bg = bgcolor or APP_COLORS["surface"]
    card = ft.Container(
        content=content,
        padding=padding,
        width=width,
        height=height,
        border_radius=APP_RADIUS["card"],
        bgcolor=base_bg,
        border=border_all(border_color or APP_COLORS["stroke2"]),
        shadow=card_shadow(),
        animate=animation,
    )
    if hover:
        def _on_hover(e: ft.HoverEvent) -> None:
            card.bgcolor = APP_COLORS["surface2"] if e.data == "true" else base_bg
            card.update()
        card.on_hover = _on_hover
    return card


def soft_card(content: ft.Control, padding: int = SPACING["xl"]) -> ft.Container:
    return app_card(content, padding=padding)


def badge(text: str, variant: str = "default") -> ft.Container:
    bgcolor, color = _badge_colors(variant)
    return ft.Container(
        content=ft.Text(text, size=13, weight=ft.FontWeight.W_800, color=color, max_lines=1, no_wrap=True),
        padding=padding_symmetric(horizontal=14, vertical=6),
        border_radius=15,
        bgcolor=bgcolor,
    )


def icon_circle(icon: str, color: str | None = None, bgcolor: str | None = None, size: int = 48) -> ft.Container:
    return ft.Container(
        width=size,
        height=size,
        border_radius=size // 2,
        bgcolor=bgcolor or APP_COLORS["surface2"],
        alignment=CENTER,
        content=ft.Icon(icon, size=max(18, size // 2), color=color or APP_COLORS["muted2"]),
    )


def category_tile(label: str, icon: str, on_click=None, height: int | None = None) -> ft.Container:
    return ft.Container(
        content=app_card(
            ft.Column(
                spacing=14,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    icon_circle(icon, color=APP_COLORS["muted2"], bgcolor=APP_COLORS["surface2"], size=52),
                    ft.Text(
                        label,
                        size=14,
                        weight=ft.FontWeight.W_800,
                        color=APP_COLORS["text"],
                        text_align=ft.TextAlign.CENTER,
                        max_lines=2,
                    ),
                ],
            ),
            padding=16,
            height=height,
        ),
        on_click=on_click,
        ink=True,
    )


def category_chip(label: str, selected: bool = False, on_click=None) -> ft.Container:
    return ft.Container(
        content=ft.Text(
            label,
            size=14,
            weight=ft.FontWeight.W_800,
            color=ft.Colors.WHITE if selected else APP_COLORS["text"],
            max_lines=1,
            no_wrap=True,
        ),
        padding=padding_symmetric(horizontal=16, vertical=9),
        border_radius=18,
        bgcolor=APP_COLORS["blue"] if selected else APP_COLORS["surface2"],
        border=border_all(APP_COLORS["blue"] if selected else APP_COLORS["stroke2"]),
        on_click=on_click,
        ink=True,
    )


def empty_state_card(
    title: str,
    description: str,
    action_text: str | None = None,
    on_action=None,
    icon=ft.Icons.INFO_OUTLINE,
) -> ft.Container:
    controls: list[ft.Control] = [
        icon_circle(icon, color=APP_COLORS["blue"], bgcolor=APP_COLORS["active"], size=58),
        ft.Text(title, size=18, weight=ft.FontWeight.W_800, color=APP_COLORS["text"], text_align=ft.TextAlign.CENTER),
        ft.Text(description, size=14, color=APP_COLORS["muted"], text_align=ft.TextAlign.CENTER),
    ]
    if action_text:
        controls.append(
            ft.Button(
                content=action_text,
                on_click=on_action,
                height=46,
                style=ft.ButtonStyle(
                    bgcolor=APP_COLORS["blue"],
                    color=ft.Colors.WHITE,
                    shape=ft.RoundedRectangleBorder(radius=APP_RADIUS["button"]),
                    padding=padding_symmetric(horizontal=18, vertical=12),
                ),
            )
        )
    return app_card(
        ft.Column(
            spacing=12,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=controls,
        ),
        padding=28,
    )


def hint_card(text: str, icon=ft.Icons.LIGHTBULB_OUTLINE) -> ft.Container:
    return app_card(
        ft.Row(
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                ft.Icon(icon, size=20, color=APP_COLORS["blue"]),
                ft.Text(text, size=14, color=APP_COLORS["muted"], expand=True),
            ],
        ),
        padding=14,
        bgcolor=APP_COLORS["surface3"],
        border_color=APP_COLORS["stroke2"],
    )


def hero_card(
    title: str,
    description: str,
    icon=None,
    badges: list[ft.Control] | None = None,
    actions: list[ft.Control] | None = None,
    leading: ft.Control | None = None,
) -> ft.Container:
    hero_leading = leading or icon_circle(icon or ft.Icons.INFO_OUTLINE, color=APP_COLORS["blue"], bgcolor=APP_COLORS["active"], size=64)
    header_controls: list[ft.Control] = [
        ft.Text(title, size=28, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
        ft.Text(description, size=15, color=APP_COLORS["muted"]),
    ]
    if badges:
        header_controls.append(ft.Row(spacing=8, run_spacing=8, wrap=True, controls=badges))
    if actions:
        header_controls.append(ft.Row(spacing=10, wrap=True, controls=actions))
    return ft.Container(
        content=ft.Row(
            spacing=18,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[hero_leading, ft.Column(spacing=10, expand=True, controls=header_controls)],
        ),
        padding=28,
        border_radius=APP_RADIUS["hero"],
        bgcolor=APP_COLORS["surface3"],
        border=border_all(APP_COLORS["stroke2"]),
        shadow=card_shadow(),
    )


def stat_card(label: str, value: str | int, sublabel: str = "", icon=None, tone: str = "blue") -> ft.Container:
    badge_bg, badge_fg = _badge_colors(tone)
    controls: list[ft.Control] = [
        icon_circle(icon or ft.Icons.INSIGHTS_OUTLINED, color=badge_fg, bgcolor=badge_bg, size=44),
        ft.Text(str(value), size=28, weight=ft.FontWeight.W_900, color=badge_fg),
        ft.Text(label, size=12, weight=ft.FontWeight.W_700, color=APP_COLORS["muted"]),
    ]
    if sublabel:
        controls.append(ft.Text(sublabel, size=12, color=APP_COLORS["muted2"]))
    return app_card(ft.Column(spacing=6, controls=controls), padding=18)


def search_box(
    value: str = "",
    hint: str = "Поиск",
    on_change=None,
    on_submit=None,
    expand: bool = True,
) -> ft.Container:
    return ft.Container(
        expand=expand,
        border_radius=18,
        bgcolor=APP_COLORS["search"],
        border=border_all(APP_COLORS["stroke2"]),
        padding=ft.Padding(left=14, top=2, right=14, bottom=2),
        content=ft.Row(
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(ft.Icons.SEARCH, size=22, color=APP_COLORS["blue"]),
                ft.TextField(
                    value=value,
                    hint_text=hint,
                    expand=True,
                    border_color=ft.Colors.TRANSPARENT,
                    focused_border_color=ft.Colors.TRANSPARENT,
                    cursor_color=APP_COLORS["blue"],
                    text_size=15,
                    color=APP_COLORS["text"],
                    hint_style=ft.TextStyle(color=APP_COLORS["muted2"]),
                    on_change=on_change,
                    on_submit=on_submit,
                ),
            ],
        ),
    )


def problem_card(problem: dict, on_click=None, compact: bool = False) -> ft.Container:
    category = problem.get("category_name") or problem.get("category", "")
    description = problem.get("desc") or problem.get("description", "")
    return ft.Container(
        content=app_card(
            ft.Row(
                spacing=14,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    icon_circle(ft.Icons.ARTICLE_OUTLINED, size=46) if not compact else ft.Container(width=0),
                    ft.Column(
                        spacing=8,
                        expand=True,
                        controls=[
                            badge(category, "default") if category else ft.Container(),
                            ft.Text(problem["title"], size=18, weight=ft.FontWeight.W_800, color=APP_COLORS["text"]),
                            ft.Text(description, size=14, color=APP_COLORS["muted"], max_lines=2),
                        ],
                    ),
                    ft.Icon(ft.Icons.CHEVRON_RIGHT, color=APP_COLORS["muted2"], size=22),
                ],
            ),
            padding=16,
            height=104 if compact else None,
            animate=True,
        ),
        on_click=on_click,
        ink=True,
    )


def info_card(title: str, body: str | list[str], icon=None, tone: str = "blue") -> ft.Container:
    tone_map = {
        "blue": "blue",
        "green": "green",
        "warning": "orange",
        "danger": "red",
    }
    color_key = tone_map.get(tone, "blue")
    badge_bg, badge_fg = _badge_colors(color_key)
    if isinstance(body, list):
        rows: list[ft.Control] = []
        for index, item in enumerate(body, start=1):
            rows.append(
                ft.Row(
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    controls=[
                        ft.Container(
                            width=24,
                            height=24,
                            border_radius=12,
                            bgcolor=badge_bg,
                            alignment=CENTER,
                            content=ft.Text(str(index), size=12, weight=ft.FontWeight.W_800, color=badge_fg),
                        ),
                        ft.Text(item, size=14, color=APP_COLORS["text"], expand=True),
                    ],
                )
            )
        body_control = ft.Column(spacing=10, controls=rows)
    else:
        body_control = ft.Text(body, size=14, color=APP_COLORS["text"])

    return app_card(
        ft.Column(
            spacing=13,
            controls=[
                ft.Row(
                    spacing=10,
                    controls=[
                        ft.Icon(icon or ft.Icons.INFO_OUTLINE, color=badge_fg, size=23),
                        ft.Text(title, size=18, weight=ft.FontWeight.W_800, color=APP_COLORS["text"], expand=True),
                    ],
                ),
                body_control,
            ],
        ),
        bgcolor=badge_bg if tone in {"warning"} else APP_COLORS["surface"],
        border_color=APP_COLORS["stroke2"],
    )
