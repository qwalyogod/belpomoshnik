from __future__ import annotations

from datetime import date

import flet as ft

from components.buttons import primary_button, secondary_button
from components.cards import app_card, badge, empty_state_card, hint_card, icon_circle
from components.layout import desktop_content
from services.dashboard import format_due_date, parse_due_date
from theme.app_theme import APP_COLORS, SPACING, border_all, get_badge_palette, padding_symmetric, ts


TASK_FILTERS = [
    ("all", "Все"),
    ("available", "Доступные"),
    ("blocked", "Заблокированные"),
    ("completed", "Выполненные"),
    ("overdue", "Просроченные"),
]


def _find_situation(situation_id: str, situations: list[dict]) -> dict:
    fallback = {
        "id": "empty",
        "title": "Ситуация",
        "status": "Не начата",
        "progress": 0,
        "description": "Личный план по жизненной ситуации.",
    }
    return next((item for item in situations if item.get("id") == situation_id), situations[0] if situations else fallback)


def _task_is_overdue(task: dict) -> bool:
    due_date = parse_due_date(task.get("due_date"))
    return bool(due_date and due_date < date.today() and not task.get("completed"))


def _task_deadline_text(task: dict, short: bool = False) -> str:
    due_date = parse_due_date(task.get("due_date"))
    if due_date:
        prefix = "до" if short else (task.get("deadline") or "Срок")
        return f"{prefix} {format_due_date(due_date)}"
    return task.get("deadline") or "Без срока"


def _filter_tasks(tasks: list[dict], task_filter: str) -> list[dict]:
    if task_filter == "available":
        return [task for task in tasks if not task.get("completed") and not task.get("blocked")]
    if task_filter == "blocked":
        return [task for task in tasks if task.get("blocked") and not task.get("completed")]
    if task_filter == "completed":
        return [task for task in tasks if task.get("completed")]
    if task_filter == "overdue":
        return [task for task in tasks if _task_is_overdue(task)]
    return tasks


def _progress(tasks: list[dict]) -> int:
    if not tasks:
        return 0
    completed = len([task for task in tasks if task.get("completed")])
    return round(completed / len(tasks) * 100)


def _status_by_progress(progress: int, current_status: str | None) -> str:
    if progress == 100:
        return "Завершена"
    if progress > 0:
        return "В процессе"
    return current_status or "Не начата"


def _status_variant(status: str) -> str:
    normalized = status.lower()
    if "заверш" in normalized:
        return "success"
    if "процесс" in normalized:
        return "blue"
    if "проср" in normalized:
        return "error"
    return "default"


def _task_variant(task: dict) -> str:
    if task.get("completed"):
        return "success"
    if task.get("blocked"):
        return "default"
    if _task_is_overdue(task):
        return "error"
    return "blue"


def _task_label(task: dict) -> str:
    if task.get("completed"):
        return "Выполнено"
    if task.get("blocked"):
        return "Заблокировано"
    if _task_is_overdue(task):
        return "Просрочено"
    return "Доступно"


def _filter_chip(label: str, key: str, selected: bool, on_select=None) -> ft.Container:
    return ft.Container(
        content=ft.Text(
            label,
            size=ts(13),
            weight=ft.FontWeight.W_800,
            color=ft.Colors.WHITE if selected else APP_COLORS["text"],
            no_wrap=True,
        ),
        padding=padding_symmetric(horizontal=15, vertical=9),
        border_radius=18,
        bgcolor=APP_COLORS["blue"] if selected else APP_COLORS["surface2"],
        border=border_all(APP_COLORS["blue"] if selected else APP_COLORS["stroke2"]),
        on_click=lambda _: on_select(key) if on_select else None,
        ink=True,
    )


def _progress_bar(value: int, color: str | None = None) -> ft.ProgressBar:
    return ft.ProgressBar(
        value=max(0, min(100, value)) / 100,
        color=color or APP_COLORS["green"],
        bgcolor=APP_COLORS["stroke2"],
        height=8,
        border_radius=999,
    )


def _unique_task_documents(tasks: list[dict]) -> list[dict]:
    documents_by_title: dict[str, dict] = {}
    for task in tasks:
        for document in task.get("documents", []):
            title = (document.get("title") or "").strip()
            if not title:
                continue
            key = title.lower()
            if key not in documents_by_title:
                documents_by_title[key] = {
                    "title": title,
                    "required": bool(document.get("required")),
                    "tasks": [task.get("title", "Задача")],
                }
            else:
                documents_by_title[key]["required"] = documents_by_title[key]["required"] or bool(document.get("required"))
                task_title = task.get("title", "Задача")
                if task_title not in documents_by_title[key]["tasks"]:
                    documents_by_title[key]["tasks"].append(task_title)
    return list(documents_by_title.values())


