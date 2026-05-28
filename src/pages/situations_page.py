from __future__ import annotations

from datetime import date, datetime

import flet as ft

from components.buttons import ghost_button, primary_button, secondary_button
from components.cards import app_card, badge, category_chip, empty_state_card, icon_circle, page_heading, stat_card
from components.layout import desktop_content
from theme.app_theme import APP_COLORS, RADIUS, SPACING, border_all, get_badge_palette, padding_symmetric


FILTERS = ["Все", "Активные", "Завершённые", "Просрочено"]
COMPLETED_STATUSES = {"Завершено", "Завершена"}


def _as_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except ValueError:
        return None


def _format_due(value: str | None) -> str:
    due_date = _as_date(value)
    if due_date is None:
        return "без срока"
    today = date.today()
    delta = (due_date - today).days
    if delta == 0:
        return "сегодня"
    if delta == 1:
        return "завтра"
    if delta > 1:
        return f"через {delta} дн."
    if delta == -1:
        return "вчера"
    return f"просрочено {abs(delta)} дн."


def _is_task_overdue(task: dict) -> bool:
    due_date = _as_date(task.get("due_date"))
    return bool(due_date and due_date < date.today() and not task.get("completed"))


def _is_completed(item: dict) -> bool:
    return int(item.get("progress", 0)) >= 100 or item.get("status") in COMPLETED_STATUSES


def _tasks_for_situation(item: dict, tasks: list[dict]) -> list[dict]:
    situation_id = item.get("id")
    return [task for task in tasks if task.get("situation_id") == situation_id]


def _task_counts(item: dict, tasks: list[dict]) -> tuple[int, int]:
    situation_tasks = _tasks_for_situation(item, tasks)
    completed = len([task for task in situation_tasks if task.get("completed")])
    return completed, len(situation_tasks)


def _computed_progress(item: dict, tasks: list[dict]) -> int:
    completed, total = _task_counts(item, tasks)
    if total:
        return round(completed / total * 100)
    return int(item.get("progress", 0))


def _has_overdue(item: dict, tasks: list[dict]) -> bool:
    return any(_is_task_overdue(task) for task in _tasks_for_situation(item, tasks))


def _nearest_task(item: dict, tasks: list[dict]) -> dict | None:
    dated_tasks: list[tuple[date, dict]] = []
    for task in _tasks_for_situation(item, tasks):
        due_date = _as_date(task.get("due_date"))
        if due_date and not task.get("completed"):
            dated_tasks.append((due_date, task))
    if not dated_tasks:
        return None
    dated_tasks.sort(key=lambda pair: pair[0])
    return dated_tasks[0][1]


def _current_stage(item: dict, tasks: list[dict]) -> str:
    for task in _tasks_for_situation(item, tasks):
        if not task.get("completed"):
            return task.get("stage_title") or task.get("stage") or "Текущий этап"
    return "Все этапы пройдены" if _is_completed(item) else "Этапы не заданы"


def _status_label(item: dict, tasks: list[dict]) -> str:
    progress = _computed_progress(item, tasks)
    if progress >= 100:
        return "Завершена"
    if _has_overdue(item, tasks):
        return "Просрочено"
    if progress > 0:
        return "В процессе"
    status = item.get("status") or "Не начата"
    return "Завершена" if status in COMPLETED_STATUSES else status


def _status_variant(label: str) -> str:
    if label == "Просрочено":
        return "red"
    if label == "В процессе":
        return "blue"
    if label in {"Завершено", "Завершена"}:
        return "green"
    return "gray"


def _progress_tone(progress: int, overdue: bool) -> str:
    if overdue:
        return "red"
    if progress >= 100:
        return "green"
    if progress > 0:
        return "blue"
    return "orange"


def _category_icon(item: dict):
    category = (item.get("category") or item.get("title") or "").lower()
    if "сем" in category or "реб" in category:
        return ft.Icons.FAMILY_RESTROOM_OUTLINED
    if "ип" in category or "бизнес" in category:
        return ft.Icons.BUSINESS_CENTER_OUTLINED
    if "переезд" in category or "жиль" in category:
        return ft.Icons.HOME_WORK_OUTLINED
    if "паспорт" in category or "документ" in category:
        return ft.Icons.DESCRIPTION_OUTLINED
    return ft.Icons.TASK_ALT_OUTLINED


