from __future__ import annotations

from urllib.parse import urlparse

import flet as ft

from components.buttons import ghost_button, primary_button, secondary_button
from components.cards import app_card, badge, empty_state_card, icon_circle
from components.layout import desktop_content
from components.placeholders import photo_placeholder
from data.mock_data import CONTENT_DISCLAIMER, LEGAL_UPDATES, SCENARIO_TEMPLATES
from theme.app_theme import APP_COLORS, CENTER, RADIUS, SPACING, border_all, get_badge_palette, padding_symmetric, ts


CATEGORY_TONES = {
    "Семья": "green",
    "Документы": "blue",
    "Жильё и ЖКХ": "purple",
    "Бизнес/ИП": "cyan",
    "Авто": "cyan",
    "Работа": "purple",
    "Здоровье": "red",
}

CATEGORY_ICONS = {
    "Семья": ft.Icons.FAMILY_RESTROOM_OUTLINED,
    "Документы": ft.Icons.BADGE_OUTLINED,
    "Жильё и ЖКХ": ft.Icons.HOME_WORK_OUTLINED,
    "Бизнес/ИП": ft.Icons.BUSINESS_CENTER_OUTLINED,
    "Авто": ft.Icons.DIRECTIONS_CAR_OUTLINED,
    "Работа": ft.Icons.WORK_OUTLINE,
    "Здоровье": ft.Icons.HEALTH_AND_SAFETY_OUTLINED,
}


def find_scenario_template(template_id: str) -> dict:
    return next((item for item in SCENARIO_TEMPLATES if item["id"] == template_id), SCENARIO_TEMPLATES[0])


def _badge_colors(tone: str) -> tuple[str, str]:
    palette = get_badge_palette()
    return palette.get(tone, palette["blue"])


def _category_tone(category: str) -> str:
    return CATEGORY_TONES.get(category, "blue")


def _category_icon(category: str) -> str:
    return CATEGORY_ICONS.get(category, ft.Icons.ROUTE_OUTLINED)


def _difficulty_tone(difficulty: str) -> str:
    if difficulty == "Лёгкая":
        return "green"
    if difficulty == "Сложная":
        return "orange"
    return "blue"


def _scenario_counts(template: dict) -> tuple[int, int, int]:
    return len(template.get("stages", [])), len(template.get("tasks", [])), len(template.get("documents", []))


def _tasks_for_stage(template: dict, stage_id: str) -> list[dict]:
    tasks = [task for task in template.get("tasks", []) if task.get("stage_id") == stage_id]
    return sorted(tasks, key=lambda item: item.get("order_index", item.get("due_in_days", 999)))


def _stage_duration(tasks: list[dict]) -> str:
    days = [int(task.get("due_in_days", 0)) for task in tasks if str(task.get("due_in_days", "")).isdigit()]
    if not days:
        deadlines = [task.get("deadline") for task in tasks if task.get("deadline")]
        return deadlines[0] if deadlines else "по плану"
    if min(days) == max(days):
        return f"{max(days)} дн."
    return f"{min(days)}-{max(days)} дн."


def _source_host(url: str) -> str:
    parsed = urlparse(url or "")
    return parsed.netloc or (url or "сайт уточняется")


def _task_dependency_text(task: dict, tasks_by_id: dict[str, dict]) -> str:
    dependencies = [
        tasks_by_id[dependency_id]["title"]
        for dependency_id in task.get("depends_on", []) or []
        if dependency_id in tasks_by_id
    ]
    if not dependencies:
        return ""
    suffix = "..." if len(dependencies) > 2 else ""
    return "Зависит от: " + ", ".join(dependencies[:2]) + suffix


def _section_header(title: str, subtitle: str | None = None, icon: str | None = None) -> ft.Control:
    controls: list[ft.Control] = []
    if icon:
        controls.append(icon_circle(icon, color=APP_COLORS["blue_text"], bgcolor=APP_COLORS["active"], size=42))
    text_controls: list[ft.Control] = [
        ft.Text(title, size=ts(24), weight=ft.FontWeight.W_900, color=APP_COLORS["text"])
    ]
    if subtitle:
        text_controls.append(ft.Text(subtitle, size=ts(14), color=APP_COLORS["muted"]))
    controls.append(ft.Column(spacing=4, expand=True, controls=text_controls))
    return ft.Row(spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=controls)


