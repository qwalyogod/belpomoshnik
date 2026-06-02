from __future__ import annotations

import flet as ft

from components.buttons import ghost_button
from components.cards import app_card, badge, category_chip, empty_state_card, icon_circle, search_box
from components.layout import desktop_content
from data.mock_data import (
    DOCUMENTS,
    INSTITUTIONS,
    LEGAL_UPDATES,
    PROBLEMS,
    SCENARIO_TEMPLATES,
    SITUATIONS,
)
from theme.app_theme import APP_COLORS, APP_RADIUS, SPACING, border_all, padding_symmetric, ts


FILTERS = [
    ("all", "Всё"),
    ("problems", "Проблемы"),
    ("scenarios", "Сценарии"),
    ("situations", "Ситуации"),
    ("documents", "Документы"),
    ("laws", "Закон-апдейты"),
    ("institutions", "Учреждения"),
]

RECENT_SEARCHES = ["Замена паспорта", "Переезд", "Медкнижка"]

POPULAR_REQUESTS = [
    {
        "title": "Потеря паспорта",
        "subtitle": "документы",
        "icon": ft.Icons.BADGE_OUTLINED,
        "route": "/problem/lost-passport",
        "tone": "blue",
    },
    {
        "title": "Оплата ЖКХ",
        "subtitle": "сроки",
        "icon": ft.Icons.HOME_WORK_OUTLINED,
        "route": "/utility",
        "tone": "cyan",
    },
    {
        "title": "Рождение ребёнка",
        "subtitle": "семья",
        "icon": ft.Icons.CHILD_CARE_OUTLINED,
        "route": "/scenarios/childbirth",
        "tone": "orange",
    },
    {
        "title": "Налог на имущество",
        "subtitle": "налоги",
        "icon": ft.Icons.ACCOUNT_BALANCE_OUTLINED,
        "route": "/taxes",
        "tone": "orange",
    },
    {
        "title": "Смена регистрации",
        "subtitle": "переезд",
        "icon": ft.Icons.PLACE_OUTLINED,
        "route": "/scenarios/moving",
        "tone": "purple",
    },
]

QUICK_FILTERS = [
    ("Рядом со мной", "По адресу из профиля", ft.Icons.LOCATION_ON_OUTLINED),
    ("Только важные", "Срочные и ключевые материалы", ft.Icons.STAR_BORDER_OUTLINED),
    ("С последним обновлением", "Проверенные источники", ft.Icons.UPDATE_OUTLINED),
    ("Онлайн-услуги", "Порталы и электронные сервисы", ft.Icons.PUBLIC_OUTLINED),
]


def _haystack(values: list[str]) -> str:
    return " ".join([str(value or "") for value in values]).lower()


def _matches(query: str, values: list[str]) -> bool:
    normalized = (query or "").strip().lower()
    if not normalized:
        return True
    return normalized in _haystack(values)


def _filter_chips(selected_filter: str, on_filter_change) -> ft.Row:
    selected = selected_filter if selected_filter in {item[0] for item in FILTERS} else "all"
    return ft.Row(
        wrap=True,
        spacing=10,
        run_spacing=10,
        controls=[
            category_chip(
                label,
                selected=key == selected,
                on_click=lambda _, filter_key=key: on_filter_change(filter_key) if on_filter_change else None,
            )
            for key, label in FILTERS
        ],
    )


