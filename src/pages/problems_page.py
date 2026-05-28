from __future__ import annotations

import flet as ft

from components.buttons import ghost_button
from components.cards import (
    app_card,
    badge,
    category_chip,
    empty_state_card,
    icon_circle,
    page_heading,
    search_box,
    section_title,
)
from components.layout import desktop_content
from data.mock_data import PROBLEMS
from theme.app_theme import APP_COLORS, APP_RADIUS, RADIUS, SPACING, border_all, get_badge_palette, padding_symmetric


FILTER_CATEGORIES = [
    {"id": "all", "name": "Все"},
    {"id": "docs", "name": "Документы"},
    {"id": "home", "name": "ЖКХ"},
    {"id": "taxes", "name": "Налоги"},
    {"id": "family", "name": "Семья"},
    {"id": "work", "name": "Работа"},
    {"id": "health", "name": "Здоровье"},
    {"id": "auto", "name": "Авто"},
    {"id": "business", "name": "Бизнес/ИП"},
]

CATEGORY_META = {
    "docs": {"icon": ft.Icons.ARTICLE_OUTLINED, "tone": "blue", "initial": "ID"},
    "home": {"icon": ft.Icons.HOME_WORK_OUTLINED, "tone": "cyan", "initial": "Ж"},
    "taxes": {"icon": ft.Icons.ACCOUNT_BALANCE_OUTLINED, "tone": "orange", "initial": "Н"},
    "family": {"icon": ft.Icons.FAMILY_RESTROOM_OUTLINED, "tone": "green", "initial": "С"},
    "work": {"icon": ft.Icons.WORK_OUTLINE, "tone": "purple", "initial": "Р"},
    "health": {"icon": ft.Icons.MEDICAL_SERVICES_OUTLINED, "tone": "red", "initial": "М"},
    "auto": {"icon": ft.Icons.DIRECTIONS_CAR_OUTLINED, "tone": "cyan", "initial": "А"},
    "business": {"icon": ft.Icons.BUSINESS_CENTER_OUTLINED, "tone": "purple", "initial": "ИП"},
}

TIME_BY_PROBLEM = {
    "lost-passport": "10-20 дней",
    "med-book": "3-10 дней",
    "no-utility-bill": "1-3 дня",
    "tax-error": "7-15 дней",
    "moving": "до 7 дней",
    "childbirth": "7-14 дней",
    "dismissal": "1-5 дней",
    "divorce": "от 1 месяца",
    "sick-leave": "1-3 дня",
    "open-ip": "1-5 дней",
    "auto-registration": "1-7 дней",
    "alimony": "от 10 дней",
    "buy-housing": "2-6 недель",
    "benefits": "7-14 дней",
}

QUICK_CATEGORIES = ["docs", "home", "taxes", "family", "work", "health"]


def _category_name(category_id: str) -> str:
    for item in FILTER_CATEGORIES:
        if item["id"] == category_id:
            return item["name"]
    return "Категория"


def _category_count(category_id: str) -> int:
    if category_id == "all":
        return len(PROBLEMS)
    return len([problem for problem in PROBLEMS if problem.get("category") == category_id])


def _category_meta(category_id: str) -> dict:
    return CATEGORY_META.get(category_id, {"icon": ft.Icons.CATEGORY_OUTLINED, "tone": "gray", "initial": "?"})


def _tone_colors(tone: str) -> tuple[str, str]:
    return get_badge_palette().get(tone, get_badge_palette()["gray"])


def _matches_query(problem: dict, query: str) -> bool:
    if not query:
        return True
    haystack = " ".join(
        [
            problem.get("title", ""),
            problem.get("description", ""),
            problem.get("category_name", ""),
            problem.get("category", ""),
            problem.get("urgency", ""),
        ]
    ).lower()
    return query.lower() in haystack


def _filtered_problems(query: str, category_id: str) -> list[dict]:
    clean_query = query.strip()
    return [
        problem
        for problem in PROBLEMS
        if (category_id == "all" or problem.get("category") == category_id)
        and _matches_query(problem, clean_query)
    ]