def _small_meta(text: str, icon: str, tone: str = "blue") -> ft.Container:
    bg, fg = _badge_colors(tone)
    return ft.Container(
        padding=padding_symmetric(horizontal=10, vertical=7),
        border_radius=16,
        bgcolor=bg,
        content=ft.Row(
            spacing=6,
            tight=True,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(icon, size=ts(15), color=fg),
                ft.Text(text, size=ts(12), weight=ft.FontWeight.W_800, color=fg, max_lines=1, no_wrap=True),
            ],
        ),
    )


def _stat_tile(label: str, value: str | int, icon: str, tone: str = "blue") -> ft.Container:
    bg, fg = _badge_colors(tone)
    return app_card(
        ft.Column(
            spacing=5,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                icon_circle(icon, color=fg, bgcolor=bg, size=44),
                ft.Text(str(value), size=ts(28), weight=ft.FontWeight.W_900, color=fg, text_align=ft.TextAlign.CENTER),
                ft.Text(label, size=ts(12), weight=ft.FontWeight.W_800, color=APP_COLORS["muted"], text_align=ft.TextAlign.CENTER),
            ],
        ),
        padding=16,
    )


def _stats_row(template: dict, is_desktop: bool) -> ft.Control:
    stage_count, task_count, document_count = _scenario_counts(template)
    tiles = [
        ("этапов", stage_count, ft.Icons.VIEW_TIMELINE_OUTLINED, "purple"),
        ("задач", task_count, ft.Icons.CHECKLIST_RTL_OUTLINED, "blue"),
        ("документов", document_count, ft.Icons.ARTICLE_OUTLINED, "cyan"),
        ("сложность", template.get("difficulty", "средняя"), ft.Icons.SPEED_OUTLINED, _difficulty_tone(template.get("difficulty", ""))),
    ]
    return ft.ResponsiveRow(
        columns=12,
        spacing=12,
        run_spacing=12,
        controls=[
            ft.Container(
                col={"xs": 6, "md": 3 if is_desktop else 6},
                content=_stat_tile(label, value, icon, tone),
            )
            for label, value, icon, tone in tiles
        ],
    )


def _hero_section(template: dict, go_back, on_create_situation, is_desktop: bool) -> ft.Control:
    category = template.get("category", "Сценарий")
    badges = [
        badge(category, _category_tone(category)),
        badge(template.get("difficulty", "Средняя"), _difficulty_tone(template.get("difficulty", ""))),
        badge(template.get("estimated_duration", "срок уточняется"), "blue"),
    ]
    if is_desktop:
        actions: ft.Control = ft.Row(
            spacing=10,
            controls=[
                primary_button(
                    "Создать мою ситуацию",
                    icon=ft.Icons.ADD_TASK_OUTLINED,
                    on_click=lambda _: on_create_situation(template["id"]),
                    width=260,
                ),
                secondary_button("Сохранить", icon=ft.Icons.BOOKMARK_BORDER, width=170),
            ],
        )
    else:
        actions = ft.Column(
            spacing=10,
            controls=[
                primary_button(
                    "Создать мою ситуацию",
                    icon=ft.Icons.ADD_TASK_OUTLINED,
                    on_click=lambda _: on_create_situation(template["id"]),
                    expand=True,
                ),
                secondary_button("Сохранить", icon=ft.Icons.BOOKMARK_BORDER, expand=True),
            ],
        )
    text_controls: list[ft.Control] = [
        ft.Row(wrap=True, spacing=8, run_spacing=8, controls=badges),
        ft.Text(
            template["title"],
            size=ts(42) if is_desktop else 30,
            weight=ft.FontWeight.W_900,
            color=APP_COLORS["text"],
        ),
        ft.Text(
            template.get("short_description") or template.get("description", ""),
            size=ts(17) if is_desktop else 14,
            color=APP_COLORS["muted"],
        ),
        actions,
    ]
    if is_desktop:
        hero_content: ft.Control = ft.Row(
            spacing=24,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                ft.Column(spacing=14, expand=True, controls=text_controls),
                photo_placeholder(template["title"].lower(), width=310, height=190),
            ],
        )
    else:
        hero_content = ft.Column(
            spacing=14,
            controls=[
                photo_placeholder(template["title"].lower(), height=150),
                *text_controls,
            ],
        )
    return ft.Column(
        spacing=18,
        controls=[
            ft.Container(
                on_click=go_back,
                ink=True,
                content=ft.Row(
                    spacing=8,
                    tight=True,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(ft.Icons.ARROW_BACK, size=ts(18), color=APP_COLORS["blue_text"]),
                        ft.Text("Жизненные сценарии", size=ts(15), weight=ft.FontWeight.W_900, color=APP_COLORS["blue_text"]),
                    ],
                ),
            ),
            app_card(hero_content, padding=26 if is_desktop else 16, bgcolor=APP_COLORS["surface3"]),
        ],
    )


