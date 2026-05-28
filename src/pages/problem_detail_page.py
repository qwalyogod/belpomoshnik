from __future__ import annotations

import flet as ft

from components.buttons import ghost_button, primary_button, secondary_button
from components.cards import app_card, badge, hero_card, hint_card, icon_circle, info_card, stat_card
from components.layout import desktop_content
from components.placeholders import photo_placeholder
from data.mock_data import CONTENT_DISCLAIMER, LEARNING_QUESTIONS, OFFICIAL_SOURCES, PROBLEM_DETAIL, PROBLEMS
from theme.app_theme import APP_COLORS, CENTER, RADIUS, SPACING, border_all, get_badge_palette, padding_symmetric


CATEGORY_TONES = {
    "docs": "blue",
    "home": "cyan",
    "taxes": "orange",
    "family": "green",
    "work": "purple",
    "health": "red",
    "auto": "cyan",
    "business": "purple",
}

SOURCE_IDS_BY_CATEGORY = {
    "docs": ["source-mvd", "source-portal-gov", "source-pravo", "source-minjust"],
    "taxes": ["source-nalog", "source-pravo", "source-portal-gov"],
    "family": ["source-minjust", "source-mintrud", "source-pravo"],
    "home": ["source-portal-gov", "source-pravo"],
    "business": ["source-nalog", "source-portal-gov", "source-pravo"],
    "health": ["source-portal-gov", "source-pravo"],
}

TIME_BY_PROBLEM = {
    "lost-passport": "15-30 дней",
    "med-book": "1-7 дней",
    "no-utility-bill": "1 день",
    "wrong-tax": "до 30 дней",
    "registration-move": "7-30 дней",
    "childbirth": "1-2 месяца",
    "divorce": "1-3 месяца",
    "sick-leave": "3-10 дней",
    "dismissal": "до 14 дней",
    "sole-trader": "1-5 дней",
}


def find_problem(problem_id: str) -> dict:
    base = next((problem for problem in PROBLEMS if problem["id"] == problem_id), PROBLEMS[0]).copy()
    base.update(PROBLEM_DETAIL.get(base["id"], {}))
    return base


def _completed_values(problem: dict, completed_steps: list[bool] | None) -> list[bool]:
    steps = problem.get("steps", [])
    values = list(completed_steps or [])
    if len(values) < len(steps):
        values.extend([False] * (len(steps) - len(values)))
    return values[: len(steps)]


def _progress_percent(values: list[bool]) -> int:
    if not values:
        return 0
    done = len([value for value in values if value])
    return round(done / len(values) * 100)


def _tone_colors(tone: str) -> tuple[str, str]:
    palette = get_badge_palette()
    return palette.get(tone, palette["blue"])


def _category_tone(problem: dict) -> str:
    return CATEGORY_TONES.get(problem.get("category", ""), "blue")


def _difficulty(problem: dict) -> tuple[str, str]:
    urgency = str(problem.get("urgency", "")).lower()
    steps_count = len(problem.get("steps", []))
    if "сроч" in urgency or steps_count > 7:
        return "Высокая сложность", "red"
    if "важ" in urgency or steps_count >= 5:
        return "Средняя сложность", "orange"
    return "Легкая сложность", "green"


def _problem_time(problem: dict) -> str:
    return problem.get("estimated_duration") or TIME_BY_PROBLEM.get(problem.get("id"), "срок уточняется")


def _cost_summary(problem: dict) -> str:
    cost = problem.get("cost")
    if isinstance(cost, list) and cost:
        return "госпошлина"
    if isinstance(cost, str) and cost:
        return cost
    return "уточняется"


def _as_list(value) -> list[str]:
    if isinstance(value, list):
        return value
    if isinstance(value, str) and value:
        return [value]
    return []


def _source_items(problem: dict) -> list[dict]:
    source_ids = SOURCE_IDS_BY_CATEGORY.get(problem.get("category", ""), ["source-pravo", "source-portal-gov"])
    source_map = {item["id"]: item for item in OFFICIAL_SOURCES}
    return [source_map[source_id] for source_id in source_ids if source_id in source_map]


def _related_problems(problem: dict) -> list[dict]:
    same_category = [
        item
        for item in PROBLEMS
        if item.get("id") != problem.get("id") and item.get("category") == problem.get("category")
    ]
    fallback = [item for item in PROBLEMS if item.get("id") != problem.get("id")]
    return (same_category + fallback)[:3]