def _difficulty(problem: dict) -> tuple[str, str]:
    urgency = problem.get("urgency", "")
    if urgency == "Важно":
        return "Средняя", "orange"
    if problem.get("category") in {"business", "family"}:
        return "Средняя", "orange"
    return "Лёгкая", "green"


def _category_icon(category_id: str, size: int = 48) -> ft.Container:
    meta = _category_meta(category_id)
    bgcolor, color = _tone_colors(meta["tone"])
    return ft.Container(
        width=size,
        height=size,
        border_radius=size // 2,
        bgcolor=bgcolor,
        alignment=ft.Alignment(0, 0),
        content=ft.Icon(meta["icon"], size=max(18, size // 2), color=color),
    )


def _category_initial(category_id: str, size: int = 46) -> ft.Container:
    meta = _category_meta(category_id)
    bgcolor, color = _tone_colors(meta["tone"])
    return ft.Container(
        width=size,
        height=size,
        border_radius=size // 2,
        bgcolor=bgcolor,
        alignment=ft.Alignment(0, 0),
        content=ft.Text(meta["initial"], size=14, weight=ft.FontWeight.W_900, color=color),
    )


def _small_meta(icon: str, text: str) -> ft.Row:
    return ft.Row(
        spacing=5,
        tight=True,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Icon(icon, size=14, color=APP_COLORS["muted2"]),
            ft.Text(text, size=13, weight=ft.FontWeight.W_800, color=APP_COLORS["muted"]),
        ],
    )


def _category_chips(selected_category: str, on_category_change) -> ft.Row:
    return ft.Row(
        wrap=True,
        spacing=10,
        run_spacing=10,
        controls=[
            category_chip(
                category["name"],
                selected=category["id"] == selected_category,
                on_click=lambda _, category_id=category["id"]: on_category_change(category_id) if on_category_change else None,
            )
            for category in FILTER_CATEGORIES
        ],
    )


def _quick_category_tile(category_id: str, on_category_change, *, width: int, height: int) -> ft.Container:
    count = _category_count(category_id)
    return ft.Container(
        width=width,
        content=app_card(
            ft.Column(
                spacing=8,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[
                    _category_icon(category_id, 50),
                    ft.Text(
                        _category_name(category_id),
                        size=16,
                        weight=ft.FontWeight.W_900,
                        color=APP_COLORS["text"],
                        text_align=ft.TextAlign.CENTER,
                        max_lines=2,
                    ),
                    ft.Text(
                        f"{count} проблем",
                        size=12,
                        weight=ft.FontWeight.W_800,
                        color=APP_COLORS["muted"],
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
            ),
            padding=14,
            height=height,
            animate=True,
        ),
        on_click=lambda _: on_category_change(category_id) if on_category_change else None,
        ink=True,
    )


def _quick_categories(on_category_change, *, desktop: bool) -> ft.Control:
    width = 132 if desktop else 152
    height = 132 if desktop else 124
    return ft.Row(
        spacing=12,
        run_spacing=12,
        wrap=True,
        controls=[
            _quick_category_tile(category_id, on_category_change, width=width, height=height)
            for category_id in QUICK_CATEGORIES
        ],
    )


def _problem_card(problem: dict, open_problem, *, width: int | None, index: int, compact: bool = False) -> ft.Container:
    category_id = problem.get("category", "")
    category_name = problem.get("category_name", _category_name(category_id))
    category_tone = _category_meta(category_id)["tone"]
    difficulty_label, difficulty_tone = _difficulty(problem)
    time_label = TIME_BY_PROBLEM.get(problem.get("id"), "3-7 дней")
    title_size = 18 if compact else 19
    description_size = 13 if compact else 14

    card_body = ft.Row(
        spacing=14,
        vertical_alignment=ft.CrossAxisAlignment.START,
        controls=[
            _category_initial(category_id, 50 if not compact else 44),
            ft.Column(
                spacing=9,
                expand=True,
                controls=[
                    ft.Row(
                        spacing=8,
                        run_spacing=8,
                        wrap=True,
                        controls=[badge(category_name, category_tone)],
                    ),
                    ft.Text(
                        problem.get("title", ""),
                        size=title_size,
                        weight=ft.FontWeight.W_900,
                        color=APP_COLORS["text"],
                        max_lines=2,
                    ),
                    ft.Text(
                        problem.get("description", ""),
                        size=description_size,
                        color=APP_COLORS["muted"],
                        max_lines=2,
                    ),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            _small_meta(ft.Icons.TIMER_OUTLINED, time_label),
                            badge(difficulty_label, difficulty_tone),
                        ],
                    ),
                ],
            ),
            ft.Icon(ft.Icons.CHEVRON_RIGHT, size=22, color=APP_COLORS["muted2"]),
        ],
    )

    return ft.Container(
        width=width,
        content=app_card(
            card_body,
            padding=18,
            height=152 if not compact else None,
            animate=True,
        ),
        on_click=lambda _: open_problem(problem["id"]),
        ink=True,
        animate_opacity=ft.Animation(220 + index * 50, ft.AnimationCurve.EASE_OUT),
    )


def _skeleton_card(width: int | None) -> ft.Container:
    return app_card(
        ft.Column(
            spacing=12,
            controls=[
                ft.Row(
                    spacing=14,
                    controls=[
                        icon_circle(ft.Icons.ARTICLE_OUTLINED, bgcolor=APP_COLORS["surface2"], size=50),
                        ft.Column(
                            spacing=8,
                            expand=True,
                            controls=[
                                ft.Container(height=14, border_radius=7, bgcolor=APP_COLORS["surface2"]),
                                ft.Container(height=18, border_radius=9, bgcolor=APP_COLORS["surface2"]),
                                ft.Container(height=12, border_radius=6, bgcolor=APP_COLORS["surface2"]),
                            ],
                        ),
                    ],
                )
            ],
        ),
        width=width,
        height=138,
        bgcolor=APP_COLORS["surface"],
        border_color=APP_COLORS["stroke2"],
        animate=True,
    )


def _empty_state() -> ft.Container:
    return empty_state_card(
        "Ничего не найдено",
        "Попробуйте изменить запрос или выбрать другую категорию.",
        icon=ft.Icons.SEARCH_OFF_OUTLINED,
    )


def _filter_hint_card(selected_category: str, total_count: int) -> ft.Container:
    rows = [
        ("Регион", "Минск"),
        ("Категория", _category_name(selected_category)),
        ("Сложность", "Любая"),
        ("Срок", "До месяца"),
    ]
    return app_card(
        ft.Column(
            spacing=13,
            controls=[
                ft.Row(
                    spacing=10,
                    controls=[
                        ft.Icon(ft.Icons.TUNE_OUTLINED, size=20, color=APP_COLORS["blue"]),
                        ft.Text("Фильтры каталога", size=20, weight=ft.FontWeight.W_900, color=APP_COLORS["text"], expand=True),
                    ],
                ),
                ft.Text(f"Найдено: {total_count}", size=13, color=APP_COLORS["muted"]),
                ft.Column(
                    spacing=9,
                    controls=[
                        ft.Container(
                            padding=padding_symmetric(horizontal=14, vertical=10),
                            border_radius=RADIUS["md"],
                            bgcolor=APP_COLORS["surface2"],
                            border=border_all(APP_COLORS["stroke2"]),
                            content=ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text(label, size=13, weight=ft.FontWeight.W_800, color=APP_COLORS["muted"]),
                                    ft.Text(value, size=13, weight=ft.FontWeight.W_900, color=APP_COLORS["text"], max_lines=1),
                                ],
                            ),
                        )
                        for label, value in rows
                    ],
                ),
            ],
        ),
        padding=20,
    )


