from __future__ import annotations

import flet as ft

from components.buttons import ghost_button, primary_button
from components.cards import app_card, badge, category_chip, empty_state_card, icon_circle, page_heading, search_box
from components.layout import desktop_content
from components.placeholders import photo_placeholder
from data.mock_data import MOCK_USER, SCENARIO_TEMPLATES
from theme.app_theme import APP_COLORS, CENTER, RADIUS, SPACING, border_all, get_badge_palette, padding_symmetric


ALL_CATEGORY = "Все"
FAVORITES_CATEGORY = "Избранное"

CATEGORY_OPTIONS = [
    (ALL_CATEGORY, ALL_CATEGORY),
    ("Семья", "Семья"),
    ("Документы", "Документы"),
    ("Жильё", "Жильё и ЖКХ"),
    ("Работа", "work"),
    ("Здоровье", "health"),
    ("ИП", "Бизнес/ИП"),
    (FAVORITES_CATEGORY, FAVORITES_CATEGORY),
]

CATEGORY_TONES = {
    "Семья": "green",
    "Документы": "blue",
    "Жильё и ЖКХ": "purple",
    "Бизнес/ИП": "cyan",
    "Авто": "cyan",
    "work": "purple",
    "health": "red",
    "taxes": "orange",
    "social": "green",
}

CATEGORY_ICONS = {
    "Семья": ft.Icons.FAMILY_RESTROOM_OUTLINED,
    "Документы": ft.Icons.BADGE_OUTLINED,
    "Жильё и ЖКХ": ft.Icons.HOME_WORK_OUTLINED,
    "Бизнес/ИП": ft.Icons.BUSINESS_CENTER_OUTLINED,
    "Авто": ft.Icons.DIRECTIONS_CAR_OUTLINED,
    "work": ft.Icons.WORK_OUTLINE,
    "health": ft.Icons.HEALTH_AND_SAFETY_OUTLINED,
    "taxes": ft.Icons.ACCOUNT_BALANCE_OUTLINED,
    "social": ft.Icons.VOLUNTEER_ACTIVISM_OUTLINED,
}

_PROFILE_TAG_TO_SCENARIO_CATS: dict[str, set[str]] = {
    "family": {"Семья"},
    "housing": {"Жильё и ЖКХ"},
    "business": {"Бизнес/ИП"},
    "documents": {"Документы"},
    "taxes": {"taxes"},
    "auto": {"Авто"},
    "health": {"health"},
    "employment": {"work"},
    "social": {"social"},
}

_EMPLOYMENT_TO_SCENARIO_CATS: dict[str, set[str]] = {
    "ip": {"Бизнес/ИП", "taxes"},
    "employee": {"work"},
    "student": {"Документы"},
    "pensioner": {"social"},
}


def _tone_colors(tone: str) -> tuple[str, str]:
    palette = get_badge_palette()
    return palette.get(tone, palette["blue"])


def _category_tone(category: str) -> str:
    return CATEGORY_TONES.get(category, "blue")


def _category_icon(category: str) -> str:
    return CATEGORY_ICONS.get(category, ft.Icons.ROUTE_OUTLINED)


def _difficulty_variant(difficulty: str) -> str:
    if difficulty == "Лёгкая":
        return "success"
    if difficulty == "Сложная":
        return "warning"
    return "orange"


def _difficulty_text(difficulty: str) -> str:
    if difficulty == "Лёгкая":
        return "Лёгкая"
    if difficulty == "Сложная":
        return "Сложная"
    return "Средняя"


def _recommended_templates(user: dict | None) -> list[dict]:
    if not user:
        return []
    cats: set[str] = set()
    for tag in user.get("interest_tags") or []:
        cats |= _PROFILE_TAG_TO_SCENARIO_CATS.get(tag, set())
    cats |= _EMPLOYMENT_TO_SCENARIO_CATS.get(user.get("employment_status", ""), set())
    if user.get("has_children"):
        cats.add("Семья")
    if user.get("is_homeowner") or user.get("is_tenant"):
        cats.add("Жильё и ЖКХ")
    if user.get("has_car"):
        cats.add("Авто")
    if not cats:
        return []
    return [template for template in SCENARIO_TEMPLATES if template.get("category") in cats][:4]