def _recent_searches(on_query_change) -> ft.Control:
    chips: list[ft.Control] = []
    for item in RECENT_SEARCHES:
        chips.append(
            ft.Container(
                ink=True,
                on_click=lambda _, value=item: on_query_change(value) if on_query_change else None,
                border_radius=18,
                bgcolor=APP_COLORS["surface2"],
                border=border_all(APP_COLORS["stroke2"]),
                padding=padding_symmetric(horizontal=12, vertical=8),
                content=ft.Row(
                    spacing=6,
                    controls=[
                        ft.Icon(ft.Icons.HISTORY_OUTLINED, size=ts(16), color=APP_COLORS["muted2"]),
                        ft.Text(item, size=ts(13), weight=ft.FontWeight.W_700, color=APP_COLORS["text"]),
                    ],
                ),
            )
        )
    return ft.Column(
        spacing=10,
        controls=[
            ft.Text("Недавние поиски", size=ts(16), weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
            ft.Row(wrap=True, spacing=8, run_spacing=8, controls=chips),
        ],
    )


def _popular_requests(go_to, desktop: bool) -> ft.Control:
    cards: list[ft.Control] = []
    for item in POPULAR_REQUESTS:
        cards.append(
            ft.Container(
                ink=True,
                on_click=lambda _, route=item["route"]: go_to(route) if go_to else None,
                width=128 if desktop else 92,
                height=108 if desktop else 92,
                border_radius=APP_RADIUS["card"],
                bgcolor=APP_COLORS["surface"],
                border=border_all(APP_COLORS["stroke2"]),
                padding=12,
                content=ft.Column(
                    spacing=8,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        icon_circle(item["icon"], size=36 if desktop else 30, color=APP_COLORS["blue"], bgcolor=APP_COLORS["active"]),
                        ft.Text(
                            item["title"],
                            size=ts(12) if desktop else 10,
                            weight=ft.FontWeight.W_800,
                            color=APP_COLORS["text"],
                            text_align=ft.TextAlign.CENTER,
                            max_lines=2,
                        ),
                    ],
                ),
            )
        )
    return ft.Column(
        spacing=12,
        controls=[
            ft.Text("Популярные запросы", size=ts(18) if desktop else 16, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
            ft.Row(wrap=True, spacing=12 if desktop else 8, run_spacing=8, controls=cards),
        ],
    )


_QUICK_FILTER_ACTIONS = [
    ("institutions", ""),
    ("laws", ""),
    ("laws", ""),
    ("institutions", "онлайн"),
]


def _quick_filters(on_filter_change=None, on_query_change=None) -> ft.Control:
    def make_handler(filter_key: str, query: str):
        def handle(_):
            if query and on_query_change:
                on_query_change(query)
            if filter_key and on_filter_change:
                on_filter_change(filter_key)
        return handle

    return app_card(
        ft.Column(
            spacing=8,
            controls=[
                ft.Text("Быстрые фильтры", size=ts(16), weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                *[
                    ft.Container(
                        ink=True,
                        border_radius=16,
                        padding=padding_symmetric(horizontal=10, vertical=10),
                        on_click=make_handler(fk, fq),
                        content=ft.Row(
                            spacing=10,
                            controls=[
                                ft.Icon(icon, size=ts(19), color=APP_COLORS["blue"]),
                                ft.Column(
                                    spacing=2,
                                    expand=True,
                                    controls=[
                                        ft.Text(title, size=ts(13), weight=ft.FontWeight.W_800, color=APP_COLORS["text"]),
                                        ft.Text(subtitle, size=ts(11), color=APP_COLORS["muted"], max_lines=1),
                                    ],
                                ),
                                ft.Icon(ft.Icons.CHEVRON_RIGHT, size=ts(18), color=APP_COLORS["muted2"]),
                            ],
                        ),
                    )
                    for (title, subtitle, icon), (fk, fq) in zip(QUICK_FILTERS, _QUICK_FILTER_ACTIONS)
                ],
            ],
        ),
        padding=16,
    )


def _problems(query: str) -> list[dict]:
    return [
        item
        for item in PROBLEMS
        if _matches(query, [item.get("title", ""), item.get("description", ""), item.get("category_name", "")])
    ][:5]


def _scenarios(query: str) -> list[dict]:
    return [
        item
        for item in SCENARIO_TEMPLATES
        if _matches(
            query,
            [
                item.get("title", ""),
                item.get("description", ""),
                item.get("short_description", ""),
                item.get("category", ""),
                item.get("difficulty", ""),
            ],
        )
    ][:5]


def _situations(query: str, situations: list[dict]) -> list[dict]:
    source = situations or SITUATIONS
    return [
        item
        for item in source
        if _matches(query, [item.get("title", ""), item.get("status", "")])
    ][:5]


def _documents(query: str, documents: list[dict]) -> list[dict]:
    source = documents or DOCUMENTS
    return [
        item
        for item in source
        if _matches(
            query,
            [
                item.get("title", ""),
                item.get("type", ""),
                item.get("document_type", ""),
                item.get("status", ""),
                item.get("issuer", ""),
            ],
        )
    ][:5]


def _laws(query: str, laws: list[dict]) -> list[dict]:
    source = laws or LEGAL_UPDATES
    return [
        item
        for item in source
        if _matches(
            query,
            [
                item.get("title", ""),
                item.get("short", ""),
                item.get("description", ""),
                item.get("target", ""),
                item.get("category_name", ""),
            ],
        )
    ][:5]


def _institutions(query: str, institutions: list[dict]) -> list[dict]:
    source = institutions or INSTITUTIONS
    return [
        item
        for item in source
        if _matches(
            query,
            [
                item.get("short_name", ""),
                item.get("full_name", ""),
                item.get("institution_type", ""),
                item.get("city", ""),
                item.get("address", ""),
                " ".join(item.get("services", []) or []),
            ],
        )
    ][:5]


def _result_card(
    *,
    title: str,
    subtitle: str,
    meta: str,
    icon,
    tone: str,
    on_click=None,
    desktop: bool,
) -> ft.Container:
    return ft.Container(
        ink=True,
        on_click=on_click,
        width=246 if desktop else None,
        content=app_card(
            ft.Row(
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    icon_circle(icon, size=42, color=APP_COLORS["blue"], bgcolor=APP_COLORS["active"]),
                    ft.Column(
                        spacing=4,
                        expand=True,
                        controls=[
                            ft.Text(title, size=ts(15) if desktop else 14, weight=ft.FontWeight.W_900, color=APP_COLORS["text"], max_lines=1),
                            ft.Text(subtitle, size=ts(12), color=APP_COLORS["muted"], max_lines=2),
                            ft.Text(meta, size=ts(11), weight=ft.FontWeight.W_800, color=APP_COLORS["orange"], max_lines=1),
                        ],
                    ),
                    ft.Icon(ft.Icons.CHEVRON_RIGHT, size=ts(19), color=APP_COLORS["muted2"]),
                ],
            ),
            padding=13 if desktop else 12,
            animate=True,
        ),
    )


def _section(
    title: str,
    icon,
    items: list[ft.Control],
    show_all_route: str | None,
    go_to,
    desktop: bool,
) -> ft.Control:
    if not items:
        return ft.Container()
    title_row = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Row(
                spacing=9,
                controls=[
                    ft.Container(
                        width=26,
                        height=26,
                        border_radius=9,
                        bgcolor=APP_COLORS["active"],
                        alignment=ft.Alignment(0, 0),
                        content=ft.Icon(icon, size=ts(16), color=APP_COLORS["blue"]),
                    ),
                    ft.Text(title, size=ts(18) if desktop else 16, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                ],
            ),
            ghost_button("Смотреть все", height=36, on_click=lambda _: go_to(show_all_route) if go_to and show_all_route else None)
            if show_all_route
            else ft.Container(),
        ],
    )
    return ft.Column(
        spacing=12,
        controls=[
            title_row,
            ft.Row(wrap=True, spacing=12, run_spacing=12, controls=items),
        ],
    )


