from __future__ import annotations

from datetime import date

import flet as ft

from components.buttons import ghost_button, primary_button, secondary_button
from components.cards import app_card, badge, category_chip, empty_state_card, icon_circle, section_title
from components.layout import desktop_content
from data.mock_data import CATEGORIES, LEGAL_UPDATES, MOCK_USER, NOTIFICATIONS, PROBLEMS, SCENARIO_TEMPLATES
from theme.app_theme import APP_COLORS, APP_RADIUS, CENTER, GRADIENT_FUTUREWAFE, SPACING, border_all, padding_symmetric, ts


def _icon(name: str) -> str:
    return getattr(ft.Icons, name, ft.Icons.ARTICLE_OUTLINED)


def _notification_icon(notification_type: str) -> str:
    icons = {
        "document": ft.Icons.SCHEDULE_OUTLINED,
        "task": ft.Icons.EVENT_AVAILABLE_OUTLINED,
        "law": ft.Icons.BALANCE_OUTLINED,
        "utility": ft.Icons.HOME_WORK_OUTLINED,
        "tax": ft.Icons.RECEIPT_LONG_OUTLINED,
    }
    return icons.get(notification_type, ft.Icons.NOTIFICATIONS_NONE_OUTLINED)


def _run_home_search(search_field: ft.TextField, run_search, go_to) -> None:
    query = (search_field.value or "").strip()
    if run_search:
        run_search(query)
    else:
        go_to("/problems")


def _empty_state(title: str, text: str, action_text: str | None = None, on_click=None) -> ft.Container:
    return empty_state_card(title, text, action_text, on_click)


def _demo_tip(text: str) -> ft.Container:
    return app_card(
        ft.Row(
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                icon_circle(ft.Icons.TIPS_AND_UPDATES_OUTLINED, color=APP_COLORS["blue"], bgcolor=APP_COLORS["active"], size=38),
                ft.Text(text, size=ts(14), color=APP_COLORS["muted"], expand=True),
            ],
        ),
        padding=14,
        bgcolor=APP_COLORS["surface3"],
        border_color=APP_COLORS["stroke2"],
    )


def _search_hero(search_field: ft.TextField, run_search, go_to, desktop: bool) -> ft.Container:
    field = ft.Container(
        expand=True,
        border_radius=18,
        bgcolor=APP_COLORS["search"],
        border=border_all(APP_COLORS["stroke2"]),
        padding=ft.Padding(left=14, top=2, right=12, bottom=2),
        content=ft.Row(
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(ft.Icons.SEARCH, size=ts(28) if desktop else 25, color=APP_COLORS["blue"]),
                search_field,
            ],
        ),
    )

    action = primary_button(
        "Найти план" if desktop else "",
        icon=None if desktop else ft.Icons.ARROW_FORWARD,
        on_click=lambda _: _run_home_search(search_field, run_search, go_to),
        width=150 if desktop else 52,
        height=52,
    )
    if not desktop:
        field.expand = False
        field.width = 248
        return app_card(
            ft.Row(spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[field, action]),
            padding=12,
            bgcolor=APP_COLORS["surface"],
        )
    return app_card(
        ft.Row(
            spacing=14,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                icon_circle(ft.Icons.QUESTION_ANSWER_OUTLINED, color=APP_COLORS["blue"], bgcolor=APP_COLORS["active"], size=44)
                if desktop
                else ft.Container(width=0),
                ft.Column(
                    spacing=2,
                    expand=True,
                    controls=[
                        ft.Text("Что случилось?", size=ts(18) if desktop else 16, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                        ft.Text("Например: паспорт, ЖКХ, налог, пособие", size=ts(13), color=APP_COLORS["muted"]),
                    ],
                )
                if desktop
                else field,
                field if desktop else action,
                action if desktop else ft.Container(width=0),
            ],
        ),
        padding=18 if desktop else 12,
        bgcolor=APP_COLORS["surface"],
    )


def _quick_action(title: str, value: str, icon, route: str, go_to, desktop: bool) -> ft.Container:
    return ft.Container(
        expand=not desktop,
        ink=True,
        on_click=lambda _: go_to(route),
        border_radius=APP_RADIUS["card"],
        content=app_card(
            ft.Column(
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    icon_circle(icon, color=APP_COLORS["blue"], bgcolor=APP_COLORS["active"], size=42),
                    ft.Text(value, size=ts(20), weight=ft.FontWeight.W_900, color=APP_COLORS["blue"]),
                    ft.Text(title, size=ts(12), weight=ft.FontWeight.W_800, color=APP_COLORS["text"], text_align=ft.TextAlign.CENTER),
                ],
            ),
            padding=14,
            height=108 if desktop else 96,
        ),
    )


def _stat_card(label: str, value: str, tone: str, icon) -> ft.Container:
    return app_card(
        ft.Row(
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                icon_circle(icon, color=APP_COLORS[tone], bgcolor=APP_COLORS["active"] if tone == "blue" else APP_COLORS["surface2"], size=42),
                ft.Column(
                    spacing=2,
                    controls=[
                        ft.Text(value, size=ts(28), weight=ft.FontWeight.W_900, color=APP_COLORS[tone]),
                        ft.Text(label, size=ts(13), color=APP_COLORS["muted"], weight=ft.FontWeight.W_600),
                    ],
                ),
            ],
        ),
        padding=16,
    )


