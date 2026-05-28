from __future__ import annotations

from datetime import datetime

import flet as ft

from components.buttons import ghost_button, primary_button
from components.cards import (
    app_card,
    badge,
    category_chip,
    empty_state_card,
    icon_circle,
    page_heading,
    search_box,
)
from components.layout import desktop_content
from data.mock_data import LEGAL_UPDATES
from theme.app_theme import APP_COLORS, APP_RADIUS, SPACING, border_all, card_shadow, padding_symmetric


LAW_FILTERS = [
    {"id": "all", "name": "Все"},
    {"id": "docs", "name": "Документы"},
    {"id": "home", "name": "ЖКХ"},
    {"id": "taxes", "name": "Налоги"},
    {"id": "family", "name": "Семья"},
    {"id": "work", "name": "Работа"},
    {"id": "important", "name": "Важные"},
]

SORT_FILTERS = [
    {"id": "new", "name": "Новые"},
    {"id": "priority", "name": "По приоритету"},
]

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
PRIORITY_META = {
    "high": ("Срочно", "red"),
    "medium": ("Важно", "orange"),
    "low": ("Информация", "blue"),
}
CATEGORY_TONES = {
    "taxes": "purple",
    "home": "cyan",
    "docs": "blue",
    "family": "green",
    "work": "orange",
}


def _priority_badge(law: dict) -> ft.Control:
    label, tone = PRIORITY_META.get(law.get("priority"), ("Информация", "blue"))
    return badge(label, tone)


def _category_badge(law: dict) -> ft.Control:
    category_id = law.get("category", "")
    return badge(law.get("category_name") or category_id or "Категория", CATEGORY_TONES.get(category_id, "blue"))


def _initial_icon(law: dict, size: int = 48) -> ft.Container:
    title = law.get("category_name") or law.get("title") or "З"
    tone = CATEGORY_TONES.get(law.get("category", ""), "blue")
    icon_bg, icon_fg = {
        "blue": (APP_COLORS["active"], APP_COLORS["blue_text"]),
        "green": (APP_COLORS["secondary_light"], APP_COLORS["green"]),
        "orange": (APP_COLORS["warning_light"], APP_COLORS["orange"]),
        "purple": (APP_COLORS["surface3"], APP_COLORS["purple"]),
        "cyan": (APP_COLORS["surface3"], APP_COLORS["cyan"]),
    }.get(tone, (APP_COLORS["active"], APP_COLORS["blue_text"]))
    return ft.Container(
        width=size,
        height=size,
        border_radius=size // 2,
        bgcolor=icon_bg,
        alignment=ft.Alignment(0, 0),
        content=ft.Text(
            title[:1].upper(),
            size=16 if size >= 44 else 13,
            weight=ft.FontWeight.W_900,
            color=icon_fg,
        ),
    )


def _parse_date(value: str) -> datetime:
    try:
        return datetime.strptime(value or "", "%d.%m.%Y")
    except ValueError:
        return datetime.min


def _matches_law(law: dict, query: str) -> bool:
    if not query:
        return True
    haystack = " ".join(
        [
            law.get("title", ""),
            law.get("short", ""),
            law.get("target", ""),
            law.get("category_name", ""),
            law.get("what_to_do", ""),
            law.get("source_url", ""),
            " ".join(law.get("related_scenarios", []) or []),
            " ".join(law.get("related_problems", []) or []),
        ]
    ).lower()
    return query.lower() in haystack


def _filtered_laws(laws: list[dict], query: str, category_id: str, sort_mode: str) -> list[dict]:
    normalized_query = (query or "").strip()
    filtered = [
        law
        for law in laws
        if (
            category_id == "all"
            or (category_id == "important" and law.get("priority") in {"high", "medium"})
            or law.get("category") == category_id
        )
        and _matches_law(law, normalized_query)
    ]
    if sort_mode == "priority":
        return sorted(
            filtered,
            key=lambda law: (PRIORITY_ORDER.get(law.get("priority"), 3), -_parse_date(law.get("date", "")).toordinal()),
        )
    return sorted(filtered, key=lambda law: _parse_date(law.get("date", "")), reverse=True)