def _category_tone(item: dict) -> str:
    category = (item.get("category") or item.get("title") or "").lower()
    if "сем" in category or "реб" in category:
        return "green"
    if "ип" in category or "бизнес" in category:
        return "purple"
    if "переезд" in category or "жиль" in category:
        return "cyan"
    if "паспорт" in category or "документ" in category:
        return "blue"
    return "gray"


def _filtered_situations(situations: list[dict], tasks: list[dict], selected_filter: str) -> list[dict]:
    selected = selected_filter if selected_filter in FILTERS else "Все"
    if selected == "Активные":
        return [item for item in situations if not _is_completed(item) and not _has_overdue(item, tasks)]
    if selected == "Завершённые":
        return [item for item in situations if _is_completed(item)]
    if selected == "Просрочено":
        return [item for item in situations if _has_overdue(item, tasks)]
    return situations


def _stats(situations: list[dict], tasks: list[dict]) -> dict[str, int]:
    active = len([item for item in situations if not _is_completed(item)])
    completed = len([item for item in situations if _is_completed(item)])
    overdue = len([item for item in situations if _has_overdue(item, tasks)])
    active_items = [item for item in situations if not _is_completed(item)]
    if active_items:
        progress = round(sum(_computed_progress(item, tasks) for item in active_items) / len(active_items))
    else:
        progress = 0
    return {
        "total": len(situations),
        "active": active,
        "completed": completed,
        "overdue": overdue,
        "progress": progress,
    }


def _upcoming_tasks(tasks: list[dict], situations: list[dict], limit: int = 4) -> list[dict]:
    situation_titles = {item.get("id"): item.get("title", "Ситуация") for item in situations}
    dated: list[tuple[date, dict]] = []
    for task in tasks:
        due_date = _as_date(task.get("due_date"))
        if due_date and not task.get("completed"):
            item = dict(task)
            item["situation_title"] = situation_titles.get(task.get("situation_id"), "Ситуация")
            dated.append((due_date, item))
    dated.sort(key=lambda pair: pair[0])
    return [item for _, item in dated[:limit]]


def _documents_to_prepare(tasks: list[dict], situations: list[dict], limit: int = 4) -> list[dict]:
    situation_titles = {item.get("id"): item.get("title", "Ситуация") for item in situations}
    seen: set[str] = set()
    result: list[dict] = []
    for task in tasks:
        if task.get("completed"):
            continue
        for document in task.get("documents") or []:
            title = document.get("title") if isinstance(document, dict) else str(document)
            if not title or title in seen:
                continue
            seen.add(title)
            result.append(
                {
                    "title": title,
                    "required": bool(document.get("required")) if isinstance(document, dict) else True,
                    "situation": situation_titles.get(task.get("situation_id"), "Ситуация"),
                }
            )
            if len(result) >= limit:
                return result
    return result


def _filter_chips(selected_filter: str, on_filter_change=None, compact: bool = False) -> ft.Row:
    selected = selected_filter if selected_filter in FILTERS else "Все"
    labels = FILTERS
    if compact:
        labels = ["Все", "Активные", "Просрочено", "Завершённые"]
    return ft.Row(
        wrap=True,
        spacing=8,
        run_spacing=8,
        controls=[
            category_chip(
                label,
                selected=label == selected,
                on_click=lambda _, value=label: on_filter_change(value) if on_filter_change else None,
            )
            for label in labels
        ],
    )


def _icon_badge(tone: str, icon) -> ft.Container:
    badge_bg, badge_fg = get_badge_palette().get(tone, get_badge_palette()["gray"])
    return icon_circle(icon, color=badge_fg, bgcolor=badge_bg, size=48)


def _progress_bar(progress: int, tone: str) -> ft.ProgressBar:
    _, progress_color = get_badge_palette().get(tone, get_badge_palette()["blue"])
    return ft.ProgressBar(
        value=max(0, min(progress, 100)) / 100,
        bar_height=7,
        border_radius=10,
        color=progress_color,
        bgcolor=APP_COLORS["surface2"],
    )


