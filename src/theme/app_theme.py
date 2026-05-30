from __future__ import annotations

from collections.abc import Iterator, Mapping

import flet as ft


LIGHT = {
    "panel": "#FFFFFF",
    "sidebar": "#F8F9FF",
    "screen": "#FFFFFF",
    "surface": "#FFFFFF",
    "surface2": "#F0F2FF",
    "surface3": "#E8EEFF",
    "canvas_start": "#F5F7FF",
    "canvas_mid": "#EEF1FF",
    "canvas_end": "#F5F7FF",
    "stroke": "#D8DEFF",
    "stroke2": "#C8CFFF",
    "text": "#000000",
    "muted": "#4A5070",
    "muted2": "#6B7490",
    "blue": "#0056FF",
    "blue_text": "#2277FF",
    "green": "#20A462",
    "orange": "#F59E0B",
    "purple": "#8B5CF6",
    "red": "#EF4444",
    "cyan": "#06A6B2",
    "active": "#E3E7FC",
    "search": "#FFFFFF",
    "on_accent": "#FFFFFF",
}

DARK = {
    "panel": "#071521",
    "sidebar": "#0A1825",
    "screen": "#081723",
    "surface": "#0F1D2B",
    "surface2": "#12263A",
    "surface3": "#0B253B",
    "canvas_start": "#071521",
    "canvas_mid": "#081723",
    "canvas_end": "#0A1825",
    "stroke": "#21384B",
    "stroke2": "#284357",
    "text": "#F3FAFF",
    "muted": "#A8BED1",
    "muted2": "#8CA6BB",
    "blue": "#168DDB",
    "blue_text": "#44AFF9",
    "green": "#4BD486",
    "orange": "#FBBF24",
    "purple": "#A78BFA",
    "red": "#FF7B7B",
    "cyan": "#21C6D3",
    "active": "#0D426B",
    "search": "#0E1C2A",
    "on_accent": "#FFFFFF",
}

BADGE_LIGHT = {
    "blue": ("#E3E7FC", "#0056FF"),
    "green": ("#EAF8EF", "#20A462"),
    "orange": ("#FFF3DF", "#F59E0B"),
    "purple": ("#F0EAFE", "#8B5CF6"),
    "red": ("#FEECEC", "#EF4444"),
    "cyan": ("#E8FAFB", "#06A6B2"),
    "gray": ("#F2F4F7", "#667085"),
}

BADGE_DARK = {
    "blue": ("#123B5B", "#44AFF9"),
    "green": ("#123A2A", "#4BD486"),
    "orange": ("#463215", "#FBBF24"),
    "purple": ("#2F244D", "#A78BFA"),
    "red": ("#43242A", "#FF7B7B"),
    "cyan": ("#123E44", "#21C6D3"),
    "gray": ("#1D2A35", "#A8BED1"),
}

RADIUS = {
    "xs": 10,
    "sm": 14,
    "md": 16,
    "lg": 18,
    "xl": 22,
    "card": 24,
    "panel": 26,
    "hero": 30,
    "phone": 54,
}

SPACING = {
    "xxs": 6,
    "xs": 8,
    "sm": 12,
    "md": 16,
    "lg": 18,
    "xl": 24,
    "xxl": 28,
    "section": 32,
    "page": 42,
}

SHADOWS = {
    "light_card": ft.BoxShadow(spread_radius=0, blur_radius=12, offset=ft.Offset(0, 8), color="#228AA7BE"),
    "light_large": ft.BoxShadow(blur_radius=24, offset=ft.Offset(0, 18), color="#2E6E8AA6"),
    "dark_card": ft.BoxShadow(blur_radius=28, offset=ft.Offset(0, 22), color="#59000000"),
}

IPHONE_MIN_WIDTH = 375
IPHONE_BASE_WIDTH = 393
IPHONE_MAX_WIDTH = 430

PAGE_HORIZONTAL_PADDING = 16
PAGE_TOP_PADDING = 12
PAGE_BOTTOM_PADDING = 16

CARD_RADIUS = RADIUS["card"]
BUTTON_RADIUS = RADIUS["sm"]
INPUT_RADIUS = RADIUS["sm"]

BOTTOM_NAV_HEIGHT = 78
BOTTOM_NAV_SAFE_GAP = 12
FLOATING_ACTION_BOTTOM_PADDING = 24
IOS_SAFE_TOP_FALLBACK = 44
IOS_SAFE_BOTTOM_FALLBACK = 8

# Device breakpoints (based on real CSS pixel widths)
# Mobile  : width < 900  OR  (900–1099 AND portrait)  — covers iPhones, Galaxy Fold
# Tablet  : 900–1279 (not mobile) — OnePlus Pad portrait, medium browsers
# Desktop : >= 1280 — MacBook Air, OnePlus Pad landscape
MOBILE_MAX_WIDTH = 899
TABLET_MIN_WIDTH = 900
TABLET_MAX_WIDTH = 1279
DESKTOP_MIN_WIDTH = 1280

# Portrait-extension: wide-ish portrait screens (Fold unfolded portrait) → mobile
PORTRAIT_MOBILE_MAX_WIDTH = 1099

# Sidebar widths
SIDEBAR_WIDTH_DESKTOP = 268
SIDEBAR_WIDTH_TABLET = 228