def _stats_grid(data: dict, desktop: bool) -> ft.ResponsiveRow:
    active = str(data.get("active_count", 0))
    task_count = str(
        len(data.get("upcoming_tasks", []))
        + len(data.get("overdue_tasks", []))
        + int(data.get("obligations_count", 0))
    )
    docs_count = str(len(data.get("documents_to_prepare", [])) + len(data.get("expiring_documents", [])) + len(data.get("overdue_documents", [])))
    items = [
        ("активные", active, "blue", ft.Icons.TASK_ALT_OUTLINED),
        ("сроков", task_count, "orange", ft.Icons.EVENT_NOTE_OUTLINED),
        ("прогресс", f"{data.get('active_progress', 0)}%", "green", ft.Icons.TRENDING_UP),
        ("документа", docs_count, "purple", ft.Icons.ARTICLE_OUTLINED),
    ]
    return ft.ResponsiveRow(
        columns=12,
        spacing=12,
        run_spacing=12,
        controls=[
            ft.Container(col={"xs": 6, "md": 3} if desktop else {"xs": 6}, content=_stat_card(label, value, tone, icon))
            for label, value, tone, icon in items
        ],
    )


def _quick_actions_grid(data: dict, go_to) -> ft.ResponsiveRow:
    items = [
        ("Сценарий", "+", ft.Icons.ROUTE_OUTLINED, "/scenarios"),
        ("Ситуации", str(data.get("active_count", 0)), ft.Icons.TASK_ALT_OUTLINED, "/situations"),
        ("Документы", str(len(data.get("documents_to_prepare", []))), ft.Icons.ARTICLE_OUTLINED, "/documents"),
        ("ЖКХ", str(len(data.get("utility_events", []))), ft.Icons.HOME_WORK_OUTLINED, "/utility"),
        ("Налоги", str(len(data.get("tax_events", []))), ft.Icons.RECEIPT_LONG_OUTLINED, "/taxes"),
    ]
    return ft.Column(
        spacing=9,
        controls=[
            ft.Container(
                ink=True,
                on_click=lambda _, target=route: go_to(target),
                border_radius=APP_RADIUS["card"],
                content=app_card(
                    ft.Row(
                        spacing=12,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            icon_circle(icon, color=APP_COLORS["blue"], bgcolor=APP_COLORS["active"], size=38),
                            ft.Text(title, size=ts(14), weight=ft.FontWeight.W_800, color=APP_COLORS["text"], expand=True),
                            ft.Text(value, size=ts(18), weight=ft.FontWeight.W_900, color=APP_COLORS["blue"]),
                        ],
                    ),
                    padding=12,
                ),
            )
            for title, value, icon, route in items
        ],
    )


def _active_actions_card(data: dict, go_to, desktop: bool) -> ft.Container:
    upcoming = data.get("upcoming_tasks", [])[:3]
    count = len(upcoming) + len(data.get("overdue_tasks", []))
    rows: list[ft.Control] = []
    for index, task in enumerate(upcoming, start=1):
        tone = "orange" if index == 1 else "blue"
        rows.append(
            ft.Row(
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    icon_circle(ft.Icons.CIRCLE_OUTLINED, color=APP_COLORS[tone], bgcolor=APP_COLORS["surface2"], size=28),
                    ft.Column(
                        spacing=2,
                        expand=True,
                        controls=[
                            ft.Text(task["title"], size=ts(13), weight=ft.FontWeight.W_800, color=APP_COLORS["text"], max_lines=2),
                            ft.Text(task["due_date_display"], size=ts(12), color=APP_COLORS["muted"]),
                        ],
                    ),
                ],
            )
        )

    if not rows:
        rows.append(ft.Text("Добавьте ситуацию из сценария, и ближайшие действия появятся здесь.", size=ts(13), color=APP_COLORS["muted"]))

    content = ft.Row(
        spacing=18,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Column(
                spacing=10,
                expand=True,
                controls=[
                    badge("сегодня важно", "orange"),
                    ft.Text(f"У вас {count} ближайших действия" if count else "Начните с готового сценария", size=ts(26) if desktop else 23, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                    ft.Text("Документы, заявления и сроки собраны в одном маршруте.", size=ts(14), color=APP_COLORS["muted"]),
                    primary_button("Открыть задачи", on_click=lambda _: go_to("/situations"), width=170 if desktop else None, expand=not desktop, height=44),
                ],
            ),
            ft.Column(spacing=9, width=330, controls=rows) if desktop else ft.Container(width=0),
        ],
    )
    if not desktop:
        content = ft.Column(
            spacing=14,
            controls=[
                ft.Column(
                    spacing=8,
                    controls=[
                        badge("сегодня важно", "orange"),
                        ft.Text(f"{max(count, 0)} ближайших действия" if count else "Начните с готового сценария", size=ts(24), weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                        ft.Text("Документы, заявления и сроки собраны в одном маршруте.", size=ts(13), color=APP_COLORS["muted"]),
                    ],
                ),
                ft.Column(spacing=9, controls=rows),
                primary_button("Открыть", on_click=lambda _: go_to("/situations"), width=130, height=42),
            ],
        )
    return app_card(content, padding=22, bgcolor=APP_COLORS["surface3"])


def _situation_summary_card(item: dict, go_to, desktop: bool) -> ft.Container:
    progress = int(item.get("progress", 0))
    variant = "green" if progress >= 100 else "blue" if progress > 0 else "gray"
    title = item.get("title", "Ситуация")
    return ft.Container(
        ink=True,
        on_click=lambda _: go_to(f"/situation-detail/{item.get('id')}"),
        border_radius=APP_RADIUS["card"],
        content=app_card(
            ft.Row(
                spacing=13,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    icon_circle(ft.Icons.ROUTE_OUTLINED, color=APP_COLORS["blue"], bgcolor=APP_COLORS["active"], size=45),
                    ft.Column(
                        spacing=7,
                        expand=True,
                        controls=[
                            ft.Row(
                                spacing=8,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Text(title, size=ts(16) if desktop else 15, weight=ft.FontWeight.W_900, color=APP_COLORS["text"], expand=True, max_lines=1),
                                    badge(f"{progress}%", variant),
                                ],
                            ),
                            ft.Text(f"{item.get('completed_tasks', 0)} из {item.get('total_tasks', 0)} задач", size=ts(12), color=APP_COLORS["muted"]),
                            ft.ProgressBar(value=progress / 100, bar_height=6, border_radius=10, color=APP_COLORS["blue"], bgcolor=APP_COLORS["stroke2"]),
                        ],
                    ),
                ],
            ),
            padding=14,
        ),
    )