def _build_sections(
    query: str,
    selected_filter: str,
    go_to,
    open_problem,
    open_scenario,
    open_law,
    situations: list[dict],
    documents: list[dict],
    laws: list[dict],
    institutions: list[dict],
    desktop: bool,
) -> list[ft.Control]:
    selected = selected_filter if selected_filter in {item[0] for item in FILTERS} else "all"
    controls: list[ft.Control] = []

    if selected in {"all", "problems"}:
        items = [
            _result_card(
                title=item.get("title", "Проблема"),
                subtitle=item.get("description", ""),
                meta=item.get("urgency", "Важно"),
                icon=ft.Icons.ARTICLE_OUTLINED,
                tone="blue",
                on_click=lambda _, problem_id=item.get("id"): open_problem(problem_id) if open_problem else None,
                desktop=desktop,
            )
            for item in _problems(query)
        ]
        controls.append(_section("Проблемы", ft.Icons.ARTICLE_OUTLINED, items, "/problems", go_to, desktop))

    if selected in {"all", "scenarios"}:
        items = [
            _result_card(
                title=item.get("title", "Сценарий"),
                subtitle=f"{item.get('category', 'Категория')} · {item.get('estimated_duration', 'срок уточняется')}",
                meta=item.get("difficulty", "Средняя"),
                icon=ft.Icons.ROUTE_OUTLINED,
                tone="purple",
                on_click=lambda _, template_id=item.get("id"): open_scenario(template_id) if open_scenario else None,
                desktop=desktop,
            )
            for item in _scenarios(query)
        ]
        controls.append(_section("Жизненные сценарии", ft.Icons.ROUTE_OUTLINED, items, "/scenarios", go_to, desktop))

    if selected in {"all", "situations"}:
        items = [
            _result_card(
                title=item.get("title", "Ситуация"),
                subtitle=f"{item.get('status', 'В процессе')} · прогресс {item.get('progress', 0)}%",
                meta="личный план",
                icon=ft.Icons.TASK_ALT_OUTLINED,
                tone="green",
                on_click=lambda _, situation_id=item.get("id"): go_to(f"/situations/{situation_id}") if go_to else None,
                desktop=desktop,
            )
            for item in _situations(query, situations)
        ]
        controls.append(_section("Мои ситуации", ft.Icons.TASK_ALT_OUTLINED, items, "/situations", go_to, desktop))

    if selected in {"all", "documents"}:
        items = [
            _result_card(
                title=item.get("title", "Документ"),
                subtitle=item.get("type") or item.get("document_type") or item.get("issuer", "Личный документ"),
                meta=item.get("status", "активен"),
                icon=ft.Icons.DESCRIPTION_OUTLINED,
                tone="cyan",
                on_click=lambda _: go_to("/documents") if go_to else None,
                desktop=desktop,
            )
            for item in _documents(query, documents)
        ]
        controls.append(_section("Документы", ft.Icons.DESCRIPTION_OUTLINED, items, "/documents", go_to, desktop))

    if selected in {"all", "laws"}:
        items = [
            _result_card(
                title=item.get("title", "Закон-апдейт"),
                subtitle=item.get("short") or item.get("description", ""),
                meta=item.get("date", "дата уточняется"),
                icon=ft.Icons.BALANCE_OUTLINED,
                tone="orange",
                on_click=lambda _, law_id=item.get("id"): open_law(law_id) if open_law else None,
                desktop=desktop,
            )
            for item in _laws(query, laws)
        ]
        controls.append(_section("Закон-апдейты", ft.Icons.BALANCE_OUTLINED, items, "/legal-updates", go_to, desktop))

    if selected in {"all", "institutions"}:
        items = [
            _result_card(
                title=item.get("short_name") or item.get("title", "Учреждение"),
                subtitle=item.get("address") or item.get("full_name", ""),
                meta=item.get("institution_type", "учреждение"),
                icon=ft.Icons.ACCOUNT_BALANCE_OUTLINED,
                tone="blue",
                on_click=None,
                desktop=desktop,
            )
            for item in _institutions(query, institutions)
        ]
        controls.append(_section("Учреждения", ft.Icons.ACCOUNT_BALANCE_OUTLINED, items, None, go_to, desktop))

    return [control for control in controls if not isinstance(control, ft.Container)]