def _empty_state(on_open_templates=None) -> ft.Container:
    return empty_state_card(
        "У вас пока нет активных ситуаций",
        "Выберите жизненный сценарий, чтобы приложение создало личный план, задачи и документы.",
        "Выбрать сценарий",
        on_open_templates,
        ft.Icons.ROUTE_OUTLINED,
    )


def _situation_card(
    item: dict,
    open_situation,
    desktop: bool,
    on_edit_situation=None,
    on_delete_situation=None,
    tasks: list[dict] | None = None,
) -> ft.Container:
    task_dataset = tasks or []
    completed_tasks, total_tasks = _task_counts(item, task_dataset)
    progress = _computed_progress(item, task_dataset)
    overdue = _has_overdue(item, task_dataset)
    status_text = _status_label(item, task_dataset)
    status_variant = _status_variant(status_text)
    tone = _progress_tone(progress, overdue)
    category_tone = _category_tone(item)
    nearest = _nearest_task(item, task_dataset)
    deadline_text = _format_due(nearest.get("due_date")) if nearest else "срок не задан"
    stage_text = _current_stage(item, task_dataset)
    description = item.get("short_description") or item.get("description") or item.get("estimated_duration") or "Личный сценарий с задачами и документами."
    title_size = 20 if desktop else 18

    action_buttons: list[ft.Control] = []
    if on_edit_situation:
        action_buttons.append(
            ft.IconButton(
                icon=ft.Icons.EDIT_OUTLINED,
                icon_size=19,
                icon_color=APP_COLORS["muted2"],
                tooltip="Редактировать",
                on_click=lambda _, situation_id=item.get("id"): on_edit_situation(situation_id),
            )
        )
    if on_delete_situation:
        action_buttons.append(
            ft.IconButton(
                icon=ft.Icons.DELETE_OUTLINE,
                icon_size=19,
                icon_color=APP_COLORS["red"],
                tooltip="Удалить",
                on_click=lambda _, situation_id=item.get("id"): on_delete_situation(situation_id),
            )
        )

    right_controls: list[ft.Control] = [badge(status_text, status_variant)]
    right_controls.extend(action_buttons)
    right_controls.append(ft.Icon(ft.Icons.ARROW_FORWARD_IOS, size=18, color=APP_COLORS["muted2"]))

    meta_controls: list[ft.Control] = [
        ft.Row(
            spacing=5,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(ft.Icons.LIST_ALT_OUTLINED, size=15, color=APP_COLORS["muted2"]),
                ft.Text(
                    f"{completed_tasks}/{total_tasks} задач" if total_tasks else "задачи не добавлены",
                    size=12,
                    weight=ft.FontWeight.W_700,
                    color=APP_COLORS["muted"],
                ),
            ],
        ),
        ft.Row(
            spacing=5,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(ft.Icons.EVENT_OUTLINED, size=15, color=APP_COLORS["muted2"]),
                ft.Text(deadline_text, size=12, weight=ft.FontWeight.W_700, color=APP_COLORS["muted"]),
            ],
        ),
    ]

    card_body = ft.Column(
        spacing=12,
        controls=[
            ft.Row(
                spacing=14,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    _icon_badge(category_tone, _category_icon(item)),
                    ft.Column(
                        spacing=7,
                        expand=True,
                        controls=[
                            ft.Row(
                                spacing=8,
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                vertical_alignment=ft.CrossAxisAlignment.START,
                                controls=[
                                    ft.Text(item.get("title", "Ситуация"), size=title_size, weight=ft.FontWeight.W_900, color=APP_COLORS["text"], expand=True),
                                    ft.Row(spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=right_controls),
                                ],
                            ),
                            ft.Text(description, size=13, color=APP_COLORS["muted"], max_lines=2),
                        ],
                    ),
                ],
            ),
            ft.Row(
                spacing=8,
                wrap=True,
                controls=[
                    badge(stage_text, "gray"),
                    *meta_controls,
                ],
            ),
            ft.Column(
                spacing=6,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text("Прогресс", size=12, weight=ft.FontWeight.W_800, color=APP_COLORS["muted"]),
                            ft.Text(f"{progress}%", size=13, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                        ],
                    ),
                    _progress_bar(progress, tone),
                ],
            ),
        ],
    )

    card = app_card(card_body, padding=18 if desktop else 16, animate=True)
    if overdue:
        card.border = border_all(APP_COLORS["red"], width=1)

    return ft.Container(
        content=card,
        on_click=lambda _: open_situation(item.get("id")),
        ink=True,
    )