def _situations_section(data: dict, go_to, desktop: bool) -> ft.Control:
    situations = data.get("situations", [])
    controls = [_situation_summary_card(item, go_to, desktop) for item in situations]
    if not controls:
        controls = [
            _empty_state(
                "У вас пока нет активных ситуаций",
                "Выберите жизненный сценарий, чтобы начать путь с готовым планом.",
                "Выбрать сценарий",
                lambda _: go_to("/scenarios"),
            )
        ]
    header = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            section_title("Мои ситуации"),
            ghost_button("Все", on_click=lambda _: go_to("/situations"), width=82, height=40) if desktop else ft.Container(width=0),
        ],
    )
    return ft.Column(spacing=12, controls=[header, ft.Column(spacing=12, controls=controls)])


def _task_row(task: dict, go_to, overdue: bool = False) -> ft.Container:
    color_key = "red" if overdue else "blue"
    return ft.Container(
        ink=True,
        on_click=lambda _: go_to(f"/situation-detail/{task.get('situation_id')}"),
        border_radius=APP_RADIUS["button"],
        content=ft.Row(
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                icon_circle(ft.Icons.CIRCLE_OUTLINED, color=APP_COLORS[color_key], bgcolor=APP_COLORS["surface2"], size=30),
                ft.Column(
                    spacing=3,
                    expand=True,
                    controls=[
                        ft.Text(task.get("title", "Задача"), size=ts(14), weight=ft.FontWeight.W_800, color=APP_COLORS["text"], max_lines=2),
                        ft.Text(f"{task.get('due_date_display', 'Без срока')} · {task.get('situation_title', 'ситуация')}", size=ts(12), color=APP_COLORS["muted"], max_lines=1),
                    ],
                ),
            ],
        ),
    )


def _tasks_section(data: dict, go_to, desktop: bool) -> ft.Control:
    upcoming = data.get("upcoming_tasks", [])
    overdue = data.get("overdue_tasks", [])
    rows = [_task_row(task, go_to) for task in upcoming[:4]]
    if overdue:
        rows = [_task_row(task, go_to, overdue=True) for task in overdue[:2]] + rows
    if not rows:
        rows = [
            ft.Text(
                "Ближайших задач пока нет. Они появятся после создания ситуации и добавления сроков.",
                size=ts(13),
                color=APP_COLORS["muted"],
            )
        ]
    return app_card(
        ft.Column(
            spacing=14,
            controls=[
                section_title("Ближайшие задачи"),
                ft.Column(spacing=12, controls=rows),
                ghost_button("Открыть календарь", on_click=lambda _: go_to("/situations"), expand=True, height=42),
            ],
        ),
        padding=18,
    )


def _category_card(category: dict, open_category, go_to) -> ft.Container:
    route = lambda _: open_category(category["id"]) if open_category else go_to("/problems")
    return ft.Container(
        ink=True,
        on_click=route,
        border_radius=APP_RADIUS["card"],
        content=app_card(
            ft.Row(
                spacing=14,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    icon_circle(_icon(category["icon"]), color=APP_COLORS["blue"], bgcolor=APP_COLORS["active"], size=52),
                    ft.Column(
                        spacing=3,
                        expand=True,
                        controls=[
                            ft.Text(category["name"], size=ts(18), weight=ft.FontWeight.W_900, color=APP_COLORS["text"], max_lines=1),
                            ft.Text(_category_subtitle(category["id"]), size=ts(13), color=APP_COLORS["muted"], max_lines=1),
                        ],
                    ),
                ],
            ),
            padding=16,
            animate=True,
        ),
    )


def _category_subtitle(category_id: str) -> str:
    subtitles = {
        "docs": "паспорт, ID, справки",
        "home": "счета, лифт, оплата",
        "taxes": "оплата, начисления",
        "family": "дети, пособия, брак",
        "work": "труд, увольнение",
        "health": "медкнижка, больничный",
        "auto": "права, регистрация",
        "business": "ИП, налоги",
    }
    return subtitles.get(category_id, "полезные инструкции")