def _source_name(law: dict) -> str:
    source = law.get("source_url") or ""
    if "nalog.gov.by" in source:
        return "Налоговая"
    if "mintrud.gov.by" in source:
        return "Минтруда"
    if "portal.gov.by" in source:
        return "Госпортал"
    if "pravo.by" in source:
        return "Pravo.by"
    return "Источник"


def _stat_tile(label: str, value: str | int, subtitle: str, icon, tone: str = "blue", compact: bool = False) -> ft.Container:
    icon_color = APP_COLORS[tone] if tone in APP_COLORS else APP_COLORS["blue"]
    if compact:
        return app_card(
            ft.Column(
                spacing=4,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    icon_circle(icon, size=34, color=icon_color),
                    ft.Text(str(value), size=21, weight=ft.FontWeight.W_900, color=APP_COLORS["text"], text_align=ft.TextAlign.CENTER),
                    ft.Text(label, size=10, weight=ft.FontWeight.W_800, color=APP_COLORS["muted"], text_align=ft.TextAlign.CENTER, max_lines=1),
                    ft.Text(subtitle, size=9, color=APP_COLORS["muted2"], text_align=ft.TextAlign.CENTER, max_lines=1),
                ],
            ),
            padding=10,
        )
    return app_card(
        ft.Row(
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                icon_circle(icon, size=42, color=icon_color),
                ft.Column(
                    spacing=1,
                    controls=[
                        ft.Text(str(value), size=24, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                        ft.Text(label, size=12, weight=ft.FontWeight.W_800, color=APP_COLORS["muted"]),
                        ft.Text(subtitle, size=11, color=APP_COLORS["muted2"]),
                    ],
                ),
            ],
        ),
        padding=16,
    )


def _stats_row(laws: list[dict], important_laws: list[dict], desktop: bool) -> ft.Control:
    source_count = len({law.get("source_url", "") for law in laws if law.get("source_url")})
    stats = [
        ("Новых", len(laws), "за 30 дней", ft.Icons.UPDATE_OUTLINED, "blue"),
        ("Важных", sum(1 for law in laws if law.get("priority") == "high"), "для профиля", ft.Icons.PRIORITY_HIGH_OUTLINED, "red"),
        ("Для меня", len(important_laws), "релевантных", ft.Icons.STAR_OUTLINE, "green"),
        ("Источников", source_count, "официальных", ft.Icons.VERIFIED_OUTLINED, "cyan"),
    ]
    controls = [_stat_tile(label, value, subtitle, icon, tone, compact=not desktop) for label, value, subtitle, icon, tone in stats]
    if desktop:
        return ft.Row(spacing=14, controls=[ft.Container(expand=True, content=control) for control in controls])
    return ft.Row(spacing=10, run_spacing=10, wrap=True, controls=[ft.Container(width=164, content=control) for control in controls[:3]])