def _selected_value(selected_category: str) -> str:
    values = {value for _, value in CATEGORY_OPTIONS}
    labels = {label: value for label, value in CATEGORY_OPTIONS}
    if selected_category in values:
        return selected_category
    return labels.get(selected_category, ALL_CATEGORY)


def _matches_query(template: dict, query: str) -> bool:
    if not query:
        return True
    haystack = " ".join(
        [
            template.get("title", ""),
            template.get("short_description", ""),
            template.get("description", ""),
            template.get("category", ""),
            template.get("difficulty", ""),
            template.get("estimated_duration", ""),
        ]
    ).lower()
    return query.lower() in haystack


def _filtered_templates(query: str, category: str, favorite_ids: set[str]) -> list[dict]:
    normalized_query = (query or "").strip()
    selected = _selected_value(category)
    filtered: list[dict] = []
    for template in SCENARIO_TEMPLATES:
        is_favorite = template.get("id") in favorite_ids
        matches_category = selected == ALL_CATEGORY or template.get("category") == selected
        if selected == FAVORITES_CATEGORY:
            matches_category = is_favorite
        if matches_category and _matches_query(template, normalized_query):
            filtered.append(template)
    return filtered


def _scenario_meta(template: dict) -> tuple[int, int, str]:
    stage_count = len(template.get("stages", []))
    task_count = len(template.get("tasks", []))
    duration = template.get("estimated_duration", "срок уточняется")
    return stage_count, task_count, duration


def _photo_label(template: dict) -> str:
    return template.get("title", "сценарий").lower()


def _empty_state() -> ft.Container:
    return empty_state_card(
        "Сценарии не найдены",
        "Попробуйте изменить запрос или выбрать другую категорию.",
        action_text="Показать все",
        icon=ft.Icons.ROUTE_OUTLINED,
    )


def _favorite_button(template: dict, is_favorite: bool, on_toggle_favorite) -> ft.Container:
    tone = "orange" if is_favorite else "blue"
    badge_bg, badge_fg = _tone_colors(tone)
    return ft.Container(
        width=44,
        height=44,
        border_radius=22,
        bgcolor=badge_bg,
        border=border_all(badge_fg if is_favorite else APP_COLORS["stroke2"]),
        alignment=CENTER,
        scale=1.06 if is_favorite else 1,
        animate_scale=ft.Animation(220, ft.AnimationCurve.EASE_OUT),
        on_click=lambda _, template_id=template["id"]: on_toggle_favorite(template_id) if on_toggle_favorite else None,
        ink=True,
        content=ft.Icon(
            ft.Icons.STAR if is_favorite else ft.Icons.STAR_BORDER,
            size=22,
            color=badge_fg,
        ),
    )