def _category_section(open_category, go_to, desktop: bool) -> ft.Control:
    grid = ft.ResponsiveRow(
        columns=12,
        spacing=14,
        run_spacing=14,
        controls=[
            ft.Container(col={"xs": 12, "sm": 6} if desktop else {"xs": 6}, content=_category_card(category, open_category, go_to))
            for category in CATEGORIES[1:7]
        ],
    )
    return ft.Column(spacing=14, controls=[section_title("Категории проблем"), grid])


def _problem_row(problem: dict, index: int, open_problem) -> ft.Container:
    return ft.Container(
        ink=True,
        on_click=lambda _: open_problem(problem["id"]),
        border_radius=APP_RADIUS["button"],
        content=ft.Row(
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                icon_circle(ft.Icons.LOOKS_ONE_OUTLINED if index == 1 else ft.Icons.ARTICLE_OUTLINED, color=APP_COLORS["blue"], bgcolor=APP_COLORS["active"], size=34),
                ft.Column(
                    spacing=3,
                    expand=True,
                    controls=[
                        ft.Text(problem["title"], size=ts(14), weight=ft.FontWeight.W_900, color=APP_COLORS["text"], max_lines=1),
                        ft.Text(problem.get("description", ""), size=ts(12), color=APP_COLORS["muted"], max_lines=1),
                    ],
                ),
                ft.Icon(ft.Icons.CHEVRON_RIGHT, size=ts(18), color=APP_COLORS["muted2"]),
            ],
        ),
    )


def _popular_problems_section(open_problem, go_to, desktop: bool) -> ft.Control:
    if desktop:
        rows = [_problem_row(problem, index, open_problem) for index, problem in enumerate(PROBLEMS[:4], start=1)]
        return app_card(
            ft.Column(
                spacing=14,
                controls=[
                    section_title("Популярные проблемы"),
                    ft.Column(spacing=12, controls=rows),
                    ghost_button("Смотреть все проблемы", on_click=lambda _: go_to("/problems"), width=220),
                ],
            ),
            padding=18,
        )
    cards = []
    for problem in PROBLEMS[:4]:
        cards.append(
            ft.Container(
                ink=True,
                on_click=lambda _, pid=problem["id"]: open_problem(pid),
                border_radius=APP_RADIUS["card"],
                content=app_card(
                    ft.Column(
                        spacing=8,
                        controls=[
                            ft.Text(problem["title"], size=ts(18), weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                            ft.Text(problem.get("description", ""), size=ts(13), color=APP_COLORS["muted"], max_lines=2),
                        ],
                    ),
                    padding=18,
                ),
            )
        )
    return ft.Column(
        spacing=14,
        controls=[
            section_title("Популярные проблемы"),
            ft.Column(spacing=12, controls=cards),
            secondary_button("Смотреть все проблемы", on_click=lambda _: go_to("/problems"), expand=True),
        ],
    )


def _documents_panel(data: dict, go_to) -> ft.Container:
    docs = data.get("documents_to_prepare", [])[:3]
    expiring = data.get("expiring_documents", [])[:2]
    overdue = data.get("overdue_documents", [])[:2]
    rows: list[ft.Control] = []
    for document in docs:
        rows.append(
            ft.Row(
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    icon_circle(ft.Icons.DESCRIPTION_OUTLINED, color=APP_COLORS["blue"], bgcolor=APP_COLORS["active"], size=36),
                    ft.Column(
                        spacing=3,
                        expand=True,
                        controls=[
                            ft.Text(document["title"], size=ts(14), weight=ft.FontWeight.W_800, color=APP_COLORS["text"], max_lines=1),
                            ft.Text(f"Для: {document['situation_title']}", size=ts(12), color=APP_COLORS["muted"], max_lines=1),
                        ],
                    ),
                    badge("обяз." if document["required"] else "опц.", "green" if document["required"] else "gray"),
                ],
            )
        )
    for document in expiring:
        rows.append(
            ft.Row(
                spacing=10,
                controls=[
                    icon_circle(ft.Icons.SCHEDULE_OUTLINED, color=APP_COLORS["orange"], bgcolor=APP_COLORS["surface2"], size=36),
                    ft.Column(
                        spacing=3,
                        expand=True,
                        controls=[
                            ft.Text(document["title"], size=ts(14), weight=ft.FontWeight.W_800, color=APP_COLORS["text"], max_lines=1),
                            ft.Text(f"до {document['expiry_date']} · {document['days_left']} дн.", size=ts(12), color=APP_COLORS["orange"]),
                        ],
                    ),
                ],
            )
        )
    for document in overdue:
        rows.append(
            ft.Row(
                spacing=10,
                controls=[
                    icon_circle(ft.Icons.ERROR_OUTLINE, color=APP_COLORS["red"], bgcolor=APP_COLORS["surface2"], size=36),
                    ft.Column(
                        spacing=3,
                        expand=True,
                        controls=[
                            ft.Text(document["title"], size=ts(14), weight=ft.FontWeight.W_800, color=APP_COLORS["text"], max_lines=1),
                            ft.Text(f"Просрочен · {document['expiry_date']}", size=ts(12), color=APP_COLORS["red"]),
                        ],
                    ),
                ],
            )
        )
    if not rows:
        rows = [ft.Text("Документы появятся после создания ситуации или добавления личных документов.", size=ts(13), color=APP_COLORS["muted"])]
    return app_card(
        ft.Column(
            spacing=14,
            controls=[
                section_title("Документы и напоминания"),
                ft.Column(spacing=13, controls=rows),
                ghost_button("Управлять документами", on_click=lambda _: go_to("/documents"), expand=True, height=42),
            ],
        ),
        padding=18,
    )