def _problem_contents_card() -> ft.Container:
    items = [
        "Что делать сейчас",
        "Пошаговый план",
        "Документы и сроки",
        "Куда обращаться",
        "Частые ошибки",
    ]
    return app_card(
        ft.Column(
            spacing=14,
            controls=[
                ft.Text("Что есть в карточке", size=20, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                ft.Column(
                    spacing=10,
                    controls=[
                        ft.Row(
                            spacing=10,
                            controls=[
                                ft.Icon(ft.Icons.CHECK, size=16, color=APP_COLORS["blue"]),
                                ft.Text(item, size=14, color=APP_COLORS["muted"], expand=True),
                            ],
                        )
                        for item in items
                    ],
                ),
            ],
        ),
        padding=20,
    )


def _side_problem_list(title: str, problems: list[dict], open_problem, icon: str) -> ft.Container:
    return app_card(
        ft.Column(
            spacing=12,
            controls=[
                ft.Row(
                    spacing=10,
                    controls=[
                        ft.Icon(icon, size=20, color=APP_COLORS["blue"]),
                        ft.Text(title, size=19, weight=ft.FontWeight.W_900, color=APP_COLORS["text"], expand=True),
                    ],
                ),
                ft.Column(
                    spacing=8,
                    controls=[
                        ft.Container(
                            padding=padding_symmetric(horizontal=12, vertical=10),
                            border_radius=RADIUS["md"],
                            bgcolor=APP_COLORS["surface2"],
                            border=border_all(APP_COLORS["stroke2"]),
                            on_click=lambda _, problem_id=problem["id"]: open_problem(problem_id),
                            ink=True,
                            content=ft.Row(
                                spacing=9,
                                controls=[
                                    _category_initial(problem.get("category", ""), 32),
                                    ft.Column(
                                        spacing=2,
                                        expand=True,
                                        controls=[
                                            ft.Text(problem.get("title", ""), size=13, weight=ft.FontWeight.W_900, color=APP_COLORS["text"], max_lines=2),
                                            ft.Text(problem.get("category_name", ""), size=11, color=APP_COLORS["muted"], max_lines=1),
                                        ],
                                    ),
                                ],
                            ),
                        )
                        for problem in problems
                    ],
                ),
            ],
        ),
        padding=18,
    )


def _desktop_problem_grid(problems: list[dict], open_problem) -> ft.Control:
    if not problems:
        return _empty_state()
    if problems is None:
        return ft.Row(spacing=14, run_spacing=14, wrap=True, controls=[_skeleton_card(378) for _ in range(3)])
    return ft.Row(
        spacing=14,
        run_spacing=14,
        wrap=True,
        controls=[
            _problem_card(problem, open_problem, width=378, index=index)
            for index, problem in enumerate(problems)
        ],
    )


def _desktop_problems(open_problem, query: str, selected_category: str, on_query_change, on_category_change, go_to=None) -> ft.Control:
    problems = _filtered_problems(query, selected_category)
    total_label = f"{len(problems)} карточек"
    popular = PROBLEMS[:3]
    recent = [PROBLEMS[index] for index in (3, 4, 5) if index < len(PROBLEMS)]

    left_content = ft.Column(
        spacing=SPACING["xl"],
        controls=[
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.END,
                controls=[
                    page_heading(
                        "Каталог проблем",
                        "Найдите понятный план действий по жизненной или бытовой проблеме.",
                    ),
                    ghost_button(
                        "Расширенный поиск",
                        icon=ft.Icons.MANAGE_SEARCH_OUTLINED,
                        on_click=lambda _: go_to("/search") if go_to else None,
                        height=40,
                    ),
                ],
            ),
            search_box(
                value=query,
                hint="Поиск: паспорт, ЖКХ, налог, регистрация, медкнижка...",
                on_change=lambda event: on_query_change(event.control.value) if on_query_change else None,
                on_submit=lambda event: on_query_change(event.control.value) if on_query_change else None,
            ),
            _category_chips(selected_category, on_category_change),
            ft.Column(
                spacing=14,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            section_title("Быстрые категории"),
                            ft.Text("По самым частым обращениям", size=13, color=APP_COLORS["muted"]),
                        ],
                    ),
                    _quick_categories(on_category_change, desktop=True),
                ],
            ),
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Row(
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.END,
                        controls=[
                            ft.Text("Все проблемы", size=25, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                            ft.Text(total_label, size=14, weight=ft.FontWeight.W_800, color=APP_COLORS["muted"]),
                        ],
                    ),
                    ft.Row(spacing=8, controls=[badge("Новые", "gray"), badge("Важные", "blue")]),
                ],
            ),
            _desktop_problem_grid(problems, open_problem),
        ],
    )

    right_content = ft.Column(
        spacing=18,
        controls=[
            _filter_hint_card(selected_category, len(problems)),
            _side_problem_list("Популярные", popular, open_problem, ft.Icons.WHATSHOT_OUTLINED),
            _side_problem_list("Недавно решённые", recent, open_problem, ft.Icons.HISTORY_OUTLINED),
            _problem_contents_card(),
        ],
    )

    return desktop_content(
        ft.Row(
            spacing=24,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                ft.Container(width=790, content=left_content),
                ft.Container(width=306, content=right_content),
            ],
        ),
        width=1120,
        top=42,
    )