def _stat_grid(situations: list[dict], tasks: list[dict], desktop: bool) -> ft.ResponsiveRow:
    stats = _stats(situations, tasks)
    controls = [
        ft.Container(
            col={"xs": 6, "sm": 3} if desktop else {"xs": 4},
            content=stat_card("всего", stats["total"], "ситуаций", ft.Icons.ROUTE_OUTLINED, "blue"),
        ),
        ft.Container(
            col={"xs": 6, "sm": 3} if desktop else {"xs": 4},
            content=stat_card("активные", stats["active"], "в работе", ft.Icons.TASK_ALT_OUTLINED, "green"),
        ),
        ft.Container(
            col={"xs": 6, "sm": 3} if desktop else {"xs": 4},
            content=stat_card("прогресс", f"{stats['progress']}%", "средний", ft.Icons.INSIGHTS_OUTLINED, "purple"),
        ),
        ft.Container(
            col={"xs": 6, "sm": 3} if desktop else {"xs": 4},
            content=stat_card("просрочено", stats["overdue"], "требуют внимания", ft.Icons.ERROR_OUTLINE, "red" if stats["overdue"] else "gray"),
        ),
    ]
    if not desktop:
        controls = controls[1:]
    return ft.ResponsiveRow(columns=12, spacing=12, run_spacing=12, controls=controls)


def _side_task_card(task: dict) -> ft.Container:
    overdue = _is_task_overdue(task)
    tone = "red" if overdue else "blue"
    due_text = _format_due(task.get("due_date"))
    return app_card(
        ft.Row(
            spacing=11,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                _icon_badge(tone, ft.Icons.ERROR_OUTLINE if overdue else ft.Icons.SCHEDULE_OUTLINED),
                ft.Column(
                    spacing=4,
                    expand=True,
                    controls=[
                        ft.Text(task.get("title", "Задача"), size=14, weight=ft.FontWeight.W_800, color=APP_COLORS["text"], max_lines=2),
                        ft.Text(task.get("situation_title", "Ситуация"), size=12, color=APP_COLORS["muted"], max_lines=1),
                    ],
                ),
                badge(due_text, "red" if overdue else "blue"),
            ],
        ),
        padding=12,
        bgcolor=APP_COLORS["surface2"],
    )