def _flow_wrap(controls: list[ft.Control], spacing: int = 8) -> ft.Row:
    return ft.Row(spacing=spacing, run_spacing=spacing, wrap=True, controls=controls)


def _mobile_badges(problem: dict) -> ft.Column:
    difficulty, difficulty_tone = _difficulty(problem)
    return ft.Column(
        spacing=8,
        controls=[
            ft.Row(
                spacing=8,
                controls=[
                    badge(problem.get("category_name", "Документы"), _category_tone(problem)),
                    badge(difficulty, difficulty_tone),
                ],
            ),
            ft.Row(controls=[badge(_problem_time(problem), "default")]),
        ],
    )


def _section_heading(title: str, icon: str | None = None, tone: str = "blue", size: int = 24) -> ft.Row:
    badge_bg, badge_fg = _tone_colors(tone)
    controls: list[ft.Control] = []
    if icon:
        controls.append(icon_circle(icon, color=badge_fg, bgcolor=badge_bg, size=42))
    controls.append(ft.Text(title, size=size, weight=ft.FontWeight.W_900, color=APP_COLORS["text"], expand=True))
    return ft.Row(spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=controls)


def _breadcrumb(go_back, desktop: bool) -> ft.Container:
    return ft.Container(
        content=ft.Row(
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(ft.Icons.ARROW_BACK, size=19, color=APP_COLORS["blue_text"]),
                ft.Text("Каталог проблем", size=14 if desktop else 13, weight=ft.FontWeight.W_800, color=APP_COLORS["blue_text"]),
            ],
        ),
        padding=padding_symmetric(horizontal=14, vertical=9),
        border_radius=RADIUS["sm"],
        bgcolor=APP_COLORS["surface2"],
        border=border_all(APP_COLORS["stroke2"]),
        on_click=go_back,
        ink=True,
    )


def _hero_action(text: str, icon: str, on_click, primary: bool, width: int) -> ft.Container:
    text_color = ft.Colors.WHITE if primary else APP_COLORS["blue_text"]
    bgcolor = APP_COLORS["blue"] if primary else APP_COLORS["surface"]
    border_color = APP_COLORS["blue"] if primary else APP_COLORS["stroke2"]
    return ft.Container(
        width=width,
        height=48,
        border_radius=RADIUS["sm"],
        bgcolor=bgcolor,
        border=border_all(border_color),
        alignment=CENTER,
        on_click=on_click,
        ink=True,
        content=ft.Row(
            spacing=8,
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(icon, size=18, color=text_color),
                ft.Text(text, size=14, weight=ft.FontWeight.W_900, color=text_color),
            ],
        ),
    )


def _numbered_item(text: str, index: int, tone: str = "orange") -> ft.Row:
    badge_bg, badge_fg = _tone_colors(tone)
    return ft.Row(
        spacing=14,
        vertical_alignment=ft.CrossAxisAlignment.START,
        controls=[
            ft.Container(
                width=28,
                height=28,
                border_radius=14,
                bgcolor=badge_bg,
                alignment=CENTER,
                content=ft.Text(str(index), size=13, weight=ft.FontWeight.W_900, color=badge_fg),
            ),
            ft.Text(text, size=15, color=APP_COLORS["text"], expand=True),
        ],
    )