def _scenario_card(
    template: dict,
    open_template,
    desktop: bool,
    favorite_ids: set[str],
    on_toggle_favorite=None,
    compact: bool = False,
) -> ft.Container:
    is_favorite = template["id"] in favorite_ids
    category = template.get("category", "Сценарий")
    category_tone = _category_tone(category)
    badge_bg, badge_fg = _tone_colors(category_tone)
    stage_count, task_count, duration = _scenario_meta(template)
    image_height = 92 if compact else 106

    card_body = ft.Column(
        spacing=14 if desktop and not compact else 10,
        controls=[
            ft.Stack(
                height=image_height,
                controls=[
                    photo_placeholder(_photo_label(template), height=image_height),
                    ft.Container(
                        right=10,
                        top=10,
                        content=_favorite_button(template, is_favorite, on_toggle_favorite),
                    ),
                ],
            ),
            ft.Row(
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    icon_circle(_category_icon(category), color=badge_fg, bgcolor=badge_bg, size=46 if not compact else 40),
                    ft.Column(
                        spacing=6,
                        expand=True,
                        controls=[
                            badge(category, category_tone),
                            ft.Text(
                                template["title"],
                                size=22 if desktop and not compact else 18,
                                weight=ft.FontWeight.W_900,
                                color=APP_COLORS["text"],
                                max_lines=2,
                            ),
                            ft.Text(
                                template.get("short_description") or template.get("description", ""),
                                size=14 if not compact else 13,
                                color=APP_COLORS["muted"],
                                max_lines=2 if compact else 3,
                            ),
                        ],
                    ),
                    ft.Icon(ft.Icons.CHEVRON_RIGHT, size=22, color=APP_COLORS["muted2"]),
                ],
            ),
            ft.Row(
                spacing=9,
                run_spacing=8,
                wrap=True,
                controls=[
                    _meta_chip(f"{stage_count} этапов", ft.Icons.VIEW_TIMELINE_OUTLINED),
                    _meta_chip(f"{task_count} шагов", ft.Icons.CHECKLIST_RTL_OUTLINED),
                    _meta_chip(duration, ft.Icons.SCHEDULE_OUTLINED),
                    badge(_difficulty_text(template.get("difficulty", "")), _difficulty_variant(template.get("difficulty", ""))),
                ],
            ),
        ],
    )
    return ft.Container(
        content=app_card(card_body, padding=18 if desktop and not compact else 14, animate=True),
        on_click=lambda _: open_template(template["id"]) if open_template else None,
        ink=True,
    )


def _meta_chip(text: str, icon: str) -> ft.Container:
    return ft.Container(
        padding=padding_symmetric(horizontal=10, vertical=6),
        border_radius=14,
        bgcolor=APP_COLORS["surface2"],
        border=border_all(APP_COLORS["stroke2"]),
        content=ft.Row(
            spacing=6,
            tight=True,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(icon, size=15, color=APP_COLORS["blue_text"]),
                ft.Text(text, size=12, weight=ft.FontWeight.W_800, color=APP_COLORS["muted"], max_lines=1, no_wrap=True),
            ],
        ),
    )


def _category_chips(selected_category: str, on_category_change, mobile: bool = False) -> ft.Control:
    selected = _selected_value(selected_category)
    chips = [
        category_chip(
            label,
            selected=value == selected,
            on_click=lambda _, category_value=value: on_category_change(category_value) if on_category_change else None,
        )
        for label, value in CATEGORY_OPTIONS
    ]
    return ft.Row(
        spacing=10,
        run_spacing=10,
        wrap=not mobile,
        scroll=ft.ScrollMode.AUTO if mobile else None,
        controls=chips,
    )


def _recommended_section(
    recommended: list[dict],
    open_template,
    is_desktop: bool,
    favorite_ids: set[str],
    on_toggle_favorite,
) -> ft.Control:
    if not recommended:
        return ft.Container()
    cards = [
        ft.Container(
            col={"xs": 12, "md": 6},
            content=_scenario_card(template, open_template, is_desktop, favorite_ids, on_toggle_favorite),
        )
        for template in recommended[:2 if is_desktop else 3]
    ]
    return ft.Column(
        spacing=14,
        controls=[
            ft.Row(
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text("Рекомендуемые сценарии", size=24 if is_desktop else 20, weight=ft.FontWeight.W_900, color=APP_COLORS["text"], expand=True),
                    badge("подходят по профилю", "default") if is_desktop else ft.Container(),
                ],
            ),
            ft.ResponsiveRow(columns=12, spacing=16, run_spacing=16, controls=cards),
        ],
    )


def _all_scenarios_section(
    templates: list[dict],
    open_template,
    is_desktop: bool,
    favorite_ids: set[str],
    on_toggle_favorite,
) -> ft.Control:
    if not templates:
        return _empty_state()
    return ft.Column(
        spacing=14,
        controls=[
            ft.Row(
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text("Все сценарии", size=24 if is_desktop else 20, weight=ft.FontWeight.W_900, color=APP_COLORS["text"], expand=True),
                    badge("популярные", "blue"),
                ],
            ),
            ft.ResponsiveRow(
                columns=12,
                spacing=16,
                run_spacing=16,
                controls=[
                    ft.Container(
                        col={"xs": 12, "md": 6},
                        content=_scenario_card(template, open_template, is_desktop, favorite_ids, on_toggle_favorite),
                    )
                    for template in templates
                ],
            ),
        ],
    )