def _amount_text(amount) -> str:
    try:
        value = float(amount or 0)
    except (TypeError, ValueError):
        value = 0
    if value <= 0:
        return "сумма не указана"
    return f"{value:.2f}".replace(".", ",") + " руб."


def _obligation_row(item: dict, go_to) -> ft.Container:
    overdue = item.get("status") == "Просрочено"
    kind = item.get("kind")
    color_key = "red" if overdue else "orange"
    icon = ft.Icons.HOME_WORK_OUTLINED if kind == "utility" else ft.Icons.RECEIPT_LONG_OUTLINED
    if item.get("days_left", 0) < 0:
        due_label = "Просрочено на " + str(abs(int(item.get("days_left", 0)))) + " дн."
    elif item.get("days_left") == 0:
        due_label = "Сегодня"
    else:
        due_label = "Через " + str(item.get("days_left", 0)) + " дн."
    return ft.Container(
        ink=True,
        on_click=lambda _: go_to(item.get("route", "/")),
        border_radius=APP_RADIUS["button"],
        padding=padding_symmetric(horizontal=4, vertical=2),
        content=ft.Row(
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                icon_circle(icon, color=APP_COLORS[color_key], bgcolor=APP_COLORS["surface2"], size=36),
                ft.Column(
                    spacing=4,
                    expand=True,
                    controls=[
                        ft.Row(
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Text(item.get("title", "Срок"), size=ts(14), weight=ft.FontWeight.W_900, color=APP_COLORS["text"], expand=True, max_lines=2),
                                badge("проср." if overdue else "срок", "red" if overdue else "orange"),
                            ],
                        ),
                        ft.Text(f"{item.get('subtitle', '')} · {due_label}", size=ts(12), color=APP_COLORS[color_key] if overdue else APP_COLORS["muted"], max_lines=1),
                        ft.Text(_amount_text(item.get("amount")), size=ts(12), color=APP_COLORS["muted2"], max_lines=1),
                    ],
                ),
            ],
        ),
    )


def _obligations_panel(data: dict, go_to, desktop: bool) -> ft.Container:
    overdue = data.get("overdue_obligations", [])
    upcoming = data.get("upcoming_obligations", [])
    rows = [_obligation_row(item, go_to) for item in overdue[:3]]
    rows.extend(_obligation_row(item, go_to) for item in upcoming[:3])
    if not rows:
        rows = [
            ft.Text(
                "Ближайших сроков по ЖКХ и налогам нет. Добавьте лицевой счёт или налоговое обязательство, чтобы видеть их здесь.",
                size=ts(13),
                color=APP_COLORS["muted"],
            )
        ]
    return app_card(
        ft.Column(
            spacing=14,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        section_title("ЖКХ и налоги"),
                        badge(str(data.get("obligations_count", 0)), "orange") if desktop else ft.Container(width=0),
                    ],
                ),
                ft.Text("Платежи, показания и налоговые сроки из локальных трекеров.", size=ts(13), color=APP_COLORS["muted"]),
                ft.Column(spacing=12, controls=rows),
                ft.Row(
                    spacing=10,
                    controls=[
                        ghost_button("ЖКХ", icon=ft.Icons.HOME_WORK_OUTLINED, on_click=lambda _: go_to("/utility"), expand=True, height=42),
                        ghost_button("Налоги", icon=ft.Icons.RECEIPT_LONG_OUTLINED, on_click=lambda _: go_to("/taxes"), expand=True, height=42),
                    ],
                ),
            ],
        ),
        padding=18,
    )


def _law_updates_panel(go_to, desktop: bool) -> ft.Container:
    rows: list[ft.Control] = []
    for law in LEGAL_UPDATES[:3]:
        priority = "red" if law.get("priority") == "high" else "orange" if law.get("priority") == "medium" else "cyan"
        rows.append(
            ft.Container(
                ink=True,
                on_click=lambda _, lid=law["id"]: go_to(f"/legal-updates/{lid}"),
                border_radius=APP_RADIUS["button"],
                content=ft.Column(
                    spacing=7,
                    controls=[
                        ft.Row(spacing=8, controls=[badge(law.get("category_name", "Закон"), "cyan"), badge("важно для вас", priority)]),
                        ft.Text(law["title"], size=ts(16), weight=ft.FontWeight.W_900, color=APP_COLORS["text"], max_lines=2),
                        ft.Text(law.get("short", ""), size=ts(13), color=APP_COLORS["muted"], max_lines=2),
                        ghost_button("Открыть обзор", icon=ft.Icons.ARROW_FORWARD, on_click=lambda _, lid=law["id"]: go_to(f"/legal-updates/{lid}"), width=170 if desktop else None),
                    ],
                ),
            )
        )
    return app_card(ft.Column(spacing=14, controls=[section_title("Закон-апдейт"), *rows]), padding=18)