def _hero(problem: dict, save_problem, create_plan, desktop: bool) -> ft.Container:
    difficulty, difficulty_tone = _difficulty(problem)
    category_tone = _category_tone(problem)
    if not desktop:
        return app_card(
            ft.Column(
                spacing=14,
                controls=[
                    icon_circle(ft.Icons.ROUTE_OUTLINED, color=APP_COLORS["blue_text"], bgcolor=APP_COLORS["active"], size=56),
                    ft.Text("Личный маршрут решения", size=24, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                    ft.Text(
                        "Соберите план, отметьте шаги и держите под рукой документы, сроки и официальные источники.",
                        size=14,
                        color=APP_COLORS["muted"],
                    ),
                    _mobile_badges(problem),
                    primary_button("Создать ситуацию", icon=ft.Icons.ADD_TASK_OUTLINED, on_click=create_plan, expand=True),
                ],
            ),
            padding=22,
            bgcolor=APP_COLORS["surface3"],
            border_color=APP_COLORS["stroke2"],
        )

    actions: list[ft.Control]
    actions = [
        _hero_action("Создать ситуацию", ft.Icons.ADD_TASK_OUTLINED, create_plan, True, 220),
        _hero_action("Сохранить", ft.Icons.BOOKMARK_BORDER, save_problem, False, 150),
    ]
    return hero_card(
        "Личный маршрут решения",
        "Соберите план, отметьте шаги и держите под рукой документы, сроки и официальные источники.",
        icon=ft.Icons.ROUTE_OUTLINED,
        badges=[
            badge(problem.get("category_name", "Документы"), category_tone),
            badge(difficulty, difficulty_tone),
            badge(_problem_time(problem), "default"),
        ],
        actions=actions,
    )


def _summary_row(label: str, value: str, icon: str, tone: str = "blue") -> ft.Row:
    badge_bg, badge_fg = _tone_colors(tone)
    return ft.Row(
        spacing=12,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(
                width=38,
                height=38,
                border_radius=19,
                bgcolor=badge_bg,
                alignment=CENTER,
                content=ft.Icon(icon, size=20, color=badge_fg),
            ),
            ft.Column(
                spacing=1,
                expand=True,
                controls=[
                    ft.Text(label, size=12, weight=ft.FontWeight.W_700, color=APP_COLORS["muted"]),
                    ft.Text(value, size=14, weight=ft.FontWeight.W_900, color=APP_COLORS["text"], max_lines=2),
                ],
            ),
        ],
    )


def _summary_card(problem: dict, values: list[bool], save_problem, create_plan) -> ft.Container:
    done = len([value for value in values if value])
    total = len(values)
    rows = [
        _summary_row("Шаги", f"{done} из {total}", ft.Icons.CHECKLIST_RTL_OUTLINED, "green"),
        _summary_row("Срок", _problem_time(problem), ft.Icons.SCHEDULE_OUTLINED, "blue"),
        _summary_row("Документы", str(len(problem.get("documents", []))), ft.Icons.ARTICLE_OUTLINED, "purple"),
        _summary_row("Стоимость", _cost_summary(problem), ft.Icons.PAYMENTS_OUTLINED, "orange"),
    ]
    return app_card(
        ft.Column(
            spacing=16,
            controls=[
                ft.Text("Кратко по плану", size=20, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                ft.Column(spacing=12, controls=rows),
                primary_button("Создать ситуацию", icon=ft.Icons.ADD_TASK_OUTLINED, on_click=create_plan, expand=True),
                secondary_button("Сохранить себе", icon=ft.Icons.BOOKMARK_BORDER, on_click=save_problem, expand=True),
                ghost_button("Скачать шаблон", icon=ft.Icons.DOWNLOAD_OUTLINED, expand=True),
            ],
        ),
        padding=20,
    )


def _immediate_card(problem: dict, desktop: bool) -> ft.Container:
    badge_bg, badge_fg = _tone_colors("orange")
    return app_card(
        ft.Column(
            spacing=18,
            controls=[
                ft.Row(
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        icon_circle(ft.Icons.PRIORITY_HIGH_OUTLINED, color=badge_fg, bgcolor=badge_bg, size=46),
                        ft.Text(
                            "Что делать прямо сейчас",
                            size=24 if desktop else 21,
                            weight=ft.FontWeight.W_900,
                            color=APP_COLORS["text"],
                            expand=True,
                        ),
                    ],
                ),
                ft.Column(
                    spacing=15,
                    controls=[_numbered_item(item, index, "orange") for index, item in enumerate(problem.get("immediate", []), start=1)],
                ),
            ],
        ),
        padding=22 if desktop else 18,
        bgcolor=badge_bg,
        border_color=badge_fg,
    )


def _progress_card(values: list[bool]) -> ft.Container:
    progress = _progress_percent(values)
    done = len([value for value in values if value])
    total = len(values)
    return app_card(
        ft.Column(
            spacing=12,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Column(
                            spacing=2,
                            controls=[
                                ft.Text("Прогресс выполнения", size=15, weight=ft.FontWeight.W_800, color=APP_COLORS["text"]),
                                ft.Text(f"Готово {done} из {total} шагов", size=13, color=APP_COLORS["muted"]),
                            ],
                        ),
                        badge(f"{progress}%", "green" if progress == 100 else "blue"),
                    ],
                ),
                ft.ProgressBar(
                    value=progress / 100,
                    bar_height=9,
                    border_radius=12,
                    color=APP_COLORS["green"] if progress == 100 else APP_COLORS["blue"],
                    bgcolor=APP_COLORS["surface2"],
                ),
            ],
        ),
        padding=18,
    )