def _quick_start_card(open_template) -> ft.Container:
    return app_card(
        ft.Column(
            spacing=14,
            controls=[
                ft.Text("Быстрый старт", size=22, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                ft.Text("Запустите сценарий и получите личные задачи с дедлайнами.", size=14, color=APP_COLORS["muted"]),
                primary_button("Создать мою ситуацию", icon=ft.Icons.ADD_TASK_OUTLINED, on_click=lambda _: open_template("childbirth"), expand=True),
            ],
        ),
        padding=22,
        bgcolor=APP_COLORS["surface3"],
    )


def _popular_card(open_template, templates: list[dict]) -> ft.Container:
    rows: list[ft.Control] = []
    for template in templates[:3]:
        stage_count, task_count, duration = _scenario_meta(template)
        category = template.get("category", "")
        badge_bg, badge_fg = _tone_colors(_category_tone(category))
        rows.append(
            ft.Container(
                padding=14,
                border_radius=RADIUS["lg"],
                bgcolor=APP_COLORS["surface2"],
                border=border_all(APP_COLORS["stroke2"]),
                on_click=lambda _, template_id=template["id"]: open_template(template_id),
                ink=True,
                content=ft.Row(
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        icon_circle(_category_icon(category), color=badge_fg, bgcolor=badge_bg, size=42),
                        ft.Column(
                            spacing=2,
                            expand=True,
                            controls=[
                                ft.Text(template["title"], size=14, weight=ft.FontWeight.W_900, color=APP_COLORS["text"], max_lines=2),
                                ft.Text(f"{task_count} шагов • {duration}", size=12, color=APP_COLORS["muted"]),
                            ],
                        ),
                        ft.Icon(ft.Icons.CHEVRON_RIGHT, size=18, color=APP_COLORS["muted2"]),
                    ],
                ),
            )
        )
    return app_card(
        ft.Column(
            spacing=12,
            controls=[
                ft.Text("Популярное сейчас", size=20, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                ft.Column(spacing=10, controls=rows),
            ],
        ),
        padding=18,
    )


def _inside_card(templates: list[dict]) -> ft.Container:
    total_steps = sum(len(template.get("tasks", [])) for template in templates)
    avg_steps = round(total_steps / len(templates)) if templates else 0
    rows = [
        ("Этапы и задачи", ft.Icons.VIEW_TIMELINE_OUTLINED),
        ("Сроки и дедлайны", ft.Icons.SCHEDULE_OUTLINED),
        ("Документы", ft.Icons.ARTICLE_OUTLINED),
        ("Куда обращаться", ft.Icons.LOCATION_ON_OUTLINED),
        ("Напоминания", ft.Icons.NOTIFICATIONS_NONE_OUTLINED),
    ]
    return app_card(
        ft.Column(
            spacing=14,
            controls=[
                ft.Text("Что будет внутри", size=20, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                ft.Column(
                    spacing=11,
                    controls=[
                        ft.Row(
                            spacing=10,
                            controls=[
                                ft.Icon(icon, size=18, color=APP_COLORS["blue_text"]),
                                ft.Text(label, size=14, weight=ft.FontWeight.W_800, color=APP_COLORS["muted"], expand=True),
                            ],
                        )
                        for label, icon in rows
                    ],
                ),
                ft.ProgressBar(
                    value=min(avg_steps / 14, 1),
                    bar_height=10,
                    border_radius=12,
                    color=APP_COLORS["blue"],
                    bgcolor=APP_COLORS["surface2"],
                ),
                ft.Text(f"Средний сценарий: {avg_steps} шагов", size=13, weight=ft.FontWeight.W_900, color=APP_COLORS["muted"]),
            ],
        ),
        padding=18,
    )


def _desktop_scenarios(
    open_template,
    query: str,
    selected_category: str,
    on_query_change,
    on_category_change,
    favorite_ids: set[str],
    on_toggle_favorite,
    user: dict | None,
    go_to=None,
) -> ft.Control:
    templates = _filtered_templates(query, selected_category, favorite_ids)
    recommended = _recommended_templates(user) if not query and _selected_value(selected_category) == ALL_CATEGORY else []
    content = ft.Column(
        spacing=26,
        controls=[
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.END,
                controls=[
                    page_heading(
                        "Жизненные сценарии",
                        "Готовые планы для важных жизненных событий: от документов до ЖКХ и налогов.",
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
                hint="Поиск сценария: рождение ребёнка, переезд, ИП, медкнижка...",
                on_change=lambda event: on_query_change(event.control.value) if on_query_change else None,
            ),
            _category_chips(selected_category, on_category_change),
            ft.Row(
                spacing=26,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    ft.Container(
                        width=800,
                        content=ft.Column(
                            spacing=26,
                            controls=[
                                _recommended_section(recommended, open_template, True, favorite_ids, on_toggle_favorite),
                                _all_scenarios_section(templates, open_template, True, favorite_ids, on_toggle_favorite),
                            ],
                        ),
                    ),
                    ft.Container(
                        width=300,
                        content=ft.Column(
                            spacing=16,
                            controls=[
                                _quick_start_card(open_template),
                                _popular_card(open_template, SCENARIO_TEMPLATES),
                                _inside_card(SCENARIO_TEMPLATES),
                            ],
                        ),
                    ),
                ],
            ),
        ],
    )
    return desktop_content(content, width=1130, top=44, bottom=120)


def _mobile_scenarios(
    open_template,
    query: str,
    selected_category: str,
    on_query_change,
    on_category_change,
    favorite_ids: set[str],
    on_toggle_favorite,
    user: dict | None,
) -> ft.Control:
    templates = _filtered_templates(query, selected_category, favorite_ids)
    recommended = _recommended_templates(user) if not query and _selected_value(selected_category) == ALL_CATEGORY else []
    content = ft.Column(
        spacing=18,
        controls=[
            ft.Row(
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(ft.Icons.ARROW_BACK_IOS_NEW, size=18, color=APP_COLORS["muted"]),
                    ft.Text("Жизненные сценарии", size=22, weight=ft.FontWeight.W_900, color=APP_COLORS["text"], expand=True),
                    icon_circle(ft.Icons.TEXT_FIELDS, color=APP_COLORS["blue_text"], bgcolor=APP_COLORS["active"], size=44),
                    icon_circle(ft.Icons.NOTIFICATIONS_NONE_OUTLINED, color=APP_COLORS["blue_text"], bgcolor=APP_COLORS["active"], size=44),
                ],
            ),
            search_box(
                value=query,
                hint="Найдите сценарий...",
                on_change=lambda event: on_query_change(event.control.value) if on_query_change else None,
            ),
            _category_chips(selected_category, on_category_change, mobile=True),
            _recommended_section(recommended, open_template, False, favorite_ids, on_toggle_favorite),
            _all_scenarios_section(templates, open_template, False, favorite_ids, on_toggle_favorite),
        ],
    )
    return ft.Container(width=340, content=content)


def build_scenario_templates_page(
    open_template,
    is_desktop: bool = False,
    query: str = "",
    selected_category: str = ALL_CATEGORY,
    on_query_change=None,
    on_category_change=None,
    favorite_ids: list[str] | set[str] | None = None,
    on_toggle_favorite=None,
    user: dict | None = None,
    go_to=None,
) -> ft.Control:
    favorite_set = set(favorite_ids or [])
    profile_user = user or MOCK_USER
    if is_desktop:
        return _desktop_scenarios(
            open_template,
            query,
            selected_category,
            on_query_change,
            on_category_change,
            favorite_set,
            on_toggle_favorite,
            profile_user,
            go_to=go_to,
        )
    return _mobile_scenarios(
        open_template,
        query,
        selected_category,
        on_query_change,
        on_category_change,
        favorite_set,
        on_toggle_favorite,
        profile_user,
    )