# Gradients (placeholder hex — update when user provides exact values)
GRADIENT_FUTUREWAFE = ["#1A1A2E", "#16213E", "#0F3460"]   # dark navy
GRADIENT_MIDNIGHT_SURGE = ["#0056FF", "#2277FF", "#7B2FBE"]  # blue → violet

# AI Chat panel
AI_CHAT_PANEL_WIDTH = 360
AI_CHAT_PANEL_HEIGHT = 520

# Animation durations (ms)
ANIM_FAST = 130
ANIM_NORMAL = 220
ANIM_PAGE = 260

DEBUG_LAYOUT = False
CENTER = ft.Alignment(0, 0)

_ACTIVE_THEME_MODE = "light"
_LEGACY_KEY_MAP = {
    "primary": "blue",
    "background": "screen",
    "surface_alt": "surface2",
    "primary_dark": "blue_text",
    "primary_light": "active",
    "secondary": "green",
    "warning": "orange",
    "danger": "red",
    "border": "stroke",
    "border_soft": "stroke2",
    "dark": "text",
    "icon": "muted2",
    "accent": "blue",
}
_LEGACY_BADGE_MAP = {
    "blue_light": "blue",
    "secondary_light": "green",
    "warning_light": "orange",
    "danger_light": "red",
}


def normalize_theme_mode(mode: str | None) -> str:
    return "dark" if str(mode or "").lower() == "dark" else "light"


def set_theme_mode(mode: str | None) -> None:
    global _ACTIVE_THEME_MODE
    _ACTIVE_THEME_MODE = normalize_theme_mode(mode)


def get_active_theme_mode() -> str:
    return _ACTIVE_THEME_MODE


def get_theme(mode: str | None = None) -> dict[str, str]:
    return DARK if normalize_theme_mode(mode or _ACTIVE_THEME_MODE) == "dark" else LIGHT


def get_badge_palette(mode: str | None = None) -> dict[str, tuple[str, str]]:
    return BADGE_DARK if normalize_theme_mode(mode or _ACTIVE_THEME_MODE) == "dark" else BADGE_LIGHT


class ThemeColorProxy(Mapping[str, str]):
    def __getitem__(self, key: str) -> str:
        theme = get_theme()
        if key in theme:
            return theme[key]
        if key in _LEGACY_BADGE_MAP:
            return get_badge_palette()[_LEGACY_BADGE_MAP[key]][0]
        mapped_key = _LEGACY_KEY_MAP.get(key)
        if mapped_key and mapped_key in theme:
            return theme[mapped_key]
        raise KeyError(key)

    def __iter__(self) -> Iterator[str]:
        keys = set(get_theme().keys())
        keys.update(_LEGACY_KEY_MAP.keys())
        keys.update(_LEGACY_BADGE_MAP.keys())
        return iter(sorted(keys))

    def __len__(self) -> int:
        return len(list(iter(self)))

    def get(self, key: str, default: str | None = None) -> str | None:
        try:
            return self[key]
        except KeyError:
            return default


APP_COLORS = ThemeColorProxy()

APP_RADIUS = {
    "card": RADIUS["card"],
    "button": RADIUS["sm"],
    "input": RADIUS["sm"],
    "pill": 999,
    "panel": RADIUS["panel"],
    "hero": RADIUS["hero"],
}

APP_SPACING = {
    "page": PAGE_HORIZONTAL_PADDING,
    "card": SPACING["xl"],
    "gap": SPACING["sm"],
    "gap_lg": SPACING["md"],
    "section": SPACING["section"],
}


def build_theme(mode: str | None = None) -> ft.Theme:
    theme = get_theme(mode)
    return ft.Theme(
        color_scheme_seed=theme["blue"],
        use_material3=True,
        visual_density=ft.VisualDensity.COMFORTABLE,
        font_family="Inter, DejaVu Sans, Arial",
    )


def page_padding() -> ft.Padding:
    return ft.Padding(
        left=PAGE_HORIZONTAL_PADDING,
        top=PAGE_TOP_PADDING,
        right=PAGE_HORIZONTAL_PADDING,
        bottom=PAGE_BOTTOM_PADDING,
    )


def padding_symmetric(horizontal: int = 0, vertical: int = 0) -> ft.Padding:
    return ft.Padding(left=horizontal, top=vertical, right=horizontal, bottom=vertical)


def padding_only(left: int = 0, top: int = 0, right: int = 0, bottom: int = 0) -> ft.Padding:
    return ft.Padding(left=left, top=top, right=right, bottom=bottom)


def card_shadow(mode: str | None = None) -> list[ft.BoxShadow]:
    theme_mode = normalize_theme_mode(mode or _ACTIVE_THEME_MODE)
    return [SHADOWS["dark_card"] if theme_mode == "dark" else SHADOWS["light_card"]]


def large_shadow(mode: str | None = None) -> list[ft.BoxShadow]:
    theme_mode = normalize_theme_mode(mode or _ACTIVE_THEME_MODE)
    return [SHADOWS["dark_card"] if theme_mode == "dark" else SHADOWS["light_large"]]


def border_all(color: str, width: int = 1) -> ft.Border:
    side = ft.BorderSide(width=width, color=color)
    return ft.Border(top=side, right=side, bottom=side, left=side)


def border_bottom(color: str, width: int = 1) -> ft.Border:
    return ft.Border(bottom=ft.BorderSide(width=width, color=color))


def border_top(color: str, width: int = 1) -> ft.Border:
    return ft.Border(top=ft.BorderSide(width=width, color=color))