def _reminders_panel(go_to, desktop: bool, notifications: list[dict] | None = None) -> ft.Container:
    reminders = (notifications if notifications is not None else NOTIFICATIONS)[:4]
    rows: list[ft.Control] = []
    for notification in reminders:
        unread = not notification.get("read", False)
        rows.append(
            ft.Row(
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    icon_circle(_notification_icon(notification.get("type", "")), color=APP_COLORS["blue"] if unread else APP_COLORS["muted2"], bgcolor=APP_COLORS["active"] if unread else APP_COLORS["surface2"], size=36),
                    ft.Column(
                        spacing=3,
                        expand=True,
                        controls=[
                            ft.Text(notification.get("title", "Уведомление"), size=ts(14), weight=ft.FontWeight.W_800, color=APP_COLORS["text"], max_lines=1),
                            ft.Text(notification.get("desc", ""), size=ts(12), color=APP_COLORS["muted"], max_lines=2),
                        ],
                    ),
                ],
            )
        )
    if not rows:
        rows = [ft.Text("Новых напоминаний нет.", size=ts(13), color=APP_COLORS["muted"])]
    return app_card(
        ft.Column(
            spacing=14,
            controls=[
                section_title("Напоминания"),
                ft.Column(spacing=13, controls=rows),
                ghost_button("Все напоминания", on_click=lambda _: go_to("/notifications"), expand=True, height=42),
            ],
        ),
        padding=18,
    )


def _scenario_start_card(go_to, desktop: bool) -> ft.Container:
    scenario = next((item for item in SCENARIO_TEMPLATES if item.get("id") == "childbirth"), SCENARIO_TEMPLATES[0])
    return app_card(
        ft.Row(
            spacing=14,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                icon_circle(ft.Icons.ROUTE_OUTLINED, color=APP_COLORS["blue"], bgcolor=APP_COLORS["active"], size=48),
                ft.Column(
                    spacing=4,
                    expand=True,
                    controls=[
                        badge("популярный", "purple"),
                        ft.Text(scenario["title"], size=ts(18), weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                        ft.Text("Начните с него: создайте личную ситуацию и отметьте несколько задач.", size=ts(13), color=APP_COLORS["muted"], max_lines=2),
                    ],
                ),
                primary_button("Начать", on_click=lambda _: go_to(f"/scenarios/{scenario['id']}"), width=110 if desktop else None),
            ],
        ),
        padding=18,
        bgcolor=APP_COLORS["surface3"],
    )


def _chip_control(category: dict, selected: bool, open_category, go_to) -> ft.Container:
    return category_chip(
        category["name"],
        selected=selected,
        on_click=lambda _, category_id=category["id"]: open_category(category_id) if open_category else go_to("/problems"),
    )


def _chips_row(open_category, go_to, desktop: bool) -> ft.Control:
    chips = []
    for index, category in enumerate(CATEGORIES[1:7]):
        chips.append(_chip_control(category, index == 0, open_category, go_to))
    if desktop:
        return ft.Row(spacing=10, wrap=True, controls=chips)
    return ft.Column(
        spacing=8,
        controls=[
            ft.Row(spacing=8, controls=chips[:3]),
            ft.Row(spacing=8, controls=chips[3:]),
        ],
    )