def _empty_search_state(query: str, on_query_change) -> ft.Control:
    title = "Ничего не найдено" if query else "Начните поиск"
    description = (
        "Попробуйте изменить запрос или выбрать другой тип результатов."
        if query
        else "Введите проблему, документ, сценарий или название учреждения."
    )
    action_text = "Искать «Рождение ребёнка»" if not query else "Сбросить поиск"
    action_value = "Рождение ребёнка" if not query else ""
    return empty_state_card(
        title,
        description,
        action_text=action_text,
        on_action=lambda _: on_query_change(action_value) if on_query_change else None,
        icon=ft.Icons.SEARCH_OFF_OUTLINED if query else ft.Icons.SEARCH,
    )


def _header(query: str, selected_filter: str, on_query_change, on_filter_change, desktop: bool) -> ft.Control:
    return ft.Column(
        spacing=12,
        controls=[
            ft.Text("Глобальный поиск", size=ts(36) if desktop else 22, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
            search_box(
                value=query,
                hint="Поиск по проблемам, сценариям, документам, законам...",
                on_change=lambda event: on_query_change(event.control.value) if on_query_change else None,
                on_submit=lambda event: on_query_change(event.control.value) if on_query_change else None,
            ),
            ft.Text(
                "Например: замена паспорта, ЖКХ, рождение ребёнка",
                size=ts(12),
                color=APP_COLORS["muted2"],
            ),
            _filter_chips(selected_filter, on_filter_change),
        ],
    )


def _desktop_search(
    query: str,
    selected_filter: str,
    on_query_change,
    on_filter_change,
    go_to,
    open_problem,
    open_scenario,
    open_law,
    situations: list[dict],
    documents: list[dict],
    laws: list[dict],
    institutions: list[dict],
) -> ft.Control:
    sections = _build_sections(
        query,
        selected_filter,
        go_to,
        open_problem,
        open_scenario,
        open_law,
        situations,
        documents,
        laws,
        institutions,
        True,
    )
    result_controls: list[ft.Control] = []
    if sections:
        result_controls.extend(sections)
    else:
        result_controls.append(_empty_search_state(query, on_query_change))

    results_switcher = ft.AnimatedSwitcher(
        content=ft.Column(spacing=24, controls=result_controls),
        duration=250,
        reverse_duration=220,
        switch_in_curve=ft.AnimationCurve.EASE_OUT,
        switch_out_curve=ft.AnimationCurve.EASE_OUT,
        transition=ft.AnimatedSwitcherTransition.FADE,
    )

    content_controls: list[ft.Control] = [
        _header(query, selected_filter, on_query_change, on_filter_change, True),
        ft.Row(
            spacing=18,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                app_card(
                    ft.Column(
                        spacing=22,
                        controls=[
                            _recent_searches(on_query_change),
                            _popular_requests(go_to, True),
                        ],
                    ),
                    padding=16,
                    width=760,
                ),
                ft.Container(width=320, content=_quick_filters(on_filter_change=on_filter_change, on_query_change=on_query_change)),
            ],
        ),
        ft.Text("Результаты поиска", size=ts(22), weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
        results_switcher,
    ]
    return desktop_content(
        ft.Column(spacing=24, controls=content_controls),
        width=1120,
        top=42,
    )


def _mobile_search(
    query: str,
    selected_filter: str,
    on_query_change,
    on_filter_change,
    go_to,
    open_problem,
    open_scenario,
    open_law,
    situations: list[dict],
    documents: list[dict],
    laws: list[dict],
    institutions: list[dict],
) -> ft.Control:
    sections = _build_sections(
        query,
        selected_filter,
        go_to,
        open_problem,
        open_scenario,
        open_law,
        situations,
        documents,
        laws,
        institutions,
        False,
    )
    result_controls: list[ft.Control] = []
    if sections:
        result_controls.extend(sections)
    else:
        result_controls.append(_empty_search_state(query, on_query_change))

    results_switcher = ft.AnimatedSwitcher(
        content=ft.Column(spacing=18, controls=result_controls),
        duration=250,
        reverse_duration=220,
        switch_in_curve=ft.AnimationCurve.EASE_OUT,
        switch_out_curve=ft.AnimationCurve.EASE_OUT,
        transition=ft.AnimatedSwitcherTransition.FADE,
    )

    controls: list[ft.Control] = [
        ft.Row(
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color=APP_COLORS["text"],
                    width=42,
                    height=42,
                    on_click=lambda _: go_to("/") if go_to else None,
                ),
                ft.Text("Глобальный поиск", size=ts(22), weight=ft.FontWeight.W_900, color=APP_COLORS["text"], expand=True),
            ],
        ),
        search_box(
            value=query,
            hint="Поиск по проблемам, сценариям, документам...",
            on_change=lambda event: on_query_change(event.control.value) if on_query_change else None,
            on_submit=lambda event: on_query_change(event.control.value) if on_query_change else None,
        ),
        ft.Text("Например: замена паспорта, ЖКХ, рождение ребёнка", size=ts(11), color=APP_COLORS["muted2"]),
        _filter_chips(selected_filter, on_filter_change),
        _recent_searches(on_query_change),
        _popular_requests(go_to, False),
        ft.Text("Результаты поиска", size=ts(18), weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
        results_switcher,
    ]
    return ft.Container(
        width=340,
        content=ft.Column(spacing=18, controls=controls),
    )


def build_search_page(
    *,
    is_desktop: bool = False,
    query: str = "",
    selected_filter: str = "all",
    on_query_change=None,
    on_filter_change=None,
    go_to=None,
    open_problem=None,
    open_scenario=None,
    open_law=None,
    situations: list[dict] | None = None,
    documents: list[dict] | None = None,
    laws: list[dict] | None = None,
    institutions: list[dict] | None = None,
) -> ft.Control:
    selected = selected_filter if selected_filter in {item[0] for item in FILTERS} else "all"
    common_args = (
        query,
        selected,
        on_query_change,
        on_filter_change,
        go_to,
        open_problem,
        open_scenario,
        open_law,
        situations or SITUATIONS,
        documents or DOCUMENTS,
        laws or LEGAL_UPDATES,
        institutions or INSTITUTIONS,
    )
    if is_desktop:
        return _desktop_search(*common_args)
    return _mobile_search(*common_args)