def _step_card(step: str, index: int, completed: bool, on_toggle_step, desktop: bool) -> ft.Container:
    badge_bg, badge_fg = _tone_colors("green" if completed else "blue")
    deadline = "Срок уточнить" if index > 1 else "сразу"
    return app_card(
        ft.Row(
            spacing=14,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                ft.Container(
                    width=38,
                    height=38,
                    border_radius=19,
                    bgcolor=badge_bg,
                    alignment=CENTER,
                    content=ft.Text(str(index + 1), size=15, weight=ft.FontWeight.W_900, color=badge_fg),
                ),
                ft.Column(
                    spacing=9,
                    expand=True,
                    controls=[
                        ft.Row(
                            spacing=8,
                            run_spacing=8,
                            wrap=True,
                            controls=[
                                badge(deadline, "green" if completed else "default"),
                                badge("выполнено", "success") if completed else badge("активный шаг", "active"),
                            ],
                        ),
                        ft.Text(
                            step,
                            size=17 if desktop else 16,
                            weight=ft.FontWeight.W_900,
                            color=APP_COLORS["muted2"] if completed else APP_COLORS["text"],
                        ),
                        ft.Text(
                            "Отметьте шаг после выполнения. Прогресс обновится сразу в текущей сессии.",
                            size=13,
                            color=APP_COLORS["muted"],
                        ),
                    ],
                ),
                ft.Checkbox(
                    value=completed,
                    active_color=APP_COLORS["green"],
                    on_change=lambda event, step_index=index: on_toggle_step(step_index, bool(event.control.value))
                    if on_toggle_step
                    else None,
                ),
            ],
        ),
        padding=18 if desktop else 16,
        animate=True,
    )


def _steps_section(problem: dict, values: list[bool], on_toggle_step, desktop: bool) -> ft.Column:
    return ft.Column(
        spacing=14,
        controls=[
            _section_heading("Пошаговый план", ft.Icons.FORMAT_LIST_NUMBERED_RTL_OUTLINED, "blue", 24 if desktop else 21),
            _progress_card(values),
            ft.Column(
                spacing=12,
                controls=[
                    _step_card(step, index, values[index], on_toggle_step, desktop)
                    for index, step in enumerate(problem.get("steps", []))
                ],
            ),
        ],
    )


def _documents_card(problem: dict, compact: bool = False) -> ft.Container:
    documents = problem.get("documents", []) or ["Перечень документов будет уточнен позже."]
    rows: list[ft.Control] = []
    for index, item in enumerate(documents, start=1):
        placeholder = photo_placeholder(f"документ {index}", width=88 if compact else 104, height=58 if compact else 68)
        rows.append(
            ft.Row(
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    placeholder,
                    ft.Column(
                        spacing=5,
                        expand=True,
                        controls=[
                            ft.Text(item, size=14, weight=ft.FontWeight.W_800, color=APP_COLORS["text"]),
                            ft.Text("Обычно требуется оригинал или копия. Уточните перед подачей.", size=12, color=APP_COLORS["muted"]),
                        ],
                    ),
                ],
            )
        )
    return app_card(
        ft.Column(
            spacing=16,
            controls=[
                _section_heading("Документы", ft.Icons.ARTICLE_OUTLINED, "purple", 21),
                ft.Column(spacing=14, controls=rows),
            ],
        ),
        padding=18,
    )


def _terms_cost_grid(problem: dict) -> ft.ResponsiveRow:
    terms = _as_list(problem.get("terms"))
    cost = _as_list(problem.get("cost"))
    return ft.ResponsiveRow(
        columns=12,
        spacing=12,
        run_spacing=12,
        controls=[
            ft.Container(
                col={"xs": 12, "sm": 6},
                content=stat_card(
                    "Срок оформления",
                    _problem_time(problem),
                    terms[0] if terms else "точный срок уточняется",
                    ft.Icons.SCHEDULE_OUTLINED,
                    "blue",
                ),
            ),
            ft.Container(
                col={"xs": 12, "sm": 6},
                content=stat_card(
                    "Стоимость",
                    _cost_summary(problem),
                    cost[0] if cost else "может зависеть от ситуации",
                    ft.Icons.PAYMENTS_OUTLINED,
                    "orange",
                ),
            ),
        ],
    )