def _launch_hint(template: dict, on_create_situation, is_desktop: bool) -> ft.Container:
    bg, fg = _badge_colors("green")
    return ft.Container(
        padding=22 if is_desktop else 18,
        border_radius=RADIUS["hero"],
        bgcolor=bg,
        border=border_all(APP_COLORS["stroke2"]),
        content=ft.Row(
            spacing=16,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                icon_circle(ft.Icons.ROUTE_OUTLINED, color=fg, bgcolor=APP_COLORS["surface"], size=58),
                ft.Column(
                    spacing=10,
                    expand=True,
                    controls=[
                        ft.Text(
                            "Сценарий поможет не потеряться в документах и сроках",
                            size=ts(22) if is_desktop else 18,
                            weight=ft.FontWeight.W_900,
                            color=APP_COLORS["text"],
                        ),
                        ft.Text(
                            "Можно просмотреть план заранее или создать персональную ситуацию с датами и напоминаниями.",
                            size=ts(14),
                            color=APP_COLORS["muted"],
                        ),
                        primary_button(
                            "Создать мою ситуацию",
                            icon=ft.Icons.ADD_TASK_OUTLINED,
                            on_click=lambda _: on_create_situation(template["id"]),
                            expand=not is_desktop,
                            width=260 if is_desktop else None,
                        ),
                    ],
                ),
            ],
        ),
    )


def _task_documents(task: dict) -> ft.Control:
    documents = task.get("documents", [])
    if not documents:
        return ft.Container()
    return ft.Column(
        spacing=6,
        controls=[
            ft.Row(
                spacing=7,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    ft.Icon(
                        ft.Icons.CHECK_CIRCLE_OUTLINE if document.get("required") else ft.Icons.INFO_OUTLINE,
                        size=ts(15),
                        color=APP_COLORS["green"] if document.get("required") else APP_COLORS["muted2"],
                    ),
                    ft.Text(
                        f"{document['title']} · {'обязательно' if document.get('required') else 'при необходимости'}",
                        size=ts(12),
                        color=APP_COLORS["muted"],
                        expand=True,
                    ),
                ],
            )
            for document in documents[:3]
        ],
    )


def _step_card(task: dict, tasks_by_id: dict[str, dict]) -> ft.Container:
    dependency_text = _task_dependency_text(task, tasks_by_id)
    meta_controls = [
        _small_meta(task.get("deadline", "без срока"), ft.Icons.SCHEDULE_OUTLINED, "blue"),
    ]
    if task.get("institution_types"):
        meta_controls.append(_small_meta(", ".join(task.get("institution_types", [])[:2]), ft.Icons.LOCATION_ON_OUTLINED, "gray"))
    if dependency_text:
        meta_controls.append(_small_meta("есть зависимость", ft.Icons.LOCK_OUTLINE, "purple"))
    body_controls: list[ft.Control] = [
        ft.Row(
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                icon_circle(ft.Icons.TASK_ALT, color=APP_COLORS["blue_text"], bgcolor=APP_COLORS["active"], size=36),
                ft.Column(
                    spacing=7,
                    expand=True,
                    controls=[
                        ft.Text(task["title"], size=ts(15), weight=ft.FontWeight.W_800, color=APP_COLORS["text"]),
                        ft.Row(wrap=True, spacing=7, run_spacing=7, controls=meta_controls),
                    ],
                ),
            ],
        )
    ]
    if dependency_text:
        body_controls.append(ft.Text(dependency_text, size=ts(12), color=APP_COLORS["purple"], weight=ft.FontWeight.W_700))
    documents = _task_documents(task)
    if not isinstance(documents, ft.Container):
        body_controls.append(documents)
    return app_card(
        ft.Column(spacing=10, controls=body_controls),
        padding=13,
        bgcolor=APP_COLORS["surface2"],
        border_color=APP_COLORS["stroke2"],
    )