def _mobile_filter_row(selected_category: str, count: int) -> ft.Row:
    category_text = _category_name(selected_category)
    return ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Row(spacing=8, controls=[badge("Важные", "blue"), badge("До месяца", "gray")]),
            ft.Text(str(count), size=14, weight=ft.FontWeight.W_900, color=APP_COLORS["muted"]),
            ft.Text(category_text, size=12, weight=ft.FontWeight.W_800, color=APP_COLORS["muted"], max_lines=1),
        ],
    )


def _mobile_page_header() -> ft.Column:
    return ft.Column(
        spacing=7,
        controls=[
            ft.Text("Каталог проблем", size=30, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
            ft.Text(
                "Выберите тему, чтобы открыть пошаговую карточку.",
                size=14,
                color=APP_COLORS["muted"],
                max_lines=2,
            ),
        ],
    )


def _mobile_problems(open_problem, query: str, selected_category: str, on_query_change, on_category_change) -> ft.Control:
    problems = _filtered_problems(query, selected_category)
    problem_controls: list[ft.Control] = []
    for index, problem in enumerate(problems):
        problem_controls.append(_problem_card(problem, open_problem, width=None, index=index, compact=True))
    if not problem_controls:
        problem_controls.append(_empty_state())

    return ft.Container(
        width=340,
        content=ft.Column(
            spacing=18,
            controls=[
                _mobile_page_header(),
                search_box(
                    value=query,
                    hint="Найдите проблему: паспорт, ЖКХ, налоги...",
                    on_change=lambda event: on_query_change(event.control.value) if on_query_change else None,
                    on_submit=lambda event: on_query_change(event.control.value) if on_query_change else None,
                ),
                _category_chips(selected_category, on_category_change),
                ft.Column(
                    spacing=12,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text("Быстрые категории", size=22, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                                ft.Text("Все", size=13, weight=ft.FontWeight.W_900, color=APP_COLORS["blue_text"]),
                            ],
                        ),
                        _quick_categories(on_category_change, desktop=False),
                    ],
                ),
                _mobile_filter_row(selected_category, len(problems)),
                ft.Column(
                    spacing=12,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text("Все проблемы", size=22, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                                ft.Text(f"{len(problems)}", size=14, weight=ft.FontWeight.W_900, color=APP_COLORS["muted"]),
                            ],
                        ),
                        ft.Column(spacing=12, controls=problem_controls),
                        ghost_button("Вернуться к общему списку", on_click=lambda _: on_category_change("all") if on_category_change else None, width=270),
                    ],
                ),
            ],
        ),
    )


def build_problems_page(
    open_problem,
    is_desktop: bool = False,
    query: str = "",
    selected_category: str = "all",
    on_query_change=None,
    on_category_change=None,
    go_to=None,
) -> ft.Control:
    selected = selected_category if selected_category in {category["id"] for category in FILTER_CATEGORIES} else "all"
    if is_desktop:
        return _desktop_problems(open_problem, query, selected, on_query_change, on_category_change, go_to=go_to)
    return _mobile_problems(open_problem, query, selected, on_query_change, on_category_change)