def _contacts_card(problem: dict) -> ft.Container:
    contacts = _as_list(problem.get("contacts")) or ["Уполномоченный орган по месту обращения."]
    return info_card("Куда обращаться", contacts, ft.Icons.LOCATION_ON_OUTLINED, "green")


def _errors_card(problem: dict) -> ft.Container:
    return info_card("Частые ошибки", problem.get("errors", []) or ["Ошибки будут добавлены позже."], ft.Icons.REPORT_PROBLEM_OUTLINED, "danger")


def _sources_card(problem: dict) -> ft.Container:
    source_controls: list[ft.Control] = []
    for source in _source_items(problem):
        checked = source.get("last_checked_at") or "требует проверки"
        source_controls.append(
            ft.Row(
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    icon_circle(ft.Icons.GAVEL_OUTLINED, color=APP_COLORS["blue_text"], bgcolor=APP_COLORS["active"], size=42),
                    ft.Column(
                        spacing=5,
                        expand=True,
                        controls=[
                            ft.Text(source["title"], size=14, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                            ft.Text(source["url"], size=12, color=APP_COLORS["blue_text"]),
                            ft.Text(source.get("description", ""), size=12, color=APP_COLORS["muted"]),
                            badge(f"Проверено: {checked}" if source.get("last_checked_at") else "требует проверки", "success" if source.get("last_checked_at") else "warning"),
                        ],
                    ),
                ],
            )
        )
    return app_card(
        ft.Column(
            spacing=16,
            controls=[
                _section_heading("Официальные источники", ft.Icons.BALANCE_OUTLINED, "blue", 21),
                ft.Text(
                    "Информация используется в справочных целях и должна сверяться с официальными ресурсами.",
                    size=13,
                    color=APP_COLORS["muted"],
                ),
                ft.Column(spacing=14, controls=source_controls),
            ],
        ),
        padding=18,
    )