def _unique_institutions(tasks: list[dict]) -> list[dict]:
    institutions_by_key: dict[str, dict] = {}
    for task in tasks:
        for institution in task.get("matched_institutions", []):
            key = str(institution.get("id") or institution.get("short_name") or institution.get("full_name") or "").lower()
            if key and key not in institutions_by_key:
                institutions_by_key[key] = institution
    return list(institutions_by_key.values())


def _nearest_tasks(tasks: list[dict], limit: int = 4) -> list[dict]:
    open_tasks = [
        task
        for task in tasks
        if not task.get("completed") and parse_due_date(task.get("due_date"))
    ]
    return sorted(open_tasks, key=lambda task: parse_due_date(task.get("due_date")) or date.max)[:limit]


def _stage_groups(tasks: list[dict]) -> list[tuple[str, list[dict]]]:
    groups: list[tuple[str, list[dict]]] = []
    stage_index: dict[str, int] = {}
    for task in tasks:
        stage_title = task.get("stage_title") or "Личные задачи"
        if stage_title not in stage_index:
            stage_index[stage_title] = len(groups)
            groups.append((stage_title, []))
        groups[stage_index[stage_title]][1].append(task)
    return groups


def _compact_meta(icon: str, text: str, tone: str = "default") -> ft.Row:
    palette = get_badge_palette()
    color = palette.get(tone, palette["gray"])[1]
    return ft.Row(
        spacing=6,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Icon(icon, size=ts(16), color=color),
            ft.Text(text, size=ts(12), color=APP_COLORS["muted"], expand=True),
        ],
    )


def _documents_preview(task: dict) -> ft.Control:
    documents = task.get("documents", [])
    if not documents:
        return ft.Container()
    labels = []
    for document in documents[:3]:
        suffix = "обяз." if document.get("required") else "по ситуации"
        labels.append(f"{document.get('title', 'Документ')} ({suffix})")
    extra = len(documents) - 3
    text = ", ".join(labels)
    if extra > 0:
        text = f"{text} + ещё {extra}"
    return _compact_meta(ft.Icons.ARTICLE_OUTLINED, text, "blue")


def _task_card(
    task: dict,
    desktop: bool,
    on_toggle_task=None,
    on_edit_task=None,
    on_delete_task=None,
) -> ft.Container:
    blocked = bool(task.get("blocked")) and not task.get("completed")
    palette = get_badge_palette()
    tone = _task_variant(task)
    tone_bg, tone_fg = palette.get(tone, palette["gray"])
    muted_bg, muted_fg = palette["gray"]
    card_bg = APP_COLORS["surface2"] if blocked else APP_COLORS["surface"]
    icon_bg = muted_bg if blocked else tone_bg
    icon_fg = muted_fg if blocked else tone_fg

    title_color = APP_COLORS["muted"] if task.get("completed") else APP_COLORS["text"]
    action_icons = ft.Row(
        spacing=0,
        controls=[
            ft.IconButton(
                icon=ft.Icons.EDIT_OUTLINED,
                icon_size=19,
                icon_color=APP_COLORS["muted2"],
                tooltip="Редактировать",
                on_click=lambda _, task_id=task["id"]: on_edit_task(task_id) if on_edit_task else None,
            ),
            ft.IconButton(
                icon=ft.Icons.DELETE_OUTLINE,
                icon_size=19,
                icon_color=APP_COLORS["red"],
                tooltip="Удалить",
                on_click=lambda _, task_id=task["id"]: on_delete_task(task_id) if on_delete_task else None,
            ),
        ],
    )

    body_controls: list[ft.Control] = [
        ft.Row(
            spacing=8,
            run_spacing=8,
            wrap=True,
            controls=[
                badge(_task_label(task), tone),
                badge(_task_deadline_text(task, short=True), "error" if _task_is_overdue(task) else "default"),
            ],
        ),
        ft.Text(
            task.get("title", "Задача"),
            size=ts(16) if desktop else 15,
            weight=ft.FontWeight.W_900,
            color=title_color,
            max_lines=3,
        ),
    ]
    if task.get("description"):
        body_controls.append(
            ft.Text(
                task["description"],
                size=ts(13),
                color=APP_COLORS["muted"],
                max_lines=3,
            )
        )
    if blocked:
        body_controls.append(
            ft.Container(
                padding=12,
                border_radius=16,
                bgcolor=get_badge_palette()["orange"][0],
                border=border_all(APP_COLORS["stroke2"]),
                content=ft.Row(
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    controls=[
                        ft.Icon(ft.Icons.LOCK_OUTLINE, size=ts(17), color=get_badge_palette()["orange"][1]),
                        ft.Text(
                            task.get("blocked_reason", "Сначала выполните предыдущий шаг."),
                            size=ts(12),
                            color=get_badge_palette()["orange"][1],
                            expand=True,
                        ),
                    ],
                ),
            )
        )

    body_controls.append(
        ft.Column(
            spacing=7,
            controls=[
                _compact_meta(ft.Icons.SCHEDULE, _task_deadline_text(task), "default"),
                _documents_preview(task),
            ],
        )
    )

    return ft.Container(
        padding=16,
        border_radius=22,
        bgcolor=card_bg,
        border=border_all(APP_COLORS["stroke2"]),
        content=ft.Row(
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                ft.Container(
                    width=44,
                    height=44,
                    border_radius=22,
                    bgcolor=icon_bg,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Checkbox(
                        value=bool(task.get("completed")),
                        disabled=blocked,
                        active_color=APP_COLORS["green"],
                        check_color=ft.Colors.WHITE,
                        on_change=lambda event, task_id=task["id"]: on_toggle_task(task_id, bool(event.control.value))
                        if on_toggle_task and not blocked
                        else None,
                    ),
                ),
                ft.Column(spacing=9, expand=True, controls=body_controls),
                action_icons if desktop else ft.Container(),
            ],
        ),
    )