def _law_card(law: dict, open_law, desktop: bool) -> ft.Container:
    is_urgent = law.get("priority") == "high"
    is_new = law.get("processing_status") == "new"
    meta = f"{law.get('target', 'Кого касается')} · {law.get('date', 'без даты')} · {_source_name(law)}"
    badges: list[ft.Control] = [_category_badge(law), _priority_badge(law)]
    if is_new:
        badges.append(badge("Новое", "new"))
    card_content = ft.Row(
        spacing=16,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            _initial_icon(law, 52 if desktop else 46),
            ft.Column(
                spacing=8,
                expand=True,
                controls=[
                    ft.Row(wrap=True, spacing=8, run_spacing=8, controls=badges),
                    ft.Text(
                        law.get("title", "Без названия"),
                        size=20 if desktop else 17,
                        weight=ft.FontWeight.W_900,
                        color=APP_COLORS["text"],
                    ),
                    ft.Text(
                        law.get("short", ""),
                        size=14 if desktop else 13,
                        color=APP_COLORS["muted"],
                        max_lines=3 if desktop else 2,
                    ),
                    ft.Text(meta, size=12, color=APP_COLORS["muted2"], max_lines=2),
                ],
            ),
            ghost_button("Подробнее", icon=ft.Icons.ARROW_FORWARD, width=132, height=40) if desktop else ft.Icon(ft.Icons.CHEVRON_RIGHT, color=APP_COLORS["muted2"]),
        ],
    )
    return ft.Container(
        content=card_content,
        padding=20 if desktop else 16,
        border_radius=APP_RADIUS["card"],
        bgcolor=APP_COLORS["surface"],
        border=border_all(APP_COLORS["red"] if is_urgent else APP_COLORS["stroke2"], 2 if is_urgent else 1),
        shadow=card_shadow(),
        animate=ft.Animation(220, ft.AnimationCurve.EASE_OUT),
        on_click=lambda _: open_law(law.get("id")),
        ink=True,
    )