def _stage_card(template: dict, stage: dict, index: int, is_desktop: bool) -> ft.Container:
    tasks = _tasks_for_stage(template, stage["id"])
    tone = "green" if index == 1 else "blue"
    if index > 2:
        tone = "gray"
    bg, fg = _badge_colors(tone)
    body_controls: list[ft.Control] = [
        ft.Row(
            spacing=14,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                icon_circle(ft.Icons.CHECK if index == 1 else ft.Icons.FLAG_OUTLINED, color=fg, bgcolor=bg, size=52),
                ft.Column(
                    spacing=6,
                    expand=True,
                    controls=[
                        ft.Text(stage["title"], size=ts(20) if is_desktop else 18, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                        ft.Text(stage.get("description", "Короткое описание этапа и результата."), size=ts(13), color=APP_COLORS["muted"]),
                        ft.Row(
                            wrap=True,
                            spacing=8,
                            run_spacing=8,
                            controls=[
                                _small_meta(f"{len(tasks)} задач", ft.Icons.CHECKLIST_RTL_OUTLINED, "green" if index == 1 else "blue"),
                                _small_meta(_stage_duration(tasks), ft.Icons.SCHEDULE_OUTLINED, "blue" if index < 3 else "gray"),
                            ],
                        ),
                    ],
                ),
                ft.Icon(ft.Icons.CHEVRON_RIGHT, size=ts(22), color=APP_COLORS["muted2"]),
            ],
        )
    ]
    tasks_by_id = {task.get("id"): task for task in template.get("tasks", [])}
    body_controls.append(ft.Column(spacing=10, controls=[_step_card(task, tasks_by_id) for task in tasks]))
    return app_card(ft.Column(spacing=16, controls=body_controls), padding=18 if is_desktop else 14, animate=True)


def _timeline_section(template: dict, is_desktop: bool) -> ft.Control:
    stages = sorted(template.get("stages", []), key=lambda item: item.get("order_index", 0))
    if not stages:
        return empty_state_card(
            "Этапы пока не указаны",
            "Редактор контента добавит этапы и задачи на следующем шаге наполнения.",
            icon=ft.Icons.VIEW_TIMELINE_OUTLINED,
        )
    stage_count, task_count, _ = _scenario_counts(template)
    return ft.Column(
        spacing=16,
        controls=[
            _section_header("Этапы сценария", f"{stage_count} этапов · {task_count} задач", ft.Icons.VIEW_TIMELINE_OUTLINED),
            ft.Column(
                spacing=14,
                controls=[
                    _stage_card(template, stage, index, is_desktop)
                    for index, stage in enumerate(stages, start=1)
                ],
            ),
        ],
    )


def _dependencies_block(template: dict) -> ft.Control:
    tasks_by_id = {task.get("id"): task for task in template.get("tasks", [])}
    dependency_rows = [
        _task_dependency_text(task, tasks_by_id)
        for task in template.get("tasks", [])
        if task.get("depends_on")
    ]
    if not dependency_rows:
        dependency_rows = [
            "Зависимости уточняются редактором контента.",
            "После запуска ситуации приложение покажет доступные и заблокированные шаги.",
        ]
    return app_card(
        ft.Column(
            spacing=13,
            controls=[
                _section_header("Зависимости между задачами", "Что нужно выполнить раньше", ft.Icons.LOCK_OUTLINE),
                ft.Column(
                    spacing=10,
                    controls=[
                        ft.Row(
                            spacing=10,
                            vertical_alignment=ft.CrossAxisAlignment.START,
                            controls=[
                                icon_circle(ft.Icons.CHECK, color=APP_COLORS["purple"], bgcolor=get_badge_palette()["purple"][0], size=30),
                                ft.Text(row, size=ts(14), color=APP_COLORS["muted"], expand=True),
                            ],
                        )
                        for row in dependency_rows[:4]
                    ],
                ),
            ],
        ),
        padding=18,
    )