def _related_card(problem: dict) -> ft.Container:
    rows: list[ft.Control] = []
    for item in _related_problems(problem):
        rows.append(
            ft.Row(
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    icon_circle(ft.Icons.ARROW_OUTWARD_OUTLINED, size=34),
                    ft.Column(
                        spacing=2,
                        expand=True,
                        controls=[
                            ft.Text(item["title"], size=14, weight=ft.FontWeight.W_900, color=APP_COLORS["text"], max_lines=2),
                            ft.Text(item.get("category_name", ""), size=12, color=APP_COLORS["muted"]),
                        ],
                    ),
                ],
            )
        )
    return app_card(
        ft.Column(
            spacing=14,
            controls=[
                ft.Text("Связанные проблемы", size=18, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                ft.Column(spacing=12, controls=rows),
            ],
        ),
        padding=18,
    )


def _contents_card() -> ft.Container:
    items = ["Что делать сейчас", "Пошаговый план", "Документы", "Сроки и стоимость", "Куда обращаться", "Источники"]
    return app_card(
        ft.Column(
            spacing=10,
            controls=[
                ft.Text("Содержание", size=18, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                ft.Column(
                    spacing=7,
                    controls=[
                        ft.Row(
                            spacing=8,
                            controls=[
                                ft.Icon(ft.Icons.CIRCLE, size=7, color=APP_COLORS["blue"] if index == 0 else APP_COLORS["muted2"]),
                                ft.Text(item, size=13, weight=ft.FontWeight.W_800, color=APP_COLORS["text"] if index == 0 else APP_COLORS["muted"]),
                            ],
                        )
                        for index, item in enumerate(items)
                    ],
                ),
            ],
        ),
        padding=18,
    )


def _quiz_questions(problem_id: str) -> list[dict]:
    return [question for question in LEARNING_QUESTIONS if question["problem_id"] == problem_id]


def _quiz_score(questions: list[dict], answers: dict) -> int:
    return len([question for question in questions if answers.get(question["id"]) == question["correct"]])


def _quiz_level(score: int) -> str:
    if score <= 1:
        return "Стоит повторить тему"
    if score == 2:
        return "Базовый уровень"
    return "Вы хорошо подготовлены"


def _quiz_block(problem: dict, quiz_state: dict, on_quiz_answer, on_submit_quiz, on_reset_quiz) -> ft.Control:
    questions = _quiz_questions(problem["id"])
    if not questions:
        return ft.Container()

    answers = quiz_state.get("answers", {})
    submitted = quiz_state.get("submitted", False)
    score = _quiz_score(questions, answers)

    question_cards: list[ft.Control] = []
    for index, question in enumerate(questions, start=1):
        selected = answers.get(question["id"])
        feedback = None
        if submitted:
            is_correct = selected == question["correct"]
            feedback = badge("Верно" if is_correct else "Нужно повторить", "success" if is_correct else "warning")
        question_cards.append(
            app_card(
                ft.Column(
                    spacing=12,
                    controls=[
                        ft.Row(
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.START,
                            controls=[
                                badge(f"Вопрос {index}", "blue"),
                                ft.Text(question["question"], size=15, weight=ft.FontWeight.W_900, color=APP_COLORS["text"], expand=True),
                            ]
                            + ([feedback] if feedback else []),
                        ),
                        ft.RadioGroup(
                            value=selected,
                            on_change=lambda event, question_id=question["id"]: on_quiz_answer(question_id, event.control.value)
                            if on_quiz_answer
                            else None,
                            content=ft.Column(
                                spacing=4,
                                controls=[
                                    ft.Radio(value=option, label=option, fill_color=APP_COLORS["blue"])
                                    for option in question["options"]
                                ],
                            ),
                        ),
                    ],
                ),
                padding=16,
            )
        )

    result_control: ft.Control
    if submitted:
        result_control = app_card(
            ft.Column(
                spacing=10,
                controls=[
                    ft.Text(f"Ваш результат: {score} из {len(questions)}", size=20, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                    ft.Text(_quiz_level(score), size=15, color=APP_COLORS["blue_text"], weight=ft.FontWeight.W_800),
                    primary_button("Пройти ещё раз", icon=ft.Icons.REPLAY, on_click=on_reset_quiz, expand=True),
                ],
            ),
            bgcolor=APP_COLORS["surface3"],
            border_color=APP_COLORS["stroke2"],
        )
    else:
        result_control = primary_button("Проверить ответы", icon=ft.Icons.CHECK_CIRCLE_OUTLINE, on_click=on_submit_quiz, expand=True)

    quiz_content = ft.Column(
        spacing=14,
        controls=[
            _section_heading("Проверьте себя", ft.Icons.QUIZ_OUTLINED, "purple", 22),
            ft.Text("Короткий тест помогает закрепить главное после чтения карточки.", size=14, color=APP_COLORS["muted"]),
            ft.Column(spacing=12, controls=question_cards),
            result_control,
        ],
    )

    return ft.AnimatedSwitcher(
        content=app_card(quiz_content, padding=18, border_color=APP_COLORS["stroke2"]),
        duration=260,
        transition=ft.AnimatedSwitcherTransition.FADE,
    )


def _main_sections(
    problem: dict,
    values: list[bool],
    on_toggle_step,
    learning_mode: bool,
    quiz_state: dict,
    on_quiz_answer,
    on_submit_quiz,
    on_reset_quiz,
    desktop: bool,
) -> ft.Column:
    return ft.Column(
        spacing=24 if desktop else 20,
        controls=[
            _immediate_card(problem, desktop),
            _steps_section(problem, values, on_toggle_step, desktop),
            _documents_card(problem),
            ft.Column(
                spacing=14,
                controls=[
                    _section_heading("Сроки и стоимость", ft.Icons.EVENT_AVAILABLE_OUTLINED, "orange", 24 if desktop else 21),
                    _terms_cost_grid(problem),
                ],
            ),
            _contacts_card(problem),
            _errors_card(problem),
            _sources_card(problem),
            _quiz_block(problem, quiz_state, on_quiz_answer, on_submit_quiz, on_reset_quiz) if learning_mode else ft.Container(),
            hint_card(CONTENT_DISCLAIMER, ft.Icons.INFO_OUTLINE),
        ],
    )


def _desktop_problem_detail(
    problem: dict,
    go_back,
    completed_steps: list[bool],
    save_problem,
    create_plan,
    learning_mode: bool,
    quiz_state: dict,
    on_toggle_step,
    on_quiz_answer,
    on_submit_quiz,
    on_reset_quiz,
) -> ft.Control:
    values = _completed_values(problem, completed_steps)
    difficulty, difficulty_tone = _difficulty(problem)
    content = ft.Column(
        spacing=28,
        controls=[
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    _breadcrumb(go_back, True),
                    _flow_wrap(
                        [
                            badge(problem.get("category_name", "Документы"), _category_tone(problem)),
                            badge(difficulty, difficulty_tone),
                            badge(f"Обновлено 12 мая", "default"),
                        ]
                    ),
                ],
            ),
            ft.Row(
                spacing=34,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    ft.Container(
                        width=742,
                        content=ft.Column(
                            spacing=24,
                            controls=[
                                ft.Column(
                                    spacing=12,
                                    controls=[
                                        ft.Text(problem["title"], size=46, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                                        ft.Text(problem["description"], size=17, color=APP_COLORS["muted"]),
                                    ],
                                ),
                                _hero(problem, save_problem, create_plan, True),
                                _main_sections(
                                    problem,
                                    values,
                                    on_toggle_step,
                                    learning_mode,
                                    quiz_state,
                                    on_quiz_answer,
                                    on_submit_quiz,
                                    on_reset_quiz,
                                    True,
                                ),
                            ],
                        ),
                    ),
                    ft.Container(
                        width=350,
                        content=ft.Column(
                            spacing=16,
                            controls=[
                                _contents_card(),
                                _summary_card(problem, values, save_problem, create_plan),
                                _documents_card(problem, compact=True),
                                _contacts_card(problem),
                                _related_card(problem),
                            ],
                        ),
                    ),
                ],
            ),
        ],
    )
    return desktop_content(content, width=1130, top=44, bottom=120)


def _mobile_problem_detail(
    problem: dict,
    go_back,
    completed_steps: list[bool],
    save_problem,
    create_plan,
    learning_mode: bool,
    quiz_state: dict,
    on_toggle_step,
    on_quiz_answer,
    on_submit_quiz,
    on_reset_quiz,
) -> ft.Control:
    values = _completed_values(problem, completed_steps)
    difficulty, difficulty_tone = _difficulty(problem)
    content = ft.Column(
        spacing=20,
        controls=[
            ft.Row(
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=APP_COLORS["muted"], on_click=go_back, tooltip="Назад"),
                    ft.Text("Карточка проблемы", size=17, weight=ft.FontWeight.W_900, color=APP_COLORS["text"], expand=True, max_lines=1),
                    ft.IconButton(icon=ft.Icons.BOOKMARK_BORDER, icon_color=APP_COLORS["muted"], on_click=save_problem, tooltip="Сохранить"),
                ],
            ),
            _mobile_badges(problem),
            ft.Column(
                spacing=10,
                controls=[
                    ft.Text(problem["title"], size=34, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                    ft.Text(problem["description"], size=15, color=APP_COLORS["muted"]),
                ],
            ),
            _hero(problem, save_problem, create_plan, False),
            _summary_card(problem, values, save_problem, create_plan),
            _main_sections(
                problem,
                values,
                on_toggle_step,
                learning_mode,
                quiz_state,
                on_quiz_answer,
                on_submit_quiz,
                on_reset_quiz,
                False,
            ),
            primary_button("Создать персональный план", on_click=create_plan, icon=ft.Icons.ADD_TASK_OUTLINED, expand=True),
        ],
    )
    return ft.Container(width=340, content=content)


def build_problem_detail_page(
    problem_id: str,
    go_back,
    create_plan,
    is_desktop: bool = False,
    completed_steps: list[bool] | None = None,
    on_toggle_step=None,
    learning_mode: bool = True,
    quiz_state: dict | None = None,
    on_quiz_answer=None,
    on_submit_quiz=None,
    on_reset_quiz=None,
    save_problem=None,
    problem_override: dict | None = None,
) -> ft.Control:
    problem = problem_override or find_problem(problem_id)
    quiz = quiz_state or {"answers": {}, "submitted": False}
    return (
        _desktop_problem_detail(
            problem,
            go_back,
            completed_steps or [],
            save_problem,
            create_plan,
            learning_mode,
            quiz,
            on_toggle_step,
            on_quiz_answer,
            on_submit_quiz,
            on_reset_quiz,
        )
        if is_desktop
        else _mobile_problem_detail(
            problem,
            go_back,
            completed_steps or [],
            save_problem,
            create_plan,
            learning_mode,
            quiz,
            on_toggle_step,
            on_quiz_answer,
            on_submit_quiz,
            on_reset_quiz,
        )
    )