def _stage_card(
    title: str,
    tasks: list[dict],
    desktop: bool,
    on_toggle_task=None,
    on_edit_task=None,
    on_delete_task=None,
) -> ft.Container:
    progress = _progress(tasks)
    completed = len([task for task in tasks if task.get("completed")])
    blocked_count = len([task for task in tasks if task.get("blocked") and not task.get("completed")])
    task_controls = [
        _task_card(task, desktop, on_toggle_task, on_edit_task, on_delete_task)
        for task in tasks
    ]
    return app_card(
        ft.Column(
            spacing=14,
            controls=[
                ft.Row(
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    controls=[
                        icon_circle(ft.Icons.ACCOUNT_TREE_OUTLINED, color=APP_COLORS["blue_text"], bgcolor=APP_COLORS["active"], size=46),
                        ft.Column(
                            spacing=7,
                            expand=True,
                            controls=[
                                ft.Text(title, size=ts(18) if desktop else 17, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                                ft.Row(
                                    wrap=True,
                                    spacing=8,
                                    run_spacing=8,
                                    controls=[
                                        badge(f"{completed}/{len(tasks)} задач", "success" if progress == 100 else "blue"),
                                        badge(f"{progress}% этапа", "default"),
                                        badge(f"{blocked_count} заблок.", "warning") if blocked_count else ft.Container(),
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
                _progress_bar(progress, APP_COLORS["blue"]),
                ft.Column(spacing=10, controls=task_controls),
            ],
        ),
        padding=18 if desktop else 16,
    )


def _stat_tile(label: str, value: str, icon: str, tone: str = "blue") -> ft.Container:
    palette = get_badge_palette()
    bg, fg = palette.get(tone, palette["blue"])
    return ft.Container(
        padding=16,
        border_radius=22,
        bgcolor=APP_COLORS["surface"],
        border=border_all(APP_COLORS["stroke2"]),
        content=ft.Column(
            spacing=8,
            controls=[
                icon_circle(icon, color=fg, bgcolor=bg, size=42),
                ft.Text(value, size=ts(23), weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                ft.Text(label, size=ts(12), color=APP_COLORS["muted"], weight=ft.FontWeight.W_700),
            ],
        ),
    )


def _tap_button(
    text: str,
    icon: str,
    on_click=None,
    *,
    primary: bool = False,
    width: int | float | None = None,
) -> ft.Container:
    return ft.Container(
        height=48,
        width=width,
        padding=padding_symmetric(horizontal=16, vertical=0),
        border_radius=16,
        bgcolor=APP_COLORS["blue"] if primary else APP_COLORS["surface"],
        border=border_all(APP_COLORS["blue"] if primary else APP_COLORS["stroke2"]),
        alignment=ft.Alignment(0, 0),
        ink=True,
        on_click=on_click,
        content=ft.Row(
            spacing=8,
            tight=True,
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(icon, size=ts(18), color=ft.Colors.WHITE if primary else APP_COLORS["text"]),
                ft.Text(
                    text,
                    size=ts(14),
                    weight=ft.FontWeight.W_900,
                    color=ft.Colors.WHITE if primary else APP_COLORS["text"],
                    no_wrap=True,
                ),
            ],
        ),
    )


def _stats_grid(tasks: list[dict], progress: int, desktop: bool) -> ft.Control:
    stages = len(_stage_groups(tasks))
    documents = len(_unique_task_documents(tasks))
    nearest = _nearest_tasks(tasks, 1)
    deadline = _task_deadline_text(nearest[0], short=True) if nearest else "нет сроков"
    tiles = [
        _stat_tile("Этапов", str(stages), ft.Icons.ACCOUNT_TREE_OUTLINED, "blue"),
        _stat_tile("Задач", str(len(tasks)), ft.Icons.CHECKLIST_RTL, "green"),
        _stat_tile("Документов", str(documents), ft.Icons.ARTICLE_OUTLINED, "purple"),
        _stat_tile("Ближайший срок", deadline, ft.Icons.SCHEDULE, "orange"),
    ]
    if desktop:
        return ft.Row(spacing=12, controls=[ft.Container(expand=True, content=tile) for tile in tiles])
    return ft.Column(spacing=10, controls=[
        ft.Row(spacing=10, controls=[ft.Container(expand=True, content=tiles[0]), ft.Container(expand=True, content=tiles[1])]),
        ft.Row(spacing=10, controls=[ft.Container(expand=True, content=tiles[2]), ft.Container(expand=True, content=tiles[3])]),
    ])


def _hero_card(
    situation: dict,
    progress: int,
    tasks: list[dict],
    desktop: bool,
    on_add_task=None,
    on_edit_situation=None,
    on_delete_situation=None,
) -> ft.Container:
    completed = len([task for task in tasks if task.get("completed")])
    status = _status_by_progress(progress, situation.get("status"))
    description = situation.get("description") or "Личный план с задачами, документами и сроками по выбранной жизненной ситуации."
    badges: list[ft.Control] = [
        badge(status, _status_variant(status)),
        badge(f"{progress}% прогресс", "green"),
    ]
    nearest = _nearest_tasks(tasks, 1)
    if nearest:
        badges.append(badge(_task_deadline_text(nearest[0], short=True), "orange" if not _task_is_overdue(nearest[0]) else "error"))

    action_controls = [
        _tap_button("Добавить задачу", ft.Icons.ADD, on_add_task, primary=True, width=180 if desktop else None),
        _tap_button(
            "Редактировать",
            ft.Icons.EDIT_OUTLINED,
            lambda _: on_edit_situation(situation["id"]) if on_edit_situation else None,
            width=164 if desktop else None,
        ),
    ]
    if desktop:
        action_controls.append(
            _tap_button(
                "Удалить",
                ft.Icons.DELETE_OUTLINE,
                lambda _: on_delete_situation(situation["id"]) if on_delete_situation else None,
                width=132,
            )
        )
    action_row = (
        ft.Row(spacing=10, controls=action_controls)
        if desktop
        else ft.Column(spacing=10, controls=action_controls)
    )

    return ft.Container(
        padding=28 if desktop else 22,
        border_radius=30,
        bgcolor=APP_COLORS["surface3"],
        border=border_all(APP_COLORS["stroke2"]),
        content=ft.Column(
            spacing=18,
            controls=[
                ft.Row(wrap=True, spacing=8, run_spacing=8, controls=badges),
                ft.Text(
                    situation.get("title", "Ситуация"),
                    size=ts(34) if desktop else 25,
                    weight=ft.FontWeight.W_900,
                    color=APP_COLORS["text"],
                    max_lines=3,
                ),
                ft.Text(description, size=ts(15), color=APP_COLORS["muted"], max_lines=4),
                ft.Column(
                    spacing=8,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text("Общий прогресс", size=ts(14), color=APP_COLORS["text"], weight=ft.FontWeight.W_800),
                                ft.Text(f"{completed}/{len(tasks)} задач", size=ts(13), color=APP_COLORS["muted"], weight=ft.FontWeight.W_700),
                            ],
                        ),
                        _progress_bar(progress),
                    ],
                ),
                action_row,
            ],
        ),
    )


def _next_step_card(tasks: list[dict], desktop: bool, on_add_task=None) -> ft.Container:
    available = [
        task
        for task in tasks
        if not task.get("completed") and not task.get("blocked")
    ]
    next_task = sorted(available, key=lambda task: parse_due_date(task.get("due_date")) or date.max)[0] if available else None
    if not next_task:
        return hint_card("Все доступные задачи выполнены. Добавьте новую задачу или проверьте заблокированные шаги.", ft.Icons.CHECK_CIRCLE_OUTLINE)

    return app_card(
        ft.Row(
            spacing=14,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                icon_circle(ft.Icons.PLAY_CIRCLE_OUTLINE, color=APP_COLORS["green"], bgcolor=get_badge_palette()["green"][0], size=52),
                ft.Column(
                    spacing=8,
                    expand=True,
                    controls=[
                        badge("Следующий шаг", "success"),
                        ft.Text(next_task.get("title", "Задача"), size=ts(19) if desktop else 17, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                        ft.Text(_task_deadline_text(next_task), size=ts(13), color=APP_COLORS["muted"]),
                    ],
                ),
                secondary_button("Добавить", icon=ft.Icons.ADD, on_click=on_add_task, width=130) if desktop else ft.Container(),
            ],
        ),
        padding=18,
        bgcolor=APP_COLORS["surface3"],
        border_color=APP_COLORS["stroke2"],
    )


def _tasks_section(
    tasks: list[dict],
    desktop: bool,
    on_toggle_task=None,
    on_edit_task=None,
    on_delete_task=None,
    on_add_task=None,
    task_filter: str = "all",
    on_task_filter_change=None,
) -> ft.Column:
    filter_bar = ft.Row(
        wrap=True,
        spacing=8,
        run_spacing=8,
        controls=[
            _filter_chip(label, key, task_filter == key, on_task_filter_change)
            for key, label in TASK_FILTERS
        ],
    )
    if not tasks:
        return ft.Column(
            spacing=12,
            controls=[
                filter_bar,
                empty_state_card(
                    "Задач пока нет",
                    "Добавьте свою задачу или создайте ситуацию из готового сценария.",
                    "Добавить задачу",
                    on_add_task,
                    ft.Icons.TASK_ALT_OUTLINED,
                ),
            ],
        )

    filtered = _filter_tasks(tasks, task_filter)
    if not filtered:
        return ft.Column(
            spacing=12,
            controls=[
                filter_bar,
                empty_state_card(
                    "Задач в этом фильтре нет",
                    "Выберите другой фильтр или добавьте новую задачу.",
                    "Добавить задачу",
                    on_add_task,
                    ft.Icons.FILTER_ALT_OUTLINED,
                ),
            ],
        )

    stage_cards = [
        _stage_card(stage_title, stage_tasks, desktop, on_toggle_task, on_edit_task, on_delete_task)
        for stage_title, stage_tasks in _stage_groups(filtered)
    ]
    return ft.Column(
        spacing=16,
        controls=[
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text("Задачи по этапам", size=ts(23) if desktop else 21, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                    secondary_button("Добавить", icon=ft.Icons.ADD, width=130, on_click=on_add_task) if desktop else ft.Container(),
                ],
            ),
            filter_bar,
            ft.Column(spacing=14, controls=stage_cards),
        ],
    )


def _documents_block(tasks: list[dict], desktop: bool) -> ft.Container:
    documents = _unique_task_documents(tasks)
    if not documents:
        return empty_state_card(
            "Документы не привязаны",
            "Когда у задачи появятся документы, они будут собраны здесь одним списком.",
            None,
            None,
            ft.Icons.FOLDER_OPEN_OUTLINED,
        )

    controls: list[ft.Control] = [
        ft.Row(
            spacing=10,
            controls=[
                ft.Icon(ft.Icons.ARTICLE_OUTLINED, size=ts(22), color=APP_COLORS["blue_text"]),
                ft.Text("Документы", size=ts(20) if desktop else 19, weight=ft.FontWeight.W_900, color=APP_COLORS["text"], expand=True),
            ],
        )
    ]
    for document in documents:
        controls.append(
            ft.Container(
                padding=14,
                border_radius=18,
                bgcolor=APP_COLORS["surface2"],
                border=border_all(APP_COLORS["stroke2"]),
                content=ft.Row(
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    controls=[
                        icon_circle(
                            ft.Icons.CHECKLIST_RTL if document["required"] else ft.Icons.INFO_OUTLINE,
                            color=APP_COLORS["blue_text"] if document["required"] else APP_COLORS["muted2"],
                            bgcolor=APP_COLORS["active"] if document["required"] else APP_COLORS["surface"],
                            size=40,
                        ),
                        ft.Column(
                            spacing=5,
                            expand=True,
                            controls=[
                                ft.Row(
                                    wrap=True,
                                    spacing=8,
                                    run_spacing=8,
                                    controls=[
                                        ft.Text(document["title"], size=ts(15), weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                                        badge("Обязательно" if document["required"] else "По ситуации", "success" if document["required"] else "default"),
                                    ],
                                ),
                                ft.Text(
                                    f"Нужно для: {', '.join(document['tasks'][:2])}" + ("..." if len(document["tasks"]) > 2 else ""),
                                    size=ts(12),
                                    color=APP_COLORS["muted"],
                                ),
                            ],
                        ),
                    ],
                ),
            )
        )
    return app_card(ft.Column(spacing=12, controls=controls), padding=18 if desktop else 16)


def _institutions_block(tasks: list[dict], desktop: bool) -> ft.Control:
    institutions = _unique_institutions(tasks)
    if not institutions:
        return app_card(
            ft.Column(
                spacing=10,
                controls=[
                    ft.Row(
                        spacing=10,
                        controls=[
                            ft.Icon(ft.Icons.ACCOUNT_BALANCE_OUTLINED, size=ts(22), color=APP_COLORS["blue_text"]),
                            ft.Text("Куда обращаться", size=ts(20) if desktop else 19, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                        ],
                    ),
                    ft.Text("Подходящие учреждения появятся после уточнения профиля и задач.", size=ts(14), color=APP_COLORS["muted"]),
                ],
            ),
            padding=18,
        )
    controls: list[ft.Control] = [
        ft.Row(
            spacing=10,
            controls=[
                ft.Icon(ft.Icons.ACCOUNT_BALANCE_OUTLINED, size=ts(22), color=APP_COLORS["blue_text"]),
                ft.Text("Куда обращаться", size=ts(20) if desktop else 19, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
            ],
        )
    ]
    for institution in institutions[:4]:
        controls.append(
            ft.Container(
                padding=14,
                border_radius=18,
                bgcolor=APP_COLORS["surface2"],
                border=border_all(APP_COLORS["stroke2"]),
                content=ft.Column(
                    spacing=7,
                    controls=[
                        ft.Row(
                            wrap=True,
                            spacing=8,
                            run_spacing=8,
                            controls=[
                                ft.Text(
                                    institution.get("short_name") or institution.get("full_name", "Учреждение"),
                                    size=ts(15),
                                    weight=ft.FontWeight.W_900,
                                    color=APP_COLORS["text"],
                                    expand=True,
                                ),
                                badge(institution.get("institution_type", "Учреждение"), "blue"),
                            ],
                        ),
                        ft.Text(institution.get("address") or "Адрес требует уточнения", size=ts(13), color=APP_COLORS["muted"]),
                        ft.Text(
                            " · ".join(item for item in [institution.get("phone"), institution.get("website")] if item)
                            or "Контакты требуют уточнения",
                            size=ts(12),
                            color=APP_COLORS["muted2"],
                        ),
                    ],
                ),
            )
        )
    return app_card(ft.Column(spacing=12, controls=controls), padding=18 if desktop else 16)


def _summary_card(progress: int, tasks: list[dict]) -> ft.Container:
    completed = len([task for task in tasks if task.get("completed")])
    blocked = len([task for task in tasks if task.get("blocked") and not task.get("completed")])
    overdue = len([task for task in tasks if _task_is_overdue(task)])
    return app_card(
        ft.Column(
            spacing=14,
            controls=[
                ft.Text("Сводка", size=ts(20), weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text("Прогресс", size=ts(13), color=APP_COLORS["muted"], weight=ft.FontWeight.W_700),
                        ft.Text(f"{progress}%", size=ts(16), color=APP_COLORS["green"], weight=ft.FontWeight.W_900),
                    ],
                ),
                _progress_bar(progress),
                ft.Divider(height=1, color=APP_COLORS["stroke2"]),
                _compact_meta(ft.Icons.CHECK_CIRCLE_OUTLINE, f"Выполнено {completed} из {len(tasks)}", "green"),
                _compact_meta(ft.Icons.LOCK_OUTLINE, f"Заблокировано: {blocked}", "default"),
                _compact_meta(ft.Icons.WARNING_AMBER_OUTLINED, f"Просрочено: {overdue}", "orange" if overdue else "default"),
            ],
        ),
        padding=18,
    )


def _nearest_deadlines_card(tasks: list[dict]) -> ft.Container:
    nearest = _nearest_tasks(tasks, 4)
    controls: list[ft.Control] = [
        ft.Text("Ближайшие сроки", size=ts(20), weight=ft.FontWeight.W_900, color=APP_COLORS["text"])
    ]
    if not nearest:
        controls.append(ft.Text("Активных сроков пока нет.", size=ts(13), color=APP_COLORS["muted"]))
    for task in nearest:
        controls.append(
            ft.Container(
                padding=12,
                border_radius=16,
                bgcolor=APP_COLORS["surface2"],
                border=border_all(APP_COLORS["stroke2"]),
                content=ft.Column(
                    spacing=5,
                    controls=[
                        ft.Text(task.get("title", "Задача"), size=ts(13), weight=ft.FontWeight.W_900, color=APP_COLORS["text"], max_lines=2),
                        ft.Text(_task_deadline_text(task, short=True), size=ts(12), color=APP_COLORS["muted"]),
                    ],
                ),
            )
        )
    return app_card(ft.Column(spacing=10, controls=controls), padding=18)


def _notes_card(
    desktop: bool,
    notes: list[dict] | None = None,
    on_add_note=None,
) -> ft.Container:
    """Real notes card with add form and reminder date."""
    note_field = ft.TextField(
        hint_text="Добавить заметку...",
        expand=True,
        multiline=True,
        min_lines=2,
        max_lines=4,
        border_radius=14,
        border_color=APP_COLORS["stroke2"],
        focused_border_color=APP_COLORS["blue"],
        cursor_color=APP_COLORS["blue"],
        text_size=14,
        color=APP_COLORS["text"],
    )
    reminder_field = ft.TextField(
        hint_text="Дата напоминания (ДД.ММ.ГГГГ)",
        width=200 if desktop else None,
        expand=not desktop,
        border_radius=12,
        border_color=APP_COLORS["stroke2"],
        focused_border_color=APP_COLORS["blue"],
        cursor_color=APP_COLORS["blue"],
        text_size=13,
        color=APP_COLORS["text"],
    )

    def _submit(_=None) -> None:
        text = (note_field.value or "").strip()
        reminder = (reminder_field.value or "").strip()
        if text and on_add_note:
            on_add_note({"text": text, "reminder_date": reminder})
            note_field.value = ""
            reminder_field.value = ""
            note_field.update()
            reminder_field.update()

    existing_notes: list[ft.Control] = []
    for note in (notes or []):
        reminder_text = f"  ·  напоминание {note['reminder_date']}" if note.get("reminder_date") else ""
        existing_notes.append(
            ft.Container(
                padding=ft.Padding(left=12, top=8, right=12, bottom=8),
                border_radius=12,
                bgcolor=APP_COLORS["surface2"],
                content=ft.Column(
                    spacing=4,
                    controls=[
                        ft.Text(note["text"], size=ts(13), color=APP_COLORS["text"]),
                        ft.Text(
                            f"{note.get('date', '')} {reminder_text}",
                            size=ts(11),
                            color=APP_COLORS["muted2"],
                        ),
                    ],
                ),
            )
        )

    add_form = ft.Column(
        spacing=8,
        controls=[
            note_field,
            ft.Row(
                spacing=8,
                controls=[
                    reminder_field,
                    ft.Container(
                        ink=True,
                        border_radius=12,
                        padding=ft.Padding(left=14, top=10, right=14, bottom=10),
                        bgcolor=APP_COLORS["blue"],
                        on_click=_submit,
                        content=ft.Row(
                            spacing=6,
                            controls=[
                                ft.Icon(ft.Icons.ADD, size=ts(16), color=ft.Colors.WHITE),
                                ft.Text("Добавить", size=ts(13), weight=ft.FontWeight.W_700, color=ft.Colors.WHITE),
                            ],
                        ),
                    ),
                ],
            ),
        ],
    )

    return app_card(
        ft.Column(
            spacing=14,
            controls=[
                ft.Row(
                    spacing=10,
                    controls=[
                        ft.Icon(ft.Icons.STICKY_NOTE_2_OUTLINED, size=ts(20), color=APP_COLORS["blue_text"]),
                        ft.Text("Заметки", size=ts(20) if desktop else 19, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                    ],
                ),
                *existing_notes,
                add_form,
            ],
        ),
        padding=18,
    )


def _desktop_content(
    situation: dict,
    progress: int,
    tasks: list[dict],
    go_back,
    on_toggle_task=None,
    on_add_task=None,
    on_edit_task=None,
    on_delete_task=None,
    on_edit_situation=None,
    on_delete_situation=None,
    on_save=None,
    task_filter: str = "all",
    notes: list[dict] | None = None,
    on_add_note=None,
    on_task_filter_change=None,
) -> ft.Control:
    left_column = ft.Column(
        spacing=20,
        expand=True,
        controls=[
            ft.Row(
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        content=ft.Row(
                            spacing=6,
                            controls=[
                                ft.Icon(ft.Icons.ARROW_BACK, size=ts(18), color=APP_COLORS["blue_text"]),
                                ft.Text("Мои ситуации", size=ts(14), weight=ft.FontWeight.W_800, color=APP_COLORS["blue_text"]),
                            ],
                        ),
                        on_click=go_back,
                        ink=True,
                    ),
                ],
            ),
            _hero_card(situation, progress, tasks, True, on_add_task, on_edit_situation, on_delete_situation),
            _stats_grid(tasks, progress, True),
            _next_step_card(tasks, True, on_add_task),
            hint_card("Отмечайте задачи выполненными — прогресс обновится автоматически.", ft.Icons.LIGHTBULB_OUTLINE),
            _tasks_section(
                tasks,
                True,
                on_toggle_task,
                on_edit_task,
                on_delete_task,
                on_add_task,
                task_filter,
                on_task_filter_change,
            ),
            _documents_block(tasks, True),
            _institutions_block(tasks, True),
            _notes_card(True, notes=notes, on_add_note=on_add_note),
            primary_button("Сохранить изменения", icon=ft.Icons.CHECK_CIRCLE, on_click=on_save, width=240),
        ],
    )
    right_column = ft.Column(
        spacing=16,
        width=330,
        controls=[
            _summary_card(progress, tasks),
            _nearest_deadlines_card(tasks),
            _documents_block(tasks, True),
            _institutions_block(tasks, True),
            app_card(
                ft.Column(
                    spacing=10,
                    controls=[
                        ft.Text("Быстрые действия", size=ts(20), weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                        secondary_button("Редактировать ситуацию", icon=ft.Icons.EDIT_OUTLINED, expand=True, on_click=lambda _: on_edit_situation(situation["id"]) if on_edit_situation else None),
                        secondary_button("Добавить задачу", icon=ft.Icons.ADD, expand=True, on_click=on_add_task),
                    ],
                ),
                padding=18,
            ),
        ],
    )
    return desktop_content(
        ft.Row(
            spacing=26,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[left_column, right_column],
        ),
        width=1180,
        top=46,
        bottom=120,
    )


def _mobile_content(
    situation: dict,
    progress: int,
    tasks: list[dict],
    go_back,
    on_toggle_task=None,
    on_add_task=None,
    on_edit_task=None,
    on_delete_task=None,
    on_edit_situation=None,
    on_delete_situation=None,
    on_save=None,
    task_filter: str = "all",
    on_task_filter_change=None,
    notes: list[dict] | None = None,
    on_add_note=None,
) -> ft.Control:
    status = _status_by_progress(progress, situation.get("status"))
    content = ft.Column(
        spacing=18,
        controls=[
            ft.Row(
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=APP_COLORS["muted"], on_click=go_back),
                    ft.Text("Детали ситуации", size=ts(20), weight=ft.FontWeight.W_900, color=APP_COLORS["text"], expand=True),
                    ft.IconButton(
                        icon=ft.Icons.EDIT_OUTLINED,
                        icon_color=APP_COLORS["muted2"],
                        tooltip="Редактировать",
                        on_click=lambda _: on_edit_situation(situation["id"]) if on_edit_situation else None,
                    ),
                ],
            ),
            ft.Row(
                wrap=True,
                spacing=8,
                run_spacing=8,
                controls=[
                    badge(status, _status_variant(status)),
                    badge(f"{progress}% прогресс", "green"),
                ],
            ),
            _hero_card(situation, progress, tasks, False, on_add_task, on_edit_situation, on_delete_situation),
            _next_step_card(tasks, False, on_add_task),
            _stats_grid(tasks, progress, False),
            hint_card("Отмечайте задачи выполненными — прогресс обновится автоматически.", ft.Icons.LIGHTBULB_OUTLINE),
            _tasks_section(
                tasks,
                False,
                on_toggle_task,
                on_edit_task,
                on_delete_task,
                on_add_task,
                task_filter,
                on_task_filter_change,
            ),
            secondary_button("Добавить задачу", icon=ft.Icons.ADD, expand=True, on_click=on_add_task),
            _documents_block(tasks, False),
            _institutions_block(tasks, False),
            _notes_card(False, notes=notes, on_add_note=on_add_note),
            primary_button("Сохранить изменения", icon=ft.Icons.CHECK_CIRCLE, expand=True, on_click=on_save),
        ],
    )
    return ft.Container(width=340, content=content)


def build_situation_detail_page(
    situation_id: str,
    go_back,
    is_desktop: bool = False,
    situations: list[dict] | None = None,
    tasks: list[dict] | None = None,
    on_toggle_task=None,
    on_add_task=None,
    on_edit_task=None,
    on_delete_task=None,
    on_edit_situation=None,
    on_delete_situation=None,
    on_save=None,
    task_filter: str = "all",
    on_task_filter_change=None,
    notes: list[dict] | None = None,
    on_add_note=None,
) -> ft.Control:
    dataset = situations or []
    task_dataset = [
        task
        for task in (tasks or [])
        if task.get("situation_id", situation_id) == situation_id
    ]
    task_dataset = sorted(
        task_dataset,
        key=lambda task: (
            task.get("stage_order", 999),
            task.get("order_index", 999),
            task.get("due_date", ""),
            task.get("title", ""),
        ),
    )
    situation = _find_situation(situation_id, dataset)
    progress = _progress(task_dataset)
    if is_desktop:
        return _desktop_content(
            situation,
            progress,
            task_dataset,
            go_back,
            on_toggle_task,
            on_add_task,
            on_edit_task,
            on_delete_task,
            on_edit_situation,
            on_delete_situation,
            on_save,
            task_filter,
            on_task_filter_change,
            notes=notes,
            on_add_note=on_add_note,
        )
    return _mobile_content(
        situation,
        progress,
        task_dataset,
        go_back,
        on_toggle_task,
        on_add_task,
        on_edit_task,
        on_delete_task,
        on_edit_situation,
        on_delete_situation,
        on_save,
        task_filter,
        on_task_filter_change,
        notes=notes,
        on_add_note=on_add_note,
    )