def _documents_section(template: dict, compact: bool = False) -> ft.Control:
    documents = template.get("documents", [])
    if not documents:
        return empty_state_card("Документы пока не указаны", "Перечень будет добавлен редактором.", icon=ft.Icons.ARTICLE_OUTLINED)
    cards = [
        ft.Container(
            col={"xs": 12, "sm": 6 if not compact else 12},
            content=app_card(
                ft.Row(
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    controls=[
                        icon_circle(ft.Icons.ARTICLE_OUTLINED, color=APP_COLORS["blue_text"], bgcolor=APP_COLORS["active"], size=42),
                        ft.Column(
                            spacing=6,
                            expand=True,
                            controls=[
                                badge("Обязательно" if document.get("required") else "При необходимости", "green" if document.get("required") else "gray"),
                                ft.Text(document["title"], size=ts(15), weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                                ft.Text(document.get("description", ""), size=ts(12), color=APP_COLORS["muted"]),
                            ],
                        ),
                    ],
                ),
                padding=14,
            ),
        )
        for document in documents
    ]
    return ft.Column(
        spacing=14,
        controls=[
            _section_header("Документы", "Общий список для прохождения сценария", ft.Icons.ARTICLE_OUTLINED),
            ft.ResponsiveRow(columns=12, spacing=12, run_spacing=12, controls=cards),
        ],
    )


def _authority_card(authority: dict) -> ft.Container:
    title = authority.get("title", "Организация")
    initial = title[:1].upper()
    return app_card(
        ft.Row(
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    width=48,
                    height=48,
                    border_radius=24,
                    bgcolor=get_badge_palette()["green"][0],
                    alignment=CENTER,
                    content=ft.Text(initial, size=ts(16), weight=ft.FontWeight.W_900, color=get_badge_palette()["green"][1]),
                ),
                ft.Column(
                    spacing=4,
                    expand=True,
                    controls=[
                        ft.Text(title, size=ts(16), weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                        ft.Text(authority.get("description", authority.get("type", "")), size=ts(12), weight=ft.FontWeight.W_700, color=APP_COLORS["muted"]),
                        ft.Row(
                            wrap=True,
                            spacing=6,
                            run_spacing=6,
                            controls=[
                                badge(authority.get("type", "организация"), "gray"),
                                badge(_source_host(authority.get("website", "")), "blue") if authority.get("website") else badge("сайт уточняется", "gray"),
                            ],
                        ),
                    ],
                ),
                ft.Icon(ft.Icons.CHEVRON_RIGHT, size=ts(20), color=APP_COLORS["muted2"]),
            ],
        ),
        padding=14,
        bgcolor=APP_COLORS["surface2"],
    )


def _authorities_section(template: dict, user: dict | None = None) -> ft.Control:
    authorities = template.get("authorities", [])
    city = (user or {}).get("city", "")
    district = (user or {}).get("district", "")
    hint = "Адрес ближайшего учреждения лучше уточнить перед визитом."
    if city or district:
        hint = f"Подбор можно уточнить по профилю: {', '.join(part for part in [district, city] if part)}."
    if not authorities:
        return empty_state_card("Учреждения уточняются", hint, icon=ft.Icons.LOCATION_ON_OUTLINED)
    return ft.Column(
        spacing=14,
        controls=[
            _section_header("Куда обращаться", hint, ft.Icons.LOCATION_ON_OUTLINED),
            ft.Column(spacing=10, controls=[_authority_card(authority) for authority in authorities]),
        ],
    )