def _documents_panel(tasks: list[dict], situations: list[dict]) -> ft.Container:
    documents = _documents_to_prepare(tasks, situations)
    if not documents:
        return app_card(
            ft.Column(
                spacing=8,
                controls=[
                    ft.Text("Документы к подготовке", size=20, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                    ft.Text("Пока нет документов из активных задач.", size=13, color=APP_COLORS["muted"]),
                ],
            ),
            padding=18,
        )

    rows: list[ft.Control] = []
    for document in documents:
        rows.append(
            ft.Row(
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    _icon_badge("cyan", ft.Icons.DOCUMENT_SCANNER_OUTLINED),
                    ft.Column(
                        spacing=3,
                        expand=True,
                        controls=[
                            ft.Row(
                                spacing=6,
                                wrap=True,
                                controls=[
                                    ft.Text(document["title"], size=14, weight=ft.FontWeight.W_800, color=APP_COLORS["text"]),
                                    badge("обязательно" if document["required"] else "по ситуации", "green" if document["required"] else "orange"),
                                ],
                            ),
                            ft.Text(document["situation"], size=12, color=APP_COLORS["muted"], max_lines=1),
                        ],
                    ),
                ],
            )
        )

    return app_card(
        ft.Column(
            spacing=14,
            controls=[
                ft.Text("Документы к подготовке", size=20, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                *rows,
            ],
        ),
        padding=18,
    )


def _desktop_sidebar(situations: list[dict], tasks: list[dict]) -> ft.Column:
    upcoming = _upcoming_tasks(tasks, situations)
    task_controls: list[ft.Control] = [
        ft.Text("Ближайшие задачи", size=22, weight=ft.FontWeight.W_900, color=APP_COLORS["text"])
    ]
    if upcoming:
        task_controls.extend([_side_task_card(task) for task in upcoming])
    else:
        task_controls.append(ft.Text("Ближайших задач нет.", size=13, color=APP_COLORS["muted"]))

    return ft.Column(
        spacing=18,
        controls=[
            app_card(ft.Column(spacing=12, controls=task_controls), padding=18),
            _documents_panel(tasks, situations),
            app_card(
                ft.Column(
                    spacing=8,
                    controls=[
                        ft.Row(
                            spacing=8,
                            controls=[
                                ft.Icon(ft.Icons.LIGHTBULB_OUTLINE, size=20, color=APP_COLORS["blue"]),
                                ft.Text("Подсказка", size=17, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                            ],
                        ),
                        ft.Text(
                            "Ситуации работают как личные проекты: следите за задачами, документами и сроками.",
                            size=13,
                            color=APP_COLORS["muted"],
                        ),
                    ],
                ),
                padding=18,
                bgcolor=APP_COLORS["surface3"],
            ),
        ],
    )


def _desktop_situations(
    open_situation,
    situations: list[dict],
    tasks: list[dict] | None = None,
    on_add_situation=None,
    on_edit_situation=None,
    on_delete_situation=None,
    on_open_templates=None,
    selected_filter: str = "Все",
    on_filter_change=None,
) -> ft.Control:
    task_dataset = tasks or []
    filtered = _filtered_situations(situations, task_dataset, selected_filter)
    situation_cards = [
        _situation_card(item, open_situation, True, on_edit_situation, on_delete_situation, task_dataset)
        for item in filtered
    ]
    if not situation_cards:
        situation_cards = [_empty_state(on_open_templates)]

    return desktop_content(
        ft.Column(
            spacing=24,
            controls=[
                page_heading(
                    "Мои ситуации",
                    "Ваши активные жизненные сценарии, задачи, сроки и документы в одном месте.",
                    actions=[
                        ghost_button("Выбрать сценарий", icon=ft.Icons.ROUTE_OUTLINED, width=190, on_click=on_open_templates),
                        primary_button("Создать ситуацию", icon=ft.Icons.ADD, width=205, on_click=on_add_situation),
                    ],
                ),
                ft.Container(
                    content=ft.Row(
                        spacing=12,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(ft.Icons.SEARCH, size=22, color=APP_COLORS["blue"]),
                            ft.Text("Поиск по ситуациям, задачам и документам...", size=15, color=APP_COLORS["muted"]),
                        ],
                    ),
                    height=58,
                    padding=padding_symmetric(horizontal=18, vertical=0),
                    border_radius=18,
                    border=border_all(APP_COLORS["stroke2"]),
                    bgcolor=APP_COLORS["search"],
                ),
                _filter_chips(selected_filter, on_filter_change),
                _stat_grid(situations, task_dataset, True),
                ft.Row(
                    spacing=22,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    controls=[
                        ft.Column(
                            spacing=16,
                            expand=True,
                            controls=[
                                ft.Text("Активные ситуации", size=26, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                                *situation_cards,
                                app_card(
                                    ft.Row(
                                        spacing=12,
                                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                        controls=[
                                            _icon_badge("blue", ft.Icons.CALENDAR_MONTH_OUTLINED),
                                            ft.Column(
                                                spacing=4,
                                                expand=True,
                                                controls=[
                                                    ft.Text("Напоминания", size=18, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                                                    ft.Text(
                                                        "Сроки задач и документы обновляются из локального состояния.",
                                                        size=13,
                                                        color=APP_COLORS["muted"],
                                                    ),
                                                ],
                                            ),
                                            secondary_button("Открыть", width=118, on_click=on_open_templates),
                                        ],
                                    ),
                                    padding=18,
                                ),
                            ],
                        ),
                        ft.Container(width=320, content=_desktop_sidebar(situations, task_dataset)),
                    ],
                ),
            ],
        ),
        width=1120,
        top=50,
    )


def _mobile_situations(
    open_situation,
    situations: list[dict],
    tasks: list[dict] | None = None,
    on_add_situation=None,
    on_edit_situation=None,
    on_delete_situation=None,
    on_open_templates=None,
    selected_filter: str = "Все",
    on_filter_change=None,
) -> ft.Control:
    task_dataset = tasks or []
    filtered = _filtered_situations(situations, task_dataset, selected_filter)
    situation_cards = [
        _situation_card(item, open_situation, False, on_edit_situation, on_delete_situation, task_dataset)
        for item in filtered
    ]
    if not situation_cards:
        situation_cards = [_empty_state(on_open_templates)]

    upcoming = _upcoming_tasks(task_dataset, situations, limit=2)
    upcoming_controls: list[ft.Control] = []
    if upcoming:
        upcoming_controls = [_side_task_card(task) for task in upcoming]
    else:
        upcoming_controls = [
            app_card(
                ft.Text("Ближайших задач нет. Все сроки под контролем.", size=13, color=APP_COLORS["muted"]),
                padding=16,
                bgcolor=APP_COLORS["surface2"],
            )
        ]

    return ft.Column(
        spacing=18,
        controls=[
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Column(
                        spacing=4,
                        expand=True,
                        controls=[
                            ft.Text("Мои ситуации", size=30, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                            ft.Text("Планы, задачи и сроки.", size=14, color=APP_COLORS["muted"]),
                        ],
                    ),
                    ft.IconButton(
                        icon=ft.Icons.ADD,
                        icon_color=APP_COLORS["blue"],
                        icon_size=28,
                        tooltip="Добавить ситуацию",
                        on_click=on_add_situation,
                    ),
                ],
            ),
            primary_button("Создать ситуацию", icon=ft.Icons.ADD, expand=True, on_click=on_add_situation),
            secondary_button("Выбрать готовый сценарий", icon=ft.Icons.ROUTE_OUTLINED, expand=True, on_click=on_open_templates),
            ft.Container(
                content=ft.Row(
                    spacing=10,
                    controls=[
                        ft.Icon(ft.Icons.SEARCH, size=21, color=APP_COLORS["blue"]),
                        ft.Text("Поиск по ситуациям...", size=14, color=APP_COLORS["muted"]),
                    ],
                ),
                height=54,
                padding=padding_symmetric(horizontal=16, vertical=0),
                border_radius=18,
                border=border_all(APP_COLORS["stroke2"]),
                bgcolor=APP_COLORS["search"],
            ),
            _filter_chips(selected_filter, on_filter_change, compact=True),
            _stat_grid(situations, task_dataset, False),
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text("Активные ситуации", size=22, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                    ft.Text("Все", size=13, weight=ft.FontWeight.W_800, color=APP_COLORS["blue_text"]),
                ],
            ),
            ft.Column(spacing=12, controls=situation_cards),
            ft.Text("Ближайшие задачи", size=22, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
            ft.Column(spacing=10, controls=upcoming_controls),
            _documents_panel(task_dataset, situations),
            ft.Container(height=SPACING["section"]),
        ],
    )


def build_situations_page(
    open_situation,
    is_desktop: bool = False,
    situations: list[dict] | None = None,
    tasks: list[dict] | None = None,
    on_add_situation=None,
    on_edit_situation=None,
    on_delete_situation=None,
    on_open_templates=None,
    selected_filter: str = "Все",
    on_filter_change=None,
) -> ft.Control:
    dataset = situations or []
    task_dataset = tasks or []
    if is_desktop:
        return _desktop_situations(
            open_situation,
            dataset,
            task_dataset,
            on_add_situation,
            on_edit_situation,
            on_delete_situation,
            on_open_templates,
            selected_filter,
            on_filter_change,
        )
    return _mobile_situations(
        open_situation,
        dataset,
        task_dataset,
        on_add_situation,
        on_edit_situation,
        on_delete_situation,
        on_open_templates,
        selected_filter,
        on_filter_change,
    )