def _desktop_home(
    open_problem,
    go_to,
    run_search=None,
    open_category=None,
    user: dict | None = None,
    dashboard: dict | None = None,
    notifications: list[dict] | None = None,
) -> ft.Control:
    data = dashboard or {}
    profile = user or MOCK_USER
    today = date.today().strftime("%d.%m.%Y")
    _fn = profile.get("first_name", "пользователь")
    first_name = _fn
    greeting = f"Добрый день, {_fn}" if _fn else "Добрый день"
    search_field = ft.TextField(
        hint_text="паспорт, ЖКХ, налог...",
        expand=True,
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color=ft.Colors.TRANSPARENT,
        cursor_color=APP_COLORS["blue"],
        color=APP_COLORS["text"],
        text_size=15,
        hint_style=ft.TextStyle(color=APP_COLORS["muted2"]),
        on_submit=lambda _: _run_home_search(search_field, run_search, go_to),
    )

    # Hero banner
    hero_banner = ft.Container(
        border_radius=APP_RADIUS["hero"],
        padding=ft.Padding(left=32, top=28, right=32, bottom=28),
        gradient=ft.LinearGradient(
            begin=ft.Alignment(-1, -1),
            end=ft.Alignment(1, 1),
            colors=GRADIENT_FUTUREWAFE,
        ),
        content=ft.Row(
            spacing=24,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Column(
                    spacing=8,
                    expand=True,
                    controls=[
                        ft.Container(
                            content=ft.Text(
                                greeting,
                                size=ts(13),
                                weight=ft.FontWeight.W_600,
                                color=ft.Colors.with_opacity(0.8, ft.Colors.WHITE),
                            ),
                            padding=ft.Padding(left=14, top=5, right=14, bottom=5),
                            border_radius=20,
                            bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.WHITE),
                        ),
                        ft.Text(
                            "Личный цифровой\nпомощник гражданина.",
                            size=ts(34),
                            weight=ft.FontWeight.W_900,
                            color=ft.Colors.WHITE,
                            height=None,
                        ),
                        ft.Text(
                            "Опишите ситуацию — Белпомощник разберёт её по шагам,\nподскажет документы и куда обратиться.",
                            size=ts(14),
                            color=ft.Colors.with_opacity(0.8, ft.Colors.WHITE),
                        ),
                        ft.Container(height=4),
                        ft.Container(
                            expand=False,
                            border_radius=16,
                            bgcolor=APP_COLORS["search"],
                            border=border_all(ft.Colors.with_opacity(0.3, ft.Colors.WHITE)),
                            padding=ft.Padding(left=14, top=2, right=10, bottom=2),
                            content=ft.Row(
                                spacing=10,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Icon(ft.Icons.SEARCH, size=ts(22), color=APP_COLORS["blue"]),
                                    search_field,
                                    ft.Container(
                                        ink=True,
                                        border_radius=12,
                                        padding=ft.Padding(left=16, top=10, right=16, bottom=10),
                                        bgcolor=APP_COLORS["blue"],
                                        on_click=lambda _: _run_home_search(search_field, run_search, go_to),
                                        content=ft.Row(
                                            spacing=6,
                                            controls=[
                                                ft.Icon(ft.Icons.AUTO_AWESOME_OUTLINED, size=ts(16), color=ft.Colors.WHITE),
                                                ft.Text("Подсказать", size=ts(14), weight=ft.FontWeight.W_700, color=ft.Colors.WHITE),
                                            ],
                                        ),
                                    ),
                                ],
                            ),
                        ),
                    ],
                ),
            ],
        ),
    )

    left = ft.Column(
        expand=True,
        spacing=24,
        controls=[
            hero_banner,
            _chips_row(open_category, go_to, True),
            _active_actions_card(data, go_to, True),
            _stats_grid(data, True),
            ft.Row(
                spacing=24,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    ft.Container(expand=True, content=_situations_section(data, go_to, True)),
                    ft.Container(width=340, content=_tasks_section(data, go_to, True)),
                ],
            ),
            _category_section(open_category, go_to, True),
            ft.Row(
                spacing=24,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    ft.Container(expand=True, content=_popular_problems_section(open_problem, go_to, True)),
                    ft.Container(
                        width=340,
                        content=ft.Column(
                            spacing=18,
                            controls=[
                                _documents_panel(data, go_to),
                                _obligations_panel(data, go_to, True),
                            ],
                        ),
                    ),
                ],
            ),
            _scenario_start_card(go_to, True),
        ],
    )
    right = ft.Container(
        width=320,
        content=ft.Column(
            spacing=18,
            controls=[
                _demo_tip(f"Сегодня {today}."),
                _reminders_panel(go_to, True, notifications),
                _law_updates_panel(go_to, True),
            ],
        ),
    )

    return desktop_content(
        ft.Row(spacing=24, vertical_alignment=ft.CrossAxisAlignment.START, controls=[left, right]),
        width=1180,
        top=32,
        bottom=60,
    )


def _mobile_home(
    open_problem,
    go_to,
    run_search=None,
    open_category=None,
    user: dict | None = None,
    dashboard: dict | None = None,
    notifications: list[dict] | None = None,
) -> ft.Control:
    data = dashboard or {}
    profile = user or MOCK_USER
    _fn = profile.get("first_name", "Иван")
    first_name = _fn
    greeting = f"Привет, {_fn}!" if _fn else "Добро пожаловать!"
    search_field = ft.TextField(
        hint_text="паспорт, ЖКХ, налог...",
        expand=True,
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color=ft.Colors.TRANSPARENT,
        cursor_color=APP_COLORS["blue"],
        color=APP_COLORS["text"],
        text_size=14,
        hint_style=ft.TextStyle(color=APP_COLORS["muted2"]),
        on_submit=lambda _: _run_home_search(search_field, run_search, go_to),
    )

    # Mobile hero banner
    mobile_hero = ft.Container(
        border_radius=APP_RADIUS["hero"],
        padding=ft.Padding(left=20, top=20, right=20, bottom=20),
        gradient=ft.LinearGradient(
            begin=ft.Alignment(-1, -1),
            end=ft.Alignment(1, 1),
            colors=GRADIENT_FUTUREWAFE,
        ),
        content=ft.Column(
            spacing=10,
            controls=[
                ft.Container(
                    content=ft.Text(
                        greeting,
                        size=ts(12),
                        weight=ft.FontWeight.W_600,
                        color=ft.Colors.with_opacity(0.8, ft.Colors.WHITE),
                    ),
                    padding=ft.Padding(left=12, top=4, right=12, bottom=4),
                    border_radius=20,
                    bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.WHITE),
                ),
                ft.Text(
                    "Личный цифровой\nпомощник гражданина.",
                    size=ts(26),
                    weight=ft.FontWeight.W_900,
                    color=ft.Colors.WHITE,
                ),
                ft.Text(
                    "Опишите ситуацию — получите пошаговый план действий.",
                    size=ts(13),
                    color=ft.Colors.with_opacity(0.8, ft.Colors.WHITE),
                ),
                ft.Container(
                    border_radius=14,
                    bgcolor=APP_COLORS["search"],
                    padding=ft.Padding(left=12, top=4, right=8, bottom=4),
                    content=ft.Row(
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(ft.Icons.SEARCH, size=ts(20), color=APP_COLORS["blue"]),
                            search_field,
                            ft.Container(
                                ink=True,
                                border_radius=10,
                                padding=ft.Padding(left=12, top=8, right=12, bottom=8),
                                bgcolor=APP_COLORS["blue"],
                                on_click=lambda _: _run_home_search(search_field, run_search, go_to),
                                content=ft.Icon(ft.Icons.ARROW_FORWARD, size=ts(16), color=ft.Colors.WHITE),
                            ),
                        ],
                    ),
                ),
            ],
        ),
    )

    content = ft.Column(
        spacing=20,
        controls=[
            mobile_hero,
            _quick_actions_grid(data, go_to),
            _chips_row(open_category, go_to, False),
            _active_actions_card(data, go_to, False),
            section_title("Статистика"),
            _stats_grid(data, False),
            _situations_section(data, go_to, False),
            _tasks_section(data, go_to, False),
            _obligations_panel(data, go_to, False),
            _documents_panel(data, go_to),
            _law_updates_panel(go_to, False),
            _category_section(open_category, go_to, False),
            _popular_problems_section(open_problem, go_to, False),
            _reminders_panel(go_to, False, notifications),
            _scenario_start_card(go_to, False),
        ],
    )
    return content