def _source_cards(template: dict, open_source) -> ft.Control:
    sources = template.get("sources", [])
    if not sources:
        return empty_state_card("Источники пока не указаны", CONTENT_DISCLAIMER, icon=ft.Icons.LINK_OUTLINED)
    return ft.Column(
        spacing=12,
        controls=[
            _section_header("Официальные источники", "Информация используется справочно и сверяется с официальными ресурсами.", ft.Icons.LINK_OUTLINED),
            app_card(
                ft.Text(CONTENT_DISCLAIMER, size=ts(14), color=APP_COLORS["muted"]),
                padding=16,
                bgcolor=APP_COLORS["surface3"],
            ),
            ft.Column(
                spacing=10,
                controls=[
                    ft.Container(
                        on_click=(lambda _, url=source.get("url", ""): open_source(url)) if open_source else None,
                        ink=True,
                        content=app_card(
                            ft.Row(
                                spacing=12,
                                vertical_alignment=ft.CrossAxisAlignment.START,
                                controls=[
                                    icon_circle(ft.Icons.LINK, color=APP_COLORS["blue_text"], bgcolor=APP_COLORS["active"], size=42),
                                    ft.Column(
                                        spacing=6,
                                        expand=True,
                                        controls=[
                                            ft.Text(source.get("title", "Официальный источник"), size=ts(15), weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                                            ft.Text(source.get("description", "Официальный источник для финальной проверки данных."), size=ts(12), color=APP_COLORS["muted"]),
                                            ft.Row(
                                                wrap=True,
                                                spacing=7,
                                                run_spacing=7,
                                                controls=[
                                                    badge(_source_host(source.get("url", "")), "blue"),
                                                    badge(f"Проверка: {source.get('last_checked') or 'требует проверки'}", "orange" if not source.get("last_checked") or source.get("last_checked") == "требует проверки" else "gray"),
                                                ],
                                            ),
                                        ],
                                    ),
                                    ft.Icon(ft.Icons.OPEN_IN_NEW, size=ts(18), color=APP_COLORS["muted2"]),
                                ],
                            ),
                            padding=14,
                        ),
                    )
                    for source in sources
                ],
            ),
        ],
    )


def _related_section(template: dict) -> ft.Control:
    related = template.get("related_scenarios", [])
    if not related:
        return empty_state_card("Связанные сценарии пока не указаны", "Они появятся после расширения базы сценариев.", icon=ft.Icons.ACCOUNT_TREE_OUTLINED)
    return ft.Column(
        spacing=14,
        controls=[
            _section_header("Связанные сценарии", "Что может понадобиться дальше", ft.Icons.ACCOUNT_TREE_OUTLINED),
            ft.Column(
                spacing=10,
                controls=[
                    app_card(
                        ft.Row(
                            spacing=12,
                            vertical_alignment=ft.CrossAxisAlignment.START,
                            controls=[
                                icon_circle(ft.Icons.ROUTE_OUTLINED, color=APP_COLORS["blue_text"], bgcolor=APP_COLORS["active"], size=42),
                                ft.Column(
                                    spacing=5,
                                    expand=True,
                                    controls=[
                                        ft.Text(item.get("title", "Связанный сценарий"), size=ts(16), weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                                        ft.Text(item.get("description", "Может понадобиться после завершения основного сценария."), size=ts(12), color=APP_COLORS["muted"]),
                                        badge(item.get("relation_type", "связано"), "gray"),
                                    ],
                                ),
                                ft.Icon(ft.Icons.CHEVRON_RIGHT, size=ts(20), color=APP_COLORS["muted2"]),
                            ],
                        ),
                        padding=14,
                    )
                    for item in related
                ],
            ),
        ],
    )


def _affecting_law_updates(template: dict, law_updates: list[dict]) -> list[dict]:
    title = (template.get("title") or "").lower()
    return [
        law for law in law_updates
        if law.get("status") == "published"
        and any(title in (scenario or "").lower() or (scenario or "").lower() in title for scenario in law.get("related_scenarios") or [])
    ]


def _law_updates_block(template: dict, law_updates: list[dict], open_law=None) -> ft.Control:
    affecting = _affecting_law_updates(template, law_updates)
    if not affecting:
        return ft.Container()
    return ft.Column(
        spacing=14,
        controls=[
            _section_header("Связанные изменения законодательства", "Может повлиять на порядок действий", ft.Icons.BALANCE_OUTLINED),
            ft.Column(
                spacing=10,
                controls=[
                    ft.Container(
                        on_click=(lambda _, law_id=law["id"]: open_law(law_id)) if open_law else None,
                        ink=True,
                        content=app_card(
                            ft.Column(
                                spacing=8,
                                controls=[
                                    ft.Row(wrap=True, spacing=7, run_spacing=7, controls=[badge(law.get("category_name", ""), "blue"), badge(law.get("date", ""), "gray")]),
                                    ft.Text(law.get("title", ""), size=ts(16), weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                                    ft.Text(law.get("short", ""), size=ts(13), color=APP_COLORS["muted"]),
                                ],
                            ),
                            padding=14,
                            border_color=APP_COLORS["orange"],
                        ),
                    )
                    for law in affecting
                ],
            ),
        ],
    )


def _summary_card(template: dict, on_create_situation) -> ft.Container:
    stage_count, task_count, document_count = _scenario_counts(template)
    rows = [
        ("Сложность", template.get("difficulty", "Средняя"), _difficulty_tone(template.get("difficulty", ""))),
        ("Срок", template.get("estimated_duration", "уточняется"), "blue"),
        ("Этапов", f"{stage_count} этапов", "purple"),
        ("Задач", f"{task_count} шагов", "orange"),
        ("Документов", f"{document_count} документов", "cyan"),
    ]
    return app_card(
        ft.Column(
            spacing=14,
            controls=[
                ft.Text("Сводка сценария", size=ts(22), weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                ft.Column(
                    spacing=12,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text(label, size=ts(14), weight=ft.FontWeight.W_800, color=APP_COLORS["muted"]),
                                badge(value, tone),
                            ],
                        )
                        for label, value, tone in rows
                    ],
                ),
                ft.Divider(height=1, color=APP_COLORS["stroke2"]),
                ft.Text("После запуска сценарий станет вашей ситуацией: появятся чек-листы, сроки, документы и напоминания.", size=ts(14), color=APP_COLORS["muted"]),
                primary_button("Создать мою ситуацию", icon=ft.Icons.ADD_TASK_OUTLINED, on_click=lambda _: on_create_situation(template["id"]), expand=True),
            ],
        ),
        padding=22,
    )


def _compact_list_card(title: str, icon: str, rows: list[tuple[str, str]], tone: str = "blue") -> ft.Container:
    bg, fg = _badge_colors(tone)
    return app_card(
        ft.Column(
            spacing=12,
            controls=[
                ft.Row(
                    spacing=10,
                    controls=[
                        icon_circle(icon, color=fg, bgcolor=bg, size=42),
                        ft.Text(title, size=ts(20), weight=ft.FontWeight.W_900, color=APP_COLORS["text"], expand=True),
                    ],
                ),
                ft.Column(
                    spacing=9,
                    controls=[
                        ft.Row(
                            spacing=9,
                            vertical_alignment=ft.CrossAxisAlignment.START,
                            controls=[
                                ft.Container(width=22, height=22, border_radius=11, bgcolor=bg, alignment=CENTER, content=ft.Icon(ft.Icons.CHECK, size=ts(13), color=fg)),
                                ft.Column(
                                    spacing=2,
                                    expand=True,
                                    controls=[
                                        ft.Text(primary, size=ts(14), weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                                        ft.Text(secondary, size=ts(12), color=APP_COLORS["muted"]),
                                    ],
                                ),
                            ],
                        )
                        for primary, secondary in rows[:4]
                    ],
                ),
            ],
        ),
        padding=18,
    )


def _right_column(template: dict, on_create_situation, user: dict | None) -> ft.Control:
    documents = [(doc["title"], "обязательно" if doc.get("required") else "при необходимости") for doc in template.get("documents", [])]
    authorities = [(item.get("title", "Организация"), item.get("description", item.get("type", ""))) for item in template.get("authorities", [])]
    related = [(item.get("title", "Связанный сценарий"), item.get("description", "")) for item in template.get("related_scenarios", [])]
    controls: list[ft.Control] = [
        _summary_card(template, on_create_situation),
        _compact_list_card("Документы", ft.Icons.ARTICLE_OUTLINED, documents, "blue") if documents else ft.Container(),
        _compact_list_card("Куда обращаться", ft.Icons.LOCATION_ON_OUTLINED, authorities, "green") if authorities else ft.Container(),
        _compact_list_card("Связанные сценарии", ft.Icons.ACCOUNT_TREE_OUTLINED, related, "purple") if related else ft.Container(),
    ]
    if user and (user.get("city") or user.get("district")):
        controls.insert(
            1,
            app_card(
                ft.Row(
                    spacing=10,
                    controls=[
                        ft.Icon(ft.Icons.MY_LOCATION_OUTLINED, size=ts(20), color=APP_COLORS["blue_text"]),
                        ft.Text(f"Профиль: {', '.join(part for part in [user.get('district'), user.get('city')] if part)}", size=ts(13), color=APP_COLORS["muted"], expand=True),
                    ],
                ),
                padding=14,
                bgcolor=APP_COLORS["surface3"],
            ),
        )
    return ft.Container(width=330, content=ft.Column(spacing=16, controls=controls))


def _desktop_content(template: dict, go_back, on_create_situation, open_source, user: dict | None, law_updates: list[dict] | None, open_law) -> ft.Control:
    main_controls: list[ft.Control] = [
        _hero_section(template, go_back, on_create_situation, True),
        _launch_hint(template, on_create_situation, True),
        _stats_row(template, True),
        _timeline_section(template, True),
        _dependencies_block(template),
        _documents_section(template),
        _authorities_section(template, user),
    ]
    law_block = _law_updates_block(template, law_updates or LEGAL_UPDATES, open_law)
    if not isinstance(law_block, ft.Container) or law_block.content is not None:
        main_controls.append(law_block)
    main_controls.extend(
        [
            _related_section(template),
            _source_cards(template, open_source),
            app_card(
                ft.Row(
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text("Готовы запустить личный план?", size=ts(20), weight=ft.FontWeight.W_900, color=APP_COLORS["text"], expand=True),
                        primary_button("Создать мою ситуацию", icon=ft.Icons.ADD_TASK_OUTLINED, width=260, on_click=lambda _: on_create_situation(template["id"])),
                    ],
                ),
                padding=18,
                bgcolor=APP_COLORS["surface3"],
            ),
        ]
    )
    return desktop_content(
        ft.Row(
            spacing=26,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                ft.Container(width=760, content=ft.Column(spacing=26, controls=main_controls)),
                _right_column(template, on_create_situation, user),
            ],
        ),
        width=1120,
        top=44,
        bottom=120,
    )