def _important_laws_card(laws: list[dict], open_law, desktop: bool) -> ft.Control:
    if not laws:
        return app_card(
            ft.Column(
                spacing=8,
                controls=[
                    ft.Text("Для меня", size=19, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                    ft.Text("Персональные апдейты появятся после заполнения профиля и активных ситуаций.", size=13, color=APP_COLORS["muted"]),
                ],
            ),
            padding=18,
            bgcolor=APP_COLORS["surface2"],
        )
    rows: list[ft.Control] = []
    for law in laws[:3]:
        rows.append(
            ft.Container(
                content=ft.Row(
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        _initial_icon(law, 34),
                        ft.Column(
                            spacing=2,
                            expand=True,
                            controls=[
                                ft.Text(law.get("title", "Без названия"), size=13, weight=ft.FontWeight.W_800, color=APP_COLORS["text"], max_lines=2),
                                ft.Text(law.get("what_to_do") or law.get("short", ""), size=11, color=APP_COLORS["muted2"], max_lines=2),
                            ],
                        ),
                    ],
                ),
                padding=12,
                border_radius=16,
                bgcolor=APP_COLORS["surface"],
                border=border_all(APP_COLORS["stroke2"]),
                on_click=lambda _, law_id=law.get("id"): open_law(law_id),
                ink=True,
            )
        )
    return app_card(
        ft.Column(
            spacing=12,
            controls=[
                ft.Text("Для меня", size=20 if desktop else 18, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                ft.Text("Подборка по интересам, активным ситуациям и приоритету.", size=12, color=APP_COLORS["muted"]),
                ft.Column(spacing=10, controls=rows),
            ],
        ),
        padding=18,
        bgcolor=APP_COLORS["surface2"],
    )


def _filter_chips(selected_category: str, on_category_change) -> ft.Row:
    return ft.Row(
        wrap=True,
        spacing=8,
        run_spacing=8,
        controls=[
            category_chip(
                item["name"],
                selected=item["id"] == selected_category,
                on_click=lambda _, category_id=item["id"]: on_category_change(category_id) if on_category_change else None,
            )
            for item in LAW_FILTERS
        ],
    )


def _sort_chips(sort_mode: str, on_sort_change) -> ft.Row:
    return ft.Row(
        wrap=True,
        spacing=8,
        run_spacing=8,
        controls=[
            category_chip(
                item["name"],
                selected=item["id"] == sort_mode,
                on_click=lambda _, sort_id=item["id"]: on_sort_change(sort_id) if on_sort_change else None,
            )
            for item in SORT_FILTERS
        ],
    )


def _quick_filter_row(selected_category: str, sort_mode: str, on_category_change, on_sort_change) -> ft.Control:
    filter_rows = [
        ("Категория", next((item["name"] for item in LAW_FILTERS if item["id"] == selected_category), "Все"), ft.Icons.CATEGORY_OUTLINED),
        ("Период", "За 30 дней", ft.Icons.DATE_RANGE_OUTLINED),
        ("Сортировка", "Приоритет" if sort_mode == "priority" else "Новые", ft.Icons.SORT_OUTLINED),
        ("Релевантность", "Для меня", ft.Icons.STAR_OUTLINE),
    ]
    return app_card(
        ft.Column(
            spacing=12,
            controls=[
                ft.Text("Фильтры", size=20, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                ft.Column(
                    spacing=8,
                    controls=[
                        ft.Container(
                            padding=padding_symmetric(horizontal=12, vertical=9),
                            border_radius=14,
                            bgcolor=APP_COLORS["surface2"],
                            border=border_all(APP_COLORS["stroke2"]),
                            content=ft.Row(
                                spacing=8,
                                controls=[
                                    ft.Icon(icon, size=17, color=APP_COLORS["muted2"]),
                                    ft.Text(label, size=12, weight=ft.FontWeight.W_800, color=APP_COLORS["muted"], expand=True),
                                    ft.Text(value, size=12, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                                ],
                            ),
                        )
                        for label, value, icon in filter_rows
                    ],
                ),
                primary_button(
                    "Важные",
                    icon=ft.Icons.PRIORITY_HIGH_OUTLINED,
                    expand=True,
                    height=42,
                    on_click=lambda _: on_category_change("important") if on_category_change else None,
                ),
                ghost_button(
                    "По приоритету",
                    icon=ft.Icons.SORT_OUTLINED,
                    expand=True,
                    height=42,
                    on_click=lambda _: on_sort_change("priority") if on_sort_change else None,
                ),
            ],
        ),
        padding=18,
    )


def _how_to_read_card(desktop: bool) -> ft.Control:
    steps = ["Что изменилось", "Кого касается", "Что сделать", "Источник"]
    return app_card(
        ft.Column(
            spacing=12,
            controls=[
                ft.Text("Как читать апдейт", size=20 if desktop else 17, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                ft.Column(
                    spacing=8,
                    controls=[
                        ft.Row(
                            spacing=9,
                            controls=[
                                ft.Container(
                                    width=24,
                                    height=24,
                                    border_radius=12,
                                    bgcolor=APP_COLORS["active"],
                                    alignment=ft.Alignment(0, 0),
                                    content=ft.Text(str(index), size=12, weight=ft.FontWeight.W_900, color=APP_COLORS["blue_text"]),
                                ),
                                ft.Text(step, size=13, color=APP_COLORS["text"], expand=True),
                            ],
                        )
                        for index, step in enumerate(steps, start=1)
                    ],
                ),
                ghost_button("Открыть пример", icon=ft.Icons.ARROW_FORWARD, expand=True, height=40),
            ],
        ),
        padding=18,
    )


def _empty_state() -> ft.Container:
    return empty_state_card(
        "Ничего не найдено",
        "Попробуйте изменить фильтр, сортировку или поисковый запрос.",
        icon=ft.Icons.MANAGE_SEARCH_OUTLINED,
    )


def _desktop_laws(
    open_law,
    query: str,
    selected_category: str,
    sort_mode: str,
    on_query_change,
    on_category_change,
    on_sort_change,
    laws: list[dict],
    important_laws: list[dict],
) -> ft.Control:
    filtered = _filtered_laws(laws, query, selected_category, sort_mode)
    right_column = ft.Container(
        width=292,
        content=ft.Column(
            spacing=16,
            controls=[
                _important_laws_card(important_laws, open_law, True),
                _quick_filter_row(selected_category, sort_mode, on_category_change, on_sort_change),
                _how_to_read_card(True),
            ],
        ),
    )
    main_column = ft.Container(
        expand=True,
        content=ft.Column(
            spacing=18,
            controls=[
                page_heading(
                    "Закон-апдейты",
                    "Изменения законодательства простым языком: что изменилось, кого касается и что сделать.",
                    actions=[
                        icon_circle(ft.Icons.TEXT_FIELDS, size=42, color=APP_COLORS["blue"]),
                        icon_circle(ft.Icons.NOTIFICATIONS_NONE_OUTLINED, size=42, color=APP_COLORS["blue"]),
                    ],
                ),
                search_box(
                    value=query,
                    hint="Поиск по законам, категориям, источникам и датам...",
                    on_change=lambda event: on_query_change(event.control.value) if on_query_change else None,
                ),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    controls=[
                        ft.Container(expand=True, content=_filter_chips(selected_category, on_category_change)),
                        _sort_chips(sort_mode, on_sort_change),
                    ],
                ),
                _stats_row(laws, important_laws, True),
                ft.Row(
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.END,
                    controls=[
                        ft.Text("Лента изменений", size=26, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                        ft.Text("понятные объяснения", size=13, color=APP_COLORS["muted"], expand=True),
                    ],
                ),
                ft.Column(
                    spacing=14,
                    controls=[_law_card(law, open_law, True) for law in filtered] or [_empty_state()],
                ),
            ],
        ),
    )
    return desktop_content(ft.Row(spacing=18, vertical_alignment=ft.CrossAxisAlignment.START, controls=[main_column, right_column]), width=1120, top=44)


def _mobile_laws(
    open_law,
    query: str,
    selected_category: str,
    sort_mode: str,
    on_query_change,
    on_category_change,
    on_sort_change,
    laws: list[dict],
    important_laws: list[dict],
) -> ft.Control:
    filtered = _filtered_laws(laws, query, selected_category, sort_mode)
    primary_feed = important_laws if selected_category == "all" and important_laws else filtered
    return ft.Container(
        width=343,
        content=ft.Column(
            spacing=16,
            controls=[
                page_heading("Закон-апдейты", "Новые правила простым языком."),
                search_box(
                    value=query,
                    hint="Поиск по законам...",
                    on_change=lambda event: on_query_change(event.control.value) if on_query_change else None,
                    expand=False,
                ),
                _filter_chips(selected_category, on_category_change),
                _sort_chips(sort_mode, on_sort_change),
                _stats_row(laws, important_laws, False),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text("Для меня" if primary_feed == important_laws else "Лента", size=22, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                        ghost_button("Фильтры", icon=ft.Icons.TUNE, height=38, on_click=lambda _: on_sort_change("priority") if on_sort_change else None),
                    ],
                ),
                ft.Column(
                    spacing=12,
                    controls=[_law_card(law, open_law, False) for law in primary_feed] or [_empty_state()],
                ),
                _how_to_read_card(False),
            ],
        ),
    )


def build_legal_updates_page(
    open_law,
    is_desktop: bool = False,
    query: str = "",
    selected_category: str = "all",
    on_query_change=None,
    on_category_change=None,
    laws: list[dict] | None = None,
    important_laws: list[dict] | None = None,
    sort_mode: str = "new",
    on_sort_change=None,
) -> ft.Control:
    selected = selected_category if selected_category in {item["id"] for item in LAW_FILTERS} else "all"
    sort_selected = sort_mode if sort_mode in {item["id"] for item in SORT_FILTERS} else "new"
    dataset = laws or LEGAL_UPDATES
    important_dataset = important_laws or []
    if is_desktop:
        return _desktop_laws(
            open_law,
            query,
            selected,
            sort_selected,
            on_query_change,
            on_category_change,
            on_sort_change,
            dataset,
            important_dataset,
        )
    return _mobile_laws(
        open_law,
        query,
        selected,
        sort_selected,
        on_query_change,
        on_category_change,
        on_sort_change,
        dataset,
        important_dataset,
    )