def _tablet_home(
    open_problem,
    go_to,
    run_search=None,
    open_category=None,
    user: dict | None = None,
    dashboard: dict | None = None,
    notifications: list[dict] | None = None,
) -> ft.Control:
    """Single-column wide layout for tablet (sidebar handles left rail)."""
    data = dashboard or {}
    profile = user or MOCK_USER
    _fn = profile.get("first_name", "пользователь")
    first_name = _fn
    greeting = f"Добрый день, {_fn}" if _fn else "Добрый день"
    search_field = ft.TextField(
        hint_text="паспорт, ЖКХ, налог...",
        expand=True,
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color=ft.Colors.TRANSPARENT,
        cursor_color=APP_COLORS["blue"],
        color=APP_COLORS["text"],
        text_size=15,
        hint_style=ft.TextStyle(color=APP_COLORS["muted2"]),
        on_submit=lambda _: _run_home_search(search_field, run_search, go_to),
    )

    hero = ft.Container(
        border_radius=APP_RADIUS["hero"],
        padding=ft.Padding(left=28, top=22, right=28, bottom=22),
        gradient=ft.LinearGradient(
            begin=ft.Alignment(-1, -1),
            end=ft.Alignment(1, 1),
            colors=GRADIENT_FUTUREWAFE,
        ),
        content=ft.Column(
            spacing=10,
            controls=[
                ft.Container(
                    content=ft.Text(
                        greeting,
                        size=ts(12),
                        weight=ft.FontWeight.W_600,
                        color=ft.Colors.with_opacity(0.8, ft.Colors.WHITE),
                    ),
                    padding=ft.Padding(left=12, top=4, right=12, bottom=4),
                    border_radius=20,
                    bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.WHITE),
                ),
                ft.Text("Личный цифровой помощник гражданина.", size=ts(26), weight=ft.FontWeight.W_900, color=ft.Colors.WHITE),
                ft.Text(
                    "Опишите ситуацию — получите пошаговый план действий и список документов.",
                    size=ts(13),
                    color=ft.Colors.with_opacity(0.8, ft.Colors.WHITE),
                ),
                ft.Container(
                    border_radius=14,
                    bgcolor=APP_COLORS["search"],
                    padding=ft.Padding(left=14, top=4, right=8, bottom=4),
                    content=ft.Row(
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(ft.Icons.SEARCH, size=ts(22), color=APP_COLORS["blue"]),
                            search_field,
                            ft.Container(
                                ink=True,
                                border_radius=12,
                                padding=ft.Padding(left=14, top=9, right=14, bottom=9),
                                bgcolor=APP_COLORS["blue"],
                                on_click=lambda _: _run_home_search(search_field, run_search, go_to),
                                content=ft.Row(spacing=6, controls=[
                                    ft.Icon(ft.Icons.AUTO_AWESOME_OUTLINED, size=ts(16), color=ft.Colors.WHITE),
                                    ft.Text("Подсказать", size=ts(13), weight=ft.FontWeight.W_700, color=ft.Colors.WHITE),
                                ]),
                            ),
                        ],
                    ),
                ),
            ],
        ),
    )

    return ft.Container(
        expand=True,
        padding=ft.Padding(left=20, top=20, right=20, bottom=32),
        content=ft.Column(
            spacing=20,
            controls=[
                hero,
                _chips_row(open_category, go_to, True),
                _active_actions_card(data, go_to, True),
                _stats_grid(data, True),
                ft.Row(
                    spacing=20,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    controls=[
                        ft.Container(expand=True, content=_situations_section(data, go_to, True)),
                        ft.Container(width=280, content=_tasks_section(data, go_to, True)),
                    ],
                ),
                _obligations_panel(data, go_to, True),
                _category_section(open_category, go_to, True),
                _popular_problems_section(open_problem, go_to, True),
                _documents_panel(data, go_to),
                _reminders_panel(go_to, True, notifications),
                _law_updates_panel(go_to, True),
                _scenario_start_card(go_to, True),
            ],
        ),
    )


def build_home_page(
    open_problem,
    go_to,
    is_desktop: bool = False,
    run_search=None,
    open_category=None,
    user: dict | None = None,
    dashboard: dict | None = None,
    notifications: list[dict] | None = None,
    is_tablet: bool = False,
) -> ft.Control:
    if is_desktop and not is_tablet:
        return _desktop_home(open_problem, go_to, run_search, open_category, user, dashboard, notifications)
    if is_tablet:
        return _tablet_home(open_problem, go_to, run_search, open_category, user, dashboard, notifications)
    return _mobile_home(open_problem, go_to, run_search, open_category, user, dashboard, notifications)