def _mobile_content(template: dict, go_back, on_create_situation, open_source, user: dict | None, law_updates: list[dict] | None, open_law) -> ft.Control:
    stage_count, task_count, document_count = _scenario_counts(template)
    law_block = _law_updates_block(template, law_updates or LEGAL_UPDATES, open_law)
    controls: list[ft.Control] = [
        ft.Row(
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.IconButton(icon=ft.Icons.ARROW_BACK_IOS_NEW, icon_color=APP_COLORS["muted"], on_click=go_back),
                ft.Text("Детали сценария", size=ts(22), weight=ft.FontWeight.W_900, color=APP_COLORS["text"], expand=True),
                icon_circle(_category_icon(template.get("category", "")), color=APP_COLORS["blue_text"], bgcolor=APP_COLORS["active"], size=44),
            ],
        ),
        _hero_section(template, go_back, on_create_situation, False),
        _launch_hint(template, on_create_situation, False),
        ft.ResponsiveRow(
            columns=12,
            spacing=10,
            run_spacing=10,
            controls=[
                ft.Container(col={"xs": 4}, content=_stat_tile("этапа", stage_count, ft.Icons.VIEW_TIMELINE_OUTLINED, "purple")),
                ft.Container(col={"xs": 4}, content=_stat_tile("задач", task_count, ft.Icons.CHECKLIST_RTL_OUTLINED, "blue")),
                ft.Container(col={"xs": 4}, content=_stat_tile("док-та", document_count, ft.Icons.ARTICLE_OUTLINED, "cyan")),
            ],
        ),
        _timeline_section(template, False),
        _dependencies_block(template),
        _documents_section(template, compact=True),
        _authorities_section(template, user),
    ]
    if not isinstance(law_block, ft.Container) or law_block.content is not None:
        controls.append(law_block)
    controls.extend(
        [
            _related_section(template),
            _source_cards(template, open_source),
            primary_button("Создать мою ситуацию", icon=ft.Icons.ADD_TASK_OUTLINED, expand=True, on_click=lambda _: on_create_situation(template["id"])),
            ghost_button("Назад к сценариям", icon=ft.Icons.ARROW_BACK, expand=True, on_click=go_back),
        ]
    )
    return ft.Container(width=340, content=ft.Column(spacing=18, controls=controls))


def build_scenario_detail_page(
    template_id: str,
    go_back,
    on_create_situation,
    open_source,
    is_desktop: bool = False,
    user: dict | None = None,
    law_updates: list[dict] | None = None,
    open_law=None,
) -> ft.Control:
    template = find_scenario_template(template_id)
    if is_desktop:
        return _desktop_content(template, go_back, on_create_situation, open_source, user, law_updates, open_law)
    return _mobile_content(template, go_back, on_create_situation, open_source, user, law_updates, open_law)
