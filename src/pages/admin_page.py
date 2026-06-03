import flet as ft

from components.buttons import primary_button, secondary_button
from components.cards import app_card, badge, icon_circle, page_heading
from components.layout import desktop_content
from theme.app_theme import APP_COLORS, border_all, padding_symmetric, ts


ACTION_OPTIONS = [
    ("info", "Информация"),
    ("visit_office", "Посещение органа"),
    ("online_request", "Онлайн-запрос"),
    ("document_prepare", "Подготовка документа"),
    ("payment", "Оплата"),
    ("waiting", "Ожидание"),
]


LAW_CATEGORY_OPTIONS = [
    ("taxes", "Налоги"),
    ("home", "ЖКХ"),
    ("docs", "Документы"),
    ("family", "Семья"),
    ("work", "Работа"),
]


SOURCE_TYPE_OPTIONS = [
    ("law", "Право"),
    ("government_portal", "Госпортал"),
    ("ministry", "Министерство"),
    ("court", "Суд"),
    ("tax", "Налоги"),
    ("registry", "Реестр / ЗАГС"),
    ("local_authority", "Исполком"),
    ("other", "Другое"),
]


def _field(
    label: str,
    value: str = "",
    hint_text: str = "",
    *,
    multiline: bool = False,
    min_lines: int = 1,
    max_lines: int = 1,
    width: int | None = None,
    keyboard_type=None,
    helper: str | None = None,
    helper_max_lines: int | None = None,
    read_only: bool = False,
    dense: bool = True,
    expand: bool | int | None = None,
) -> ft.TextField:
    """Единый стиль TextField для всей админки — без серого Material3-фила."""
    is_multi = multiline or min_lines > 1
    kw: dict = {}
    if keyboard_type is not None:
        kw["keyboard_type"] = keyboard_type
    if helper is not None:
        kw["helper"] = helper
    if helper_max_lines is not None:
        kw["helper_max_lines"] = helper_max_lines
    if expand is not None:
        kw["expand"] = expand
    return ft.TextField(
        label=label,
        value=value or "",
        hint_text=hint_text,
        multiline=is_multi,
        min_lines=min_lines if is_multi else 1,
        max_lines=max_lines if is_multi else 1,
        width=width,
        border_radius=12,
        border_color=APP_COLORS["stroke2"],
        focused_border_color=APP_COLORS["primary"],
        bgcolor=APP_COLORS["surface"],
        fill_color=APP_COLORS["surface"],
        filled=True,
        color=APP_COLORS["text"],
        cursor_color=APP_COLORS["primary"],
        label_style=ft.TextStyle(color=APP_COLORS["muted"]),
        hint_style=ft.TextStyle(color=APP_COLORS["muted2"]),
        text_style=ft.TextStyle(size=ts(14)),
        content_padding=ft.Padding(left=12, top=10, right=12, bottom=10),
        dense=dense,
        read_only=read_only,
        **kw,
    )


def _status_badge(status: str) -> ft.Container:
    if status == "published":
        return badge("published", "success")
    if status == "archived":
        return badge("archived", "default")
    return badge("draft", "warning")


def _source_status_badge(status: str) -> ft.Container:
    if status == "active":
        return badge("активен", "success")
    if status == "archived":
        return badge("архив", "default")
    return badge("требует проверки", "warning")


def _required_badge(required: bool) -> ft.Container:
    return badge("Обязательный" if required else "Необязательный", "success" if required else "default")


def _status_toggle_button(status: str, on_click) -> ft.Control:
    if status == "published":
        return secondary_button("В черновик", on_click=on_click, height=38)
    return primary_button("Опубликовать", on_click=on_click, height=38)


def _api_status_card(state: dict, on_refresh=None) -> ft.Container:
    connected = bool(state.get("connected"))
    return app_card(
        ft.Row(
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                icon_circle(
                    ft.Icons.CLOUD_DONE_OUTLINED if connected else ft.Icons.CLOUD_OFF_OUTLINED,
                    color=APP_COLORS["primary"] if connected else APP_COLORS["warning"],
                    bgcolor=APP_COLORS["primary_light"] if connected else APP_COLORS["warning_light"],
                    size=42,
                ),
                ft.Column(
                    spacing=2,
                    expand=True,
                    controls=[
                        ft.Text("Backend API", size=ts(16), weight=ft.FontWeight.BOLD, color=APP_COLORS["text"]),
                        ft.Text(
                            "Подключено" if connected else state.get("error", "Нет подключения"),
                            size=ts(13),
                            color=APP_COLORS["muted"],
                        ),
                        ft.Text(
                            f"Последняя синхронизация: {state.get('last_sync') or '—'}",
                            size=ts(12),
                            color=APP_COLORS["muted"],
                        ),
                    ],
                ),
                secondary_button("Обновить", on_click=on_refresh, icon=ft.Icons.REFRESH, height=40),
            ],
        ),
        border_color="#A7F3D0" if connected else "#FDE68A",
        bgcolor=APP_COLORS["primary_light"] if connected else APP_COLORS["warning_light"],
    )


def _role_by_id(roles: list[dict], role_id: str) -> dict:
    for role in roles:
        if role.get("id") == role_id:
            return role
    return roles[0] if roles else {}


_AUDIT_EVENT_LABELS = {
    "create": "Создание",
    "update": "Изменение",
    "delete": "Удаление",
    "other": "Прочее",
}
_AUDIT_EVENT_VARIANTS = {
    "create": "success",
    "update": "blue",
    "delete": "error",
    "other": "default",
}


def _full_audit_log_card(audit_logs: list[dict], selected_filter: str = "all") -> ft.Container:
    filter_options = [("all", "Все")] + list(_AUDIT_EVENT_LABELS.items())
    filtered = audit_logs if selected_filter == "all" else [e for e in audit_logs if e.get("event_type") == selected_filter]

    chips = ft.Row(
        wrap=True,
        spacing=8,
        run_spacing=8,
        controls=[
            ft.Container(
                padding=padding_symmetric(horizontal=12, vertical=6),
                border_radius=999,
                bgcolor=APP_COLORS["primary"] if selected_filter == fid else APP_COLORS["surface_alt"],
                border=border_all(APP_COLORS["primary"] if selected_filter == fid else APP_COLORS["border_soft"]),
                content=ft.Text(flabel, size=ts(12), weight=ft.FontWeight.W_700, color="#FFFFFF" if selected_filter == fid else APP_COLORS["text"]),
            )
            for fid, flabel in filter_options
        ],
    )

    rows: list[ft.Control] = []
    for entry in filtered[:20]:
        etype = entry.get("event_type", "other")
        rows.append(
            ft.Container(
                padding=ft.Padding(left=10, top=8, right=10, bottom=8),
                border_radius=12,
                bgcolor=APP_COLORS["surface_alt"],
                content=ft.Column(
                    spacing=4,
                    controls=[
                        ft.Row(
                            spacing=6,
                            wrap=True,
                            controls=[
                                badge(_AUDIT_EVENT_LABELS.get(etype, "Прочее"), _AUDIT_EVENT_VARIANTS.get(etype, "default")),
                                ft.Text(entry.get("action", "Действие"), size=ts(13), weight=ft.FontWeight.W_600, color=APP_COLORS["text"], expand=True),
                            ],
                        ),
                        ft.Text(
                            f"{entry.get('actor', 'Пользователь')} · {entry.get('role_id', '')} · {entry.get('created_at', '')}",
                            size=ts(11),
                            color=APP_COLORS["muted"],
                        ),
                    ],
                ),
            )
        )

    return app_card(
        ft.Column(
            spacing=12,
            controls=[
                ft.Row(
                    spacing=8,
                    controls=[
                        ft.Icon(ft.Icons.HISTORY_OUTLINED, size=ts(20), color=APP_COLORS["primary"]),
                        ft.Text("Журнал действий редактора", size=ts(16), weight=ft.FontWeight.BOLD, color=APP_COLORS["text"]),
                        ft.Text(f"({len(filtered)})", size=ts(13), color=APP_COLORS["muted"]),
                    ],
                ),
                chips,
                ft.Container(height=1, bgcolor=APP_COLORS["border_soft"]),
                ft.Column(spacing=6, controls=rows or [ft.Text("Действий по этому фильтру нет.", size=ts(13), color=APP_COLORS["muted"])]),
            ],
        ),
        padding=20,
    )


def _role_access_card(state: dict, on_select_admin_role=None) -> ft.Container:
    roles = state.get("roles", [])
    admin_users = state.get("admin_users", [])
    audit_logs = state.get("audit_logs", [])
    current_role_id = state.get("current_role") or "content_editor"
    current_role = _role_by_id(roles, current_role_id)
    role_title_by_id = {role.get("id"): role.get("title", role.get("id", "")) for role in roles}

    role_dropdown = ft.Dropdown(
        label="Текущий режим админки",
        value=current_role.get("id", current_role_id),
        options=[ft.dropdown.Option(role.get("id"), role.get("title", role.get("id"))) for role in roles],
        border_radius=12,
        on_select=lambda e: on_select_admin_role(e.control.value) if on_select_admin_role else None,
    )

    section_badges = [
        badge(section, "blue" if current_role.get("id") != "citizen" else "default")
        for section in current_role.get("sections", [])
    ]
    permission_items = [
        ft.Row(
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, size=ts(16), color=APP_COLORS["secondary"]),
                ft.Text(item, size=ts(13), color=APP_COLORS["muted"], expand=True),
            ],
        )
        for item in current_role.get("permissions", [])
    ]

    users_controls = [
        ft.Row(
            spacing=8,
            wrap=True,
            controls=[
                ft.Text(user.get("name", "Пользователь"), size=ts(13), weight=ft.FontWeight.W_600, color=APP_COLORS["text"], expand=True),
                badge(role_title_by_id.get(user.get("role_id"), user.get("role_id", "роль")), "default"),
                badge(user.get("status", "active"), "success" if user.get("status") == "active" else "warning"),
            ],
        )
        for user in admin_users
    ]
    audit_controls = [
        ft.Container(
            padding=ft.Padding(left=10, top=8, right=10, bottom=8),
            border_radius=12,
            bgcolor=APP_COLORS["surface_alt"],
            border=border_all(APP_COLORS["border"]),
            content=ft.Column(
                spacing=4,
                controls=[
                    ft.Text(item.get("action", "Действие"), size=ts(13), weight=ft.FontWeight.W_600, color=APP_COLORS["text"]),
                    ft.Text(
                        f"{item.get('actor', 'Пользователь')} · {role_title_by_id.get(item.get('role_id'), item.get('role_id', 'роль'))} · {item.get('created_at', '')}",
                        size=ts(12),
                        color=APP_COLORS["muted"],
                    ),
                ],
            ),
        )
        for item in audit_logs[:3]
    ]

    controls: list[ft.Control] = [
                ft.Row(
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        icon_circle(ft.Icons.ADMIN_PANEL_SETTINGS_OUTLINED, color=APP_COLORS["primary"], bgcolor=APP_COLORS["primary_light"], size=42),
                        ft.Column(
                            spacing=3,
                            expand=True,
                            controls=[
                                ft.Text("Роли и доступ", size=ts(20), weight=ft.FontWeight.BOLD, color=APP_COLORS["text"]),
                                ft.Text(
                                    "Три уровня доступа: гражданин, редактор контента и администратор площадки.",
                                    size=ts(13),
                                    color=APP_COLORS["muted"],
                                ),
                            ],
                        ),
                    ],
                ),
                role_dropdown,
                ft.Text(current_role.get("description", ""), size=ts(13), color=APP_COLORS["muted"]),
                ft.Text("Доступные разделы", size=ts(14), weight=ft.FontWeight.W_600, color=APP_COLORS["text"]),
                ft.Row(wrap=True, spacing=8, run_spacing=8, controls=section_badges or [badge("Нет разделов", "default")]),
                ft.Text("Права роли", size=ts(14), weight=ft.FontWeight.W_600, color=APP_COLORS["text"]),
                ft.Column(spacing=6, controls=permission_items or [ft.Text("Права пока не настроены.", size=ts(13), color=APP_COLORS["muted"])]),
    ]
    if current_role.get("id") == "platform_admin":
        controls.extend(
            [
                ft.Divider(height=1, color=APP_COLORS["border"]),
                ft.Text("Пользователи и роли", size=ts(14), weight=ft.FontWeight.W_600, color=APP_COLORS["text"]),
                ft.Column(spacing=8, controls=users_controls or [ft.Text("Пользователи пока не добавлены.", size=ts(13), color=APP_COLORS["muted"])]),
                ft.Text("Последние действия", size=ts(14), weight=ft.FontWeight.W_600, color=APP_COLORS["text"]),
                ft.Column(spacing=8, controls=audit_controls or [ft.Text("Журнал действий пока пуст.", size=ts(13), color=APP_COLORS["muted"])]),
            ]
        )
    else:
        controls.append(
            ft.Text(
                "Пользователи, роли и аудит доступны только в режиме «Админ площадки».",
                size=ts(12),
                color=APP_COLORS["muted"],
            )
        )

    return app_card(ft.Column(spacing=14, controls=controls))


def _problem_create_card(on_create_problem=None) -> ft.Container:
    title_field = _field("Название проблемы", hint_text="Например: Социальная помощь")
    category_field = _field("Категория", hint_text="Например: Семья")
    short_field = _field("Краткое описание", hint_text="Короткое описание для карточки",
                         multiline=True, min_lines=2, max_lines=3)

    def submit(_):
        if on_create_problem:
            on_create_problem(title_field.value or "", category_field.value or "", short_field.value or "")

    return app_card(
        ft.Column(
            spacing=12,
            controls=[
                ft.Text("Создать проблему", size=ts(18), weight=ft.FontWeight.BOLD, color=APP_COLORS["text"]),
                title_field,
                category_field,
                short_field,
                primary_button("Создать проблему", on_click=submit, icon=ft.Icons.ADD, expand=True),
            ],
        ),
    )


def _scenario_create_card(problems: list[dict], on_create_scenario=None) -> ft.Container:
    options = [ft.dropdown.Option(str(item["id"]), item["title"]) for item in problems]
    problem_dropdown = ft.Dropdown(
        label="Проблема",
        options=options,
        value=options[0].key if options else None,
        border_radius=12,
    )
    title_field = _field("Название сценария", hint_text="Например: Оформление пособий")
    short_field = _field("Краткое описание", hint_text="Описание сценария",
                         multiline=True, min_lines=2, max_lines=3)
    difficulty = ft.Dropdown(
        label="Сложность",
        value="medium",
        options=[
            ft.dropdown.Option("easy", "easy"),
            ft.dropdown.Option("medium", "medium"),
            ft.dropdown.Option("hard", "hard"),
        ],
        border_radius=12,
    )

    def submit(_):
        if on_create_scenario:
            try:
                problem_id = int(problem_dropdown.value) if problem_dropdown.value else 0
            except (TypeError, ValueError):
                problem_id = 0
            on_create_scenario(
                problem_id,
                title_field.value or "",
                short_field.value or "",
                difficulty.value or "medium",
            )

    return app_card(
        ft.Column(
            spacing=12,
            controls=[
                ft.Text("Создать сценарий", size=ts(18), weight=ft.FontWeight.BOLD, color=APP_COLORS["text"]),
                problem_dropdown,
                title_field,
                short_field,
                difficulty,
                primary_button("Создать сценарий", on_click=submit, icon=ft.Icons.ADD_TASK, expand=True),
            ],
        ),
    )


def _source_create_card(on_create_source=None) -> ft.Container:
    title_field = _field("Название источника", hint_text="Например: Министерство труда")
    url_field = _field("Сайт", hint_text="https://mintrud.gov.by/")
    source_type = ft.Dropdown(
        label="Тип источника",
        value="government_portal",
        options=[ft.dropdown.Option(value, label) for value, label in SOURCE_TYPE_OPTIONS],
        border_radius=12,
    )
    last_checked = _field("Дата проверки", hint_text="YYYY-MM-DD или оставить пустым")
    description = _field("Описание", hint_text="Что проверяется по этому источнику",
                         multiline=True, min_lines=2, max_lines=3)

    def submit(_):
        if on_create_source:
            on_create_source(
                title_field.value or "",
                url_field.value or "",
                source_type.value or "other",
                description.value or "",
                last_checked.value or "",
            )

    return app_card(
        ft.Column(
            spacing=12,
            controls=[
                ft.Text("Добавить источник", size=ts(18), weight=ft.FontWeight.BOLD, color=APP_COLORS["text"]),
                ft.Text(
                    "Используйте только открытые официальные ресурсы Республики Беларусь.",
                    size=ts(12),
                    color=APP_COLORS["muted"],
                ),
                title_field,
                url_field,
                ft.Row(
                    spacing=10,
                    run_spacing=10,
                    wrap=True,
                    controls=[
                        ft.Container(expand=True, content=source_type),
                        ft.Container(expand=True, content=last_checked),
                    ],
                ),
                description,
                primary_button("Добавить источник", on_click=submit, icon=ft.Icons.VERIFIED_OUTLINED, expand=True),
            ],
        )
    )


def _sources_list_card(
    sources: list[dict],
    on_edit_source=None,
    on_delete_source=None,
    on_set_source_status=None,
) -> ft.Container:
    source_type_map = dict(SOURCE_TYPE_OPTIONS)
    rows: list[ft.Control] = []
    if not sources:
        rows.append(ft.Text("Пока нет источников. Добавьте первый официальный источник.", size=ts(14), color=APP_COLORS["muted"]))

    for source in sources:
        current_status = source.get("status", "requires_check")
        next_status = "requires_check" if current_status == "active" else "active"
        rows.append(
            app_card(
                ft.Column(
                    spacing=10,
                    controls=[
                        ft.Row(
                            spacing=8,
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text(source.get("title", "Без названия"), size=ts(16), weight=ft.FontWeight.BOLD, color=APP_COLORS["text"], expand=True),
                                _source_status_badge(current_status),
                            ],
                        ),
                        ft.Row(
                            wrap=True,
                            spacing=6,
                            run_spacing=6,
                            controls=[
                                badge(source_type_map.get(source.get("source_type"), source.get("source_type", "Тип")), "blue"),
                                badge(f"Проверка: {source.get('last_checked_at') or 'требует проверки'}", "warning" if not source.get("last_checked_at") else "default"),
                            ],
                        ),
                        ft.Text(source.get("description", ""), size=ts(13), color=APP_COLORS["muted"]),
                        ft.Text(source.get("url", ""), size=ts(12), color=APP_COLORS["blue"]),
                        ft.Row(
                            alignment=ft.MainAxisAlignment.END,
                            spacing=8,
                            wrap=True,
                            controls=[
                                secondary_button(
                                    "Редактировать",
                                    icon=ft.Icons.EDIT_OUTLINED,
                                    height=38,
                                    on_click=lambda _, source_id=source["id"]: on_edit_source(source_id) if on_edit_source else None,
                                ),
                                secondary_button(
                                    "На проверку" if current_status == "active" else "Активировать",
                                    icon=ft.Icons.RULE_OUTLINED,
                                    height=38,
                                    on_click=lambda _, source_id=source["id"], status_value=next_status: on_set_source_status(source_id, status_value)
                                    if on_set_source_status
                                    else None,
                                ),
                                secondary_button(
                                    "Удалить",
                                    icon=ft.Icons.DELETE_OUTLINE,
                                    height=38,
                                    on_click=lambda _, source_id=source["id"]: on_delete_source(source_id) if on_delete_source else None,
                                ),
                            ],
                        ),
                    ],
                ),
                padding=14,
            )
        )

    return app_card(
        ft.Column(
            spacing=10,
            controls=[
                ft.Text("Официальные источники", size=ts(20), weight=ft.FontWeight.BOLD, color=APP_COLORS["text"]),
                ft.Text(
                    "Справочник нужен редактору для проверки сценариев, шагов и закон-апдейтов.",
                    size=ts(13),
                    color=APP_COLORS["muted"],
                ),
                *rows,
            ],
        )
    )


def _law_update_create_card(on_create_law_update=None) -> ft.Container:
    title_field = _field("Заголовок", hint_text="Например: Новые сроки подачи заявления")
    category_dropdown = ft.Dropdown(
        label="Категория",
        value="family",
        options=[ft.dropdown.Option(value, label) for value, label in LAW_CATEGORY_OPTIONS],
        border_radius=12,
    )
    target_field = _field("Кого касается", hint_text="Например: Семьи с детьми")
    date_field = _field("Дата вступления", hint_text="Например: 01.09.2026")
    short_field = _field("Что изменилось", hint_text="Короткое объяснение простым языком",
                         multiline=True, min_lines=2, max_lines=3)
    action_field = _field("Что сделать пользователю",
                          hint_text="Например: проверить срок обращения и подготовить документы",
                          multiline=True, min_lines=2, max_lines=3)
    related_field = _field("Связанные сценарии", hint_text="Через запятую: Рождение ребёнка, Пособия")
    related_problems_field = _field(
        "Связанные проблемы",
        hint_text="ID через запятую: childbirth, lost-passport",
    )
    source_field = _field("Официальный источник", hint_text="https://pravo.by/")
    priority_dropdown = ft.Dropdown(
        label="Приоритет",
        value="medium",
        options=[
            ft.dropdown.Option("low", "Низкий"),
            ft.dropdown.Option("medium", "Средний"),
            ft.dropdown.Option("high", "Высокий"),
        ],
        border_radius=12,
    )

    def submit(_):
        if on_create_law_update:
            on_create_law_update(
                title_field.value or "",
                category_dropdown.value or "family",
                target_field.value or "",
                date_field.value or "",
                short_field.value or "",
                action_field.value or "",
                related_field.value or "",
                related_problems_field.value or "",
                source_field.value or "",
                priority_dropdown.value or "medium",
            )

    return app_card(
        ft.Column(
            spacing=12,
            controls=[
                ft.Text("Добавить закон-апдейт", size=ts(18), weight=ft.FontWeight.BOLD, color=APP_COLORS["text"]),
                title_field,
                ft.Row(
                    spacing=10,
                    run_spacing=10,
                    wrap=True,
                    controls=[
                        ft.Container(expand=True, content=category_dropdown),
                        ft.Container(expand=True, content=priority_dropdown),
                    ],
                ),
                target_field,
                date_field,
                short_field,
                action_field,
                related_field,
                related_problems_field,
                source_field,
                primary_button("Добавить закон-апдейт", on_click=submit, icon=ft.Icons.GAVEL_OUTLINED, expand=True),
            ],
        ),
    )


def _law_updates_list_card(
    laws: list[dict],
    on_set_law_update_status=None,
    on_delete_law_update=None,
    on_edit_law_update=None,
) -> ft.Container:
    rows: list[ft.Control] = []
    if not laws:
        rows.append(ft.Text("Пока нет закон-апдейтов.", size=ts(14), color=APP_COLORS["muted"]))

    for item in laws:
        current_status = item.get("status", "published")
        next_status = "draft" if current_status == "published" else "published"
        priority = item.get("priority", "medium")
        related = item.get("related_scenarios") or []
        related_text = ", ".join(related) if related else "не указаны"
        related_problems = item.get("related_problems") or []
        related_problems_text = ", ".join(related_problems) if related_problems else "не указаны"
        rows.append(
            app_card(
                ft.Column(
                    spacing=10,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text(item.get("title", "Без названия"), size=ts(16), weight=ft.FontWeight.BOLD, color=APP_COLORS["text"], expand=True),
                                _status_badge(current_status),
                            ],
                        ),
                        ft.Row(
                            spacing=6,
                            run_spacing=6,
                            wrap=True,
                            controls=[
                                badge(item.get("category_name", item.get("category", "Категория")), "blue"),
                                badge(f"Приоритет: {priority}", "warning" if priority == "high" else "default"),
                                badge(item.get("date", "без даты"), "default"),
                            ],
                        ),
                        ft.Text(item.get("short", ""), size=ts(13), color=APP_COLORS["muted"]),
                        ft.Text(f"Кого касается: {item.get('target', 'не указано')}", size=ts(12), color=APP_COLORS["muted"]),
                        ft.Text(f"Что сделать: {item.get('what_to_do') or 'будет уточнено редактором'}", size=ts(12), color=APP_COLORS["muted"]),
                        ft.Text(f"Связанные сценарии: {related_text}", size=ts(12), color=APP_COLORS["muted"]),
                        ft.Text(f"Связанные проблемы: {related_problems_text}", size=ts(12), color=APP_COLORS["muted"]),
                        ft.Row(
                            alignment=ft.MainAxisAlignment.END,
                            spacing=8,
                            wrap=True,
                            controls=[
                                secondary_button(
                                    "Редактировать",
                                    on_click=lambda _, law_id=item["id"]: on_edit_law_update(law_id) if on_edit_law_update else None,
                                    icon=ft.Icons.EDIT_OUTLINED,
                                    height=38,
                                ),
                                _status_toggle_button(
                                    current_status,
                                    on_click=lambda _, law_id=item["id"], status_value=next_status: on_set_law_update_status(law_id, status_value)
                                    if on_set_law_update_status
                                    else None,
                                ),
                                secondary_button(
                                    "Удалить",
                                    on_click=lambda _, law_id=item["id"]: on_delete_law_update(law_id) if on_delete_law_update else None,
                                    icon=ft.Icons.DELETE_OUTLINE,
                                    height=38,
                                ),
                            ],
                        ),
                    ],
                ),
                padding=14,
            )
        )

    return app_card(
        ft.Column(
            spacing=10,
            controls=[ft.Text("Закон-апдейты редактора", size=ts(20), weight=ft.FontWeight.BOLD, color=APP_COLORS["text"]), *rows],
        )
    )


def _problems_list_card(problems: list[dict], on_set_problem_status=None) -> ft.Container:
    rows: list[ft.Control] = []
    if not problems:
        rows.append(ft.Text("Пока нет проблем в базе.", size=ts(14), color=APP_COLORS["muted"]))

    for item in problems:
        current_status = item.get("status", "draft")
        next_status = "draft" if current_status == "published" else "published"
        rows.append(
            app_card(
                ft.Column(
                    spacing=10,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text(
                                    item.get("title", "Без названия"),
                                    size=ts(17),
                                    weight=ft.FontWeight.BOLD,
                                    color=APP_COLORS["text"],
                                    expand=True,
                                ),
                                _status_badge(current_status),
                            ],
                        ),
                        ft.Text(item.get("short_description", ""), size=ts(13), color=APP_COLORS["muted"]),
                        ft.Row(
                            alignment=ft.MainAxisAlignment.END,
                            controls=[
                                _status_toggle_button(
                                    current_status,
                                    on_click=lambda _, problem_id=item["id"], status_value=next_status: on_set_problem_status(problem_id, status_value)
                                    if on_set_problem_status
                                    else None,
                                )
                            ],
                        ),
                    ],
                ),
                padding=14,
            )
        )

    return app_card(
        ft.Column(
            spacing=10,
            controls=[ft.Text("Проблемы", size=ts(20), weight=ft.FontWeight.BOLD, color=APP_COLORS["text"]), *rows],
        )
    )


def _scenarios_list_card(scenarios: list[dict], on_set_scenario_status=None, on_select_scenario=None, on_edit_scenario=None, on_delete_scenario=None) -> ft.Container:
    rows: list[ft.Control] = []
    if not scenarios:
        rows.append(ft.Text("Пока нет сценариев в базе.", size=ts(14), color=APP_COLORS["muted"]))

    for item in scenarios:
        current_status = item.get("status", "draft")
        next_status = "draft" if current_status == "published" else "published"
        rows.append(
            app_card(
                ft.Column(
                    spacing=10,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text(
                                    item.get("title", "Без названия"),
                                    size=ts(17),
                                    weight=ft.FontWeight.BOLD,
                                    color=APP_COLORS["text"],
                                    expand=True,
                                ),
                                _status_badge(current_status),
                            ],
                        ),
                        ft.Row(
                            spacing=8,
                            controls=[
                                badge(item.get("difficulty_level", "medium"), "blue"),
                                badge(item.get("estimated_duration") or "duration: n/a", "default"),
                            ],
                        ),
                        ft.Text(item.get("short_description", ""), size=ts(13), color=APP_COLORS["muted"]),
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            wrap=True,
                            run_spacing=8,
                            controls=[
                                secondary_button(
                                    "Открыть в конструкторе",
                                    on_click=lambda _, scenario_id=item["id"]: on_select_scenario(scenario_id) if on_select_scenario else None,
                                    height=38,
                                ),
                                ft.Row(
                                    spacing=6,
                                    controls=[
                                        secondary_button(
                                            "Редактировать",
                                            icon=ft.Icons.EDIT_OUTLINED,
                                            on_click=lambda _, scenario_id=item["id"]: on_edit_scenario(scenario_id) if on_edit_scenario else None,
                                            height=38,
                                        ),
                                        ft.TextButton(
                                            "Удалить",
                                            icon=ft.Icons.DELETE_OUTLINE,
                                            style=ft.ButtonStyle(color=APP_COLORS["danger"]),
                                            on_click=lambda _, scenario_id=item["id"]: on_delete_scenario(scenario_id) if on_delete_scenario else None,
                                        ),
                                        _status_toggle_button(
                                            current_status,
                                            on_click=lambda _, scenario_id=item["id"], status_value=next_status: on_set_scenario_status(scenario_id, status_value)
                                            if on_set_scenario_status
                                            else None,
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
                padding=14,
            )
        )

    return app_card(
        ft.Column(
            spacing=10,
            controls=[ft.Text("Сценарии", size=ts(20), weight=ft.FontWeight.BOLD, color=APP_COLORS["text"]), *rows],
        )
    )


def _document_create_card(on_create_document=None) -> ft.Container:
    title_f = _field("Название документа *")
    type_f = _field("Тип (паспорт, заявление...)")
    where_f = _field("Где получить")
    validity_f = _field("Срок действия")
    desc_f = _field("Описание", multiline=True, min_lines=2, max_lines=3)
    required_cb = ft.Checkbox(label="Обязательный", value=True)

    def submit(_) -> None:
        if on_create_document:
            on_create_document(
                _text_value(title_f),
                _text_value(type_f),
                _text_value(where_f),
                _text_value(validity_f),
                _text_value(desc_f),
                required_cb.value,
            )
            for f in (title_f, type_f, where_f, validity_f, desc_f):
                f.value = ""
            required_cb.value = True

    return app_card(
        ft.Column(
            spacing=12,
            controls=[
                ft.Text("Добавить документ", size=ts(18), weight=ft.FontWeight.BOLD, color=APP_COLORS["text"]),
                title_f, type_f, where_f, validity_f, desc_f, required_cb,
                primary_button("Добавить", on_click=submit, height=44),
            ],
        )
    )


def _documents_list_card(
    documents: list[dict],
    on_edit_document=None,
    on_delete_document=None,
) -> ft.Container:
    if not documents:
        return app_card(ft.Text("Документов пока нет.", size=ts(13), color=APP_COLORS["muted"]))
    rows: list[ft.Control] = []
    for item in documents:
        rows.append(
            ft.Row(
                spacing=8,
                controls=[
                    ft.Column(
                        spacing=2,
                        expand=True,
                        controls=[
                            ft.Text(item.get("title", "Без названия"), size=ts(14), weight=ft.FontWeight.BOLD, color=APP_COLORS["text"]),
                            ft.Text(
                                " · ".join(filter(None, [item.get("document_type"), item.get("status")])),
                                size=ts(11), color=APP_COLORS["muted"],
                            ),
                        ],
                    ),
                    ft.IconButton(
                        ft.Icons.EDIT_OUTLINED, icon_size=16, tooltip="Редактировать",
                        on_click=lambda _, did=item["id"]: on_edit_document(did) if on_edit_document else None,
                    ),
                    ft.IconButton(
                        ft.Icons.DELETE_OUTLINE, icon_size=16, tooltip="Удалить",
                        icon_color=APP_COLORS["danger"],
                        on_click=lambda _, did=item["id"]: on_delete_document(did) if on_delete_document else None,
                    ),
                ],
            )
        )
    return app_card(
        ft.Column(
            spacing=10,
            controls=[
                ft.Text("Документы", size=ts(18), weight=ft.FontWeight.BOLD, color=APP_COLORS["text"]),
                *rows,
            ],
        )
    )


def _authority_create_card(on_create_authority=None) -> ft.Container:
    title_f = _field("Название организации *")
    type_f = _field("Тип (например: исполком)")
    address_f = _field("Адрес")
    phone_f = _field("Телефон")
    url_f = _field("Сайт")
    hours_f = _field("Часы работы")
    desc_f = _field("Описание", multiline=True, min_lines=2, max_lines=3)

    def submit(_) -> None:
        if on_create_authority:
            on_create_authority(
                _text_value(title_f),
                _text_value(type_f),
                _text_value(address_f),
                _text_value(phone_f),
                _text_value(url_f),
                _text_value(hours_f),
                _text_value(desc_f),
            )
            for f in (title_f, type_f, address_f, phone_f, url_f, hours_f, desc_f):
                f.value = ""

    return app_card(
        ft.Column(
            spacing=12,
            controls=[
                ft.Text("Добавить учреждение", size=ts(18), weight=ft.FontWeight.BOLD, color=APP_COLORS["text"]),
                title_f, type_f, address_f, phone_f, url_f, hours_f, desc_f,
                primary_button("Добавить", on_click=submit, height=44),
            ],
        )
    )


def _authorities_list_card(
    authorities: list[dict],
    on_edit_authority=None,
    on_delete_authority=None,
) -> ft.Container:
    if not authorities:
        return app_card(ft.Text("Учреждений пока нет.", size=ts(13), color=APP_COLORS["muted"]))
    rows: list[ft.Control] = []
    for item in authorities:
        rows.append(
            ft.Row(
                spacing=8,
                controls=[
                    ft.Column(
                        spacing=2,
                        expand=True,
                        controls=[
                            ft.Text(item.get("title", "Без названия"), size=ts(14), weight=ft.FontWeight.BOLD, color=APP_COLORS["text"]),
                            ft.Text(
                                " · ".join(filter(None, [item.get("type"), item.get("address")])),
                                size=ts(11), color=APP_COLORS["muted"],
                            ),
                        ],
                    ),
                    ft.IconButton(
                        ft.Icons.EDIT_OUTLINED, icon_size=16, tooltip="Редактировать",
                        on_click=lambda _, aid=item["id"]: on_edit_authority(aid) if on_edit_authority else None,
                    ),
                    ft.IconButton(
                        ft.Icons.DELETE_OUTLINE, icon_size=16, tooltip="Удалить",
                        icon_color=APP_COLORS["danger"],
                        on_click=lambda _, aid=item["id"]: on_delete_authority(aid) if on_delete_authority else None,
                    ),
                ],
            )
        )
    return app_card(
        ft.Column(
            spacing=10,
            controls=[
                ft.Text("Учреждения", size=ts(18), weight=ft.FontWeight.BOLD, color=APP_COLORS["text"]),
                *rows,
            ],
        )
    )


def _scenario_builder_header(
    scenarios: list[dict],
    selected_scenario_id: int | None,
    scenario_detail: dict | None,
    on_select_scenario=None,
    on_verify_scenario=None,
) -> ft.Control:
    scenario_options = [ft.dropdown.Option(str(item["id"]), item.get("title", f"#{item['id']}")) for item in scenarios]
    selector = ft.Dropdown(
        label="Сценарий для конструктора",
        value=str(selected_scenario_id) if selected_scenario_id is not None else (scenario_options[0].key if scenario_options else None),
        options=scenario_options,
        border_radius=12,
        on_select=(lambda e: on_select_scenario(e.control.value) if on_select_scenario else None),
    )

    controls: list[ft.Control] = [
        ft.Text("Конструктор сценария", size=ts(20), weight=ft.FontWeight.BOLD, color=APP_COLORS["text"]),
        selector,
    ]

    if not scenario_detail:
        controls.append(ft.Text("Выберите сценарий, чтобы добавить этапы и шаги.", size=ts(13), color=APP_COLORS["muted"]))
    else:
        verified_at = scenario_detail.get("content_verified_at")
        verified_by = scenario_detail.get("verified_by", "")
        controls.append(
            ft.Row(
                wrap=True,
                spacing=8,
                run_spacing=8,
                controls=[
                    badge(scenario_detail.get("difficulty_level", "medium"), "blue"),
                    badge(f"Этапов: {len(scenario_detail.get('stages', []))}", "default"),
                    badge(scenario_detail.get("status", "draft"), "success" if scenario_detail.get("status") == "published" else "warning"),
                    badge(
                        "Проверено" if verified_at else "Не проверено",
                        "success" if verified_at else "warning",
                    ),
                ],
            )
        )
        if verified_at:
            checked = str(verified_at)[:10]
            controls.append(
                ft.Text(
                    f"Проверено: {checked}" + (f" · {verified_by}" if verified_by else ""),
                    size=ts(12),
                    color=APP_COLORS["muted"],
                )
            )
        controls.append(
            secondary_button(
                "Отметить проверенным по источникам",
                icon=ft.Icons.VERIFIED_OUTLINED,
                on_click=lambda _, sid=selected_scenario_id: on_verify_scenario(sid) if on_verify_scenario else None,
                height=38,
            )
        )

    return app_card(ft.Column(spacing=12, controls=controls))


def _stage_create_card(
    selected_scenario_id: int | None,
    scenario_detail: dict | None,
    on_create_stage=None,
) -> ft.Control:
    title_field = _field("Название этапа", hint_text="Например: Регистрация рождения")
    description_field = _field("Описание этапа", multiline=True, min_lines=2, max_lines=3)
    stages_count = len((scenario_detail or {}).get("stages", []))
    order_field = _field("Порядок", value=str(stages_count + 1 if stages_count else 1), width=140)
    required_switch = ft.Switch(label="Обязательный этап", value=True)

    def submit(_):
        try:
            order_value = int(order_field.value or "0")
        except ValueError:
            order_value = 0
        if on_create_stage:
            on_create_stage(
                selected_scenario_id,
                title_field.value or "",
                description_field.value or "",
                order_value,
                required_switch.value,
            )

    return app_card(
        ft.Column(
            spacing=12,
            controls=[
                ft.Text("Добавить этап", size=ts(18), weight=ft.FontWeight.BOLD, color=APP_COLORS["text"]),
                title_field,
                description_field,
                ft.Row(spacing=10, run_spacing=8, wrap=True, controls=[order_field, required_switch]),
                primary_button("Добавить этап", on_click=submit, icon=ft.Icons.ADD, expand=True),
            ],
        ),
    )


def _step_create_card(
    selected_scenario_id: int | None,
    scenario_detail: dict | None,
    authorities: list[dict],
    deadlines: list[dict],
    documents: list[dict],
    on_create_step=None,
) -> ft.Control:
    stages = (scenario_detail or {}).get("stages", [])
    stage_options = [ft.dropdown.Option(str(item["id"]), item.get("title", f"Этап #{item['id']}")) for item in stages]
    stage_dropdown = ft.Dropdown(
        label="Этап",
        options=stage_options,
        value=stage_options[0].key if stage_options else None,
        border_radius=12,
    )
    title_field = _field("Название шага", hint_text="Например: Подать заявление")
    description_field = _field("Описание шага", multiline=True, min_lines=2, max_lines=3)
    order_field = _field("Порядок", value="1", width=140)
    action_dropdown = ft.Dropdown(
        label="Тип действия",
        value="info",
        options=[ft.dropdown.Option(value, label) for value, label in ACTION_OPTIONS],
        border_radius=12,
    )
    authority_dropdown = ft.Dropdown(
        label="Организация",
        options=[ft.dropdown.Option("", "Не выбрано")]
        + [ft.dropdown.Option(str(item["id"]), item.get("title", f"#{item['id']}")) for item in authorities],
        value="",
        border_radius=12,
    )
    deadline_dropdown = ft.Dropdown(
        label="Срок",
        options=[ft.dropdown.Option("", "Не выбрано")]
        + [ft.dropdown.Option(str(item["id"]), item.get("title", f"#{item['id']}")) for item in deadlines],
        value="",
        border_radius=12,
    )
    required_switch = ft.Switch(label="Обязательный шаг", value=True)
    document_checks = [ft.Checkbox(label=item.get("title", f"Документ #{item['id']}"), data=item["id"]) for item in documents]

    def submit(_):
        try:
            order_value = int(order_field.value or "0")
        except ValueError:
            order_value = 0
        selected_document_ids = [check.data for check in document_checks if check.value]
        if on_create_step:
            on_create_step(
                selected_scenario_id,
                stage_dropdown.value,
                title_field.value or "",
                description_field.value or "",
                order_value,
                action_dropdown.value or "info",
                authority_dropdown.value or None,
                deadline_dropdown.value or None,
                required_switch.value,
                selected_document_ids,
            )

    return app_card(
        ft.Column(
            spacing=12,
            controls=[
                ft.Text("Добавить шаг", size=ts(18), weight=ft.FontWeight.BOLD, color=APP_COLORS["text"]),
                stage_dropdown,
                title_field,
                description_field,
                ft.Row(spacing=10, run_spacing=8, wrap=True, controls=[order_field, required_switch]),
                action_dropdown,
                authority_dropdown,
                deadline_dropdown,
                ft.Text("Документы шага", size=ts(14), color=APP_COLORS["text"], weight=ft.FontWeight.W_600),
                ft.Container(
                    height=140,
                    padding=ft.Padding(left=8, top=8, right=8, bottom=8),
                    border=border_all(APP_COLORS["border"]),
                    border_radius=12,
                    content=ft.Column(scroll=ft.ScrollMode.AUTO, spacing=4, controls=document_checks or [ft.Text("Нет документов", size=ts(12), color=APP_COLORS["muted"])]),
                ),
                primary_button("Добавить шаг", on_click=submit, icon=ft.Icons.ADD_TASK, expand=True),
            ],
        ),
    )


def _step_dependencies_block(
    step: dict,
    stages: list[dict],
    dependencies: list[dict],
    selected_scenario_id,
    on_add_dependency=None,
    on_delete_dependency=None,
) -> ft.Control:
    step_id = step.get("id")
    step_deps = [d for d in dependencies if d.get("step_id") == step_id]
    all_steps: dict[int, str] = {}
    for stage in stages:
        for s in stage.get("steps", []):
            if s.get("id") != step_id:
                all_steps[s["id"]] = f"{stage.get('title', '?')} → {s.get('title', '?')}"

    dep_controls: list[ft.Control] = []
    for dep in step_deps:
        prereq_id = dep.get("depends_on_step_id")
        prereq_title = all_steps.get(prereq_id, f"Шаг #{prereq_id}")
        dep_controls.append(
            ft.Row(
                spacing=6,
                controls=[
                    ft.Icon(ft.Icons.LOCK_OUTLINE, size=ts(14), color=APP_COLORS["warning"]),
                    ft.Text(prereq_title, size=ts(12), color=APP_COLORS["muted"], expand=True),
                    ft.IconButton(
                        ft.Icons.CLOSE,
                        icon_size=14,
                        tooltip="Удалить зависимость",
                        on_click=lambda _, dep_id=dep["id"]: on_delete_dependency(selected_scenario_id, dep_id) if on_delete_dependency else None,
                    ),
                ],
            )
        )

    if not dep_controls and not on_add_dependency:
        return ft.Container(visible=False)

    body = dep_controls if dep_controls else [ft.Text("нет зависимостей", size=ts(11), color=APP_COLORS["muted"])]
    return ft.Column(
        spacing=4,
        controls=[
            ft.Row(
                spacing=6,
                controls=[
                    ft.Text("Зависит от:", size=ts(12), weight=ft.FontWeight.W_600, color=APP_COLORS["text"]),
                    ft.TextButton(
                        "+ добавить",
                        style=ft.ButtonStyle(color=APP_COLORS["primary"], padding=ft.Padding(0, 0, 0, 0)),
                        on_click=lambda _: on_add_dependency(selected_scenario_id, step_id) if on_add_dependency else None,
                    ),
                ],
            ),
            *body,
        ],
    )


def _related_scenarios_card(
    scenario_detail: dict | None,
    all_scenarios: list[dict],
    selected_scenario_id,
    on_add_related=None,
    on_delete_related=None,
) -> ft.Control:
    if not scenario_detail:
        return ft.Container(visible=False)
    related = (scenario_detail or {}).get("related_scenarios", [])
    current_sid = scenario_detail.get("id")
    related_ids = {r.get("related_scenario_id") for r in related}

    rows: list[ft.Control] = []
    for r in related:
        rows.append(
            ft.Row(
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.LINK, size=ts(14), color=APP_COLORS["primary"]),
                    ft.Text(r.get("related_scenario_title", f"#{r.get('related_scenario_id')}"), size=ts(13), expand=True),
                    ft.Text(r.get("relation_type", ""), size=ts(11), color=APP_COLORS["muted"]),
                    ft.IconButton(
                        ft.Icons.CLOSE,
                        icon_size=14,
                        tooltip="Удалить связь",
                        on_click=lambda _, rid=r["id"]: on_delete_related(selected_scenario_id, rid) if on_delete_related else None,
                    ),
                ],
            )
        )

    available = [s for s in all_scenarios if s.get("id") != current_sid and s.get("id") not in related_ids]

    return app_card(
        ft.Column(
            spacing=10,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text("Связанные сценарии", size=ts(18), weight=ft.FontWeight.BOLD, color=APP_COLORS["text"]),
                        secondary_button(
                            "Добавить связь",
                            icon=ft.Icons.ADD_LINK,
                            on_click=lambda _: on_add_related(selected_scenario_id, available) if on_add_related and available else (
                                None if available else _show_no_available()
                            ),
                            height=36,
                        ),
                    ],
                ),
                *(rows if rows else [ft.Text("Нет связанных сценариев.", size=ts(13), color=APP_COLORS["muted"])]),
            ],
        )
    )


def _show_no_available():
    pass


_SOURCE_TYPE_LABELS = {
    "law": "Право",
    "government_portal": "Гос. портал",
    "ministry": "Министерство",
    "court": "Суд",
    "tax": "Налоговая",
    "registry": "Реестр",
    "other": "Другое",
}

_SOURCEABLE_LABELS = {
    "scenario": "Сценарий",
    "stage": "Этап",
    "step": "Шаг",
}


def _source_references_card(
    scenario_detail: dict | None,
    on_add_source_ref=None,
    on_delete_source_ref=None,
) -> ft.Control:
    if not scenario_detail:
        return ft.Container(visible=False)
    refs = (scenario_detail or {}).get("source_references", [])
    scenario_id = scenario_detail.get("id")

    rows: list[ft.Control] = []
    for ref in refs:
        s_type = _SOURCEABLE_LABELS.get(ref.get("sourceable_type", ""), ref.get("sourceable_type", ""))
        src_type = _SOURCE_TYPE_LABELS.get(ref.get("source_type", ""), ref.get("source_type", ""))
        rows.append(
            ft.Row(
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.LINK, size=ts(14), color=APP_COLORS["accent"]),
                    ft.Column(
                        spacing=1,
                        expand=True,
                        controls=[
                            ft.Text(ref.get("title", ""), size=ts(13), weight=ft.FontWeight.W_500, color=APP_COLORS["text"]),
                            ft.Text(f"{s_type} · {src_type}", size=ts(11), color=APP_COLORS["muted"]),
                        ],
                    ),
                    ft.IconButton(
                        ft.Icons.CLOSE,
                        icon_size=14,
                        tooltip="Удалить источник",
                        on_click=lambda _, rid=ref["id"]: on_delete_source_ref(scenario_id, rid) if on_delete_source_ref else None,
                    ),
                ],
            )
        )

    no_refs = [ft.Text("Нет прикреплённых источников.", size=ts(13), color=APP_COLORS["muted"])]
    return app_card(
        ft.Column(
            spacing=10,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text("Источники права", size=ts(18), weight=ft.FontWeight.BOLD, color=APP_COLORS["text"]),
                        secondary_button(
                            "Добавить источник",
                            icon=ft.Icons.ADD_LINK,
                            on_click=lambda _: on_add_source_ref(scenario_id) if on_add_source_ref else None,
                            height=36,
                        ),
                    ],
                ),
                *(rows if rows else no_refs),
            ],
        )
    )


def _scenario_stage_tree(
    selected_scenario_id: int | None,
    scenario_detail: dict | None,
    on_set_stage_required=None,
    on_set_step_required=None,
    on_edit_stage=None,
    on_delete_stage=None,
    on_edit_step=None,
    on_delete_step=None,
    on_move_stage=None,
    on_move_step=None,
    on_add_dependency=None,
    on_delete_dependency=None,
) -> ft.Control:
    stages = sorted((scenario_detail or {}).get("stages", []), key=lambda s: s.get("order_index", 0))
    if not stages:
        return app_card(ft.Text("Пока нет этапов. Добавьте первый этап через форму выше.", size=ts(13), color=APP_COLORS["muted"]))

    stage_controls: list[ft.Control] = []
    for stage_idx, stage in enumerate(stages):
        steps = sorted(stage.get("steps", []), key=lambda s: s.get("order_index", 0))
        step_controls: list[ft.Control] = []
        for step_idx, step in enumerate(steps):
            step_controls.append(
                ft.Container(
                    padding=ft.Padding(left=12, top=10, right=12, bottom=10),
                    border_radius=12,
                    bgcolor=APP_COLORS["surface_alt"],
                    border=border_all(APP_COLORS["border"]),
                    content=ft.Column(
                        spacing=8,
                        controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text(step.get("title", "Без названия"), size=ts(14), weight=ft.FontWeight.BOLD, color=APP_COLORS["text"], expand=True),
                                    _required_badge(bool(step.get("is_required", True))),
                                ],
                            ),
                            ft.Text(step.get("description", ""), size=ts(12), color=APP_COLORS["muted"]),
                            ft.Row(
                                wrap=True,
                                spacing=6,
                                run_spacing=6,
                                controls=[
                                    badge(step.get("action_type", "info"), "blue"),
                                    badge(f"Порядок: {step.get('order_index', 0)}", "default"),
                                ],
                            ),
                            _step_dependencies_block(
                                step,
                                stages,
                                (scenario_detail or {}).get("dependencies", []),
                                selected_scenario_id,
                                on_add_dependency=on_add_dependency,
                                on_delete_dependency=on_delete_dependency,
                            ),
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                wrap=True,
                                run_spacing=4,
                                spacing=6,
                                controls=[
                                    ft.Row(
                                        spacing=4,
                                        controls=[
                                            ft.IconButton(
                                                ft.Icons.ARROW_UPWARD,
                                                tooltip="Переместить выше",
                                                icon_size=18,
                                                disabled=step_idx == 0,
                                                on_click=lambda _, step_id=step["id"]: on_move_step(selected_scenario_id, step_id, "up") if on_move_step else None,
                                            ),
                                            ft.IconButton(
                                                ft.Icons.ARROW_DOWNWARD,
                                                tooltip="Переместить ниже",
                                                icon_size=18,
                                                disabled=step_idx == len(steps) - 1,
                                                on_click=lambda _, step_id=step["id"]: on_move_step(selected_scenario_id, step_id, "down") if on_move_step else None,
                                            ),
                                        ],
                                    ),
                                    ft.Row(
                                        spacing=6,
                                        controls=[
                                            secondary_button(
                                                "Сделать необязательным" if step.get("is_required", True) else "Сделать обязательным",
                                                on_click=lambda _, step_id=step["id"], required=not bool(step.get("is_required", True)): on_set_step_required(selected_scenario_id, step_id, required)
                                                if on_set_step_required
                                                else None,
                                                height=34,
                                            ),
                                            secondary_button(
                                                "Редактировать",
                                                icon=ft.Icons.EDIT_OUTLINED,
                                                on_click=lambda _, step_id=step["id"]: on_edit_step(selected_scenario_id, step_id) if on_edit_step else None,
                                                height=34,
                                            ),
                                            ft.TextButton(
                                                "Удалить",
                                                icon=ft.Icons.DELETE_OUTLINE,
                                                style=ft.ButtonStyle(color=APP_COLORS["danger"]),
                                                on_click=lambda _, step_id=step["id"]: on_delete_step(selected_scenario_id, step_id) if on_delete_step else None,
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),
                )
            )

        stage_controls.append(
            app_card(
                ft.Column(
                    spacing=10,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Column(
                                    spacing=4,
                                    controls=[
                                        ft.Text(stage.get("title", "Без названия"), size=ts(17), weight=ft.FontWeight.BOLD, color=APP_COLORS["text"]),
                                        ft.Text(stage.get("description", ""), size=ts(13), color=APP_COLORS["muted"]),
                                    ],
                                    expand=True,
                                ),
                                _required_badge(bool(stage.get("is_required", True))),
                            ],
                        ),
                        ft.Row(
                            wrap=True,
                            spacing=8,
                            controls=[
                                badge(f"Порядок: {stage.get('order_index', 0)}", "default"),
                                badge(f"Шагов: {len(steps)}", "blue"),
                            ],
                        ),
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            wrap=True,
                            run_spacing=4,
                            spacing=6,
                            controls=[
                                ft.Row(
                                    spacing=4,
                                    controls=[
                                        ft.IconButton(
                                            ft.Icons.ARROW_UPWARD,
                                            tooltip="Переместить выше",
                                            icon_size=18,
                                            disabled=stage_idx == 0,
                                            on_click=lambda _, stage_id=stage["id"]: on_move_stage(selected_scenario_id, stage_id, "up") if on_move_stage else None,
                                        ),
                                        ft.IconButton(
                                            ft.Icons.ARROW_DOWNWARD,
                                            tooltip="Переместить ниже",
                                            icon_size=18,
                                            disabled=stage_idx == len(stages) - 1,
                                            on_click=lambda _, stage_id=stage["id"]: on_move_stage(selected_scenario_id, stage_id, "down") if on_move_stage else None,
                                        ),
                                    ],
                                ),
                                ft.Row(
                                    spacing=6,
                                    controls=[
                                        secondary_button(
                                            "Сделать необязательным" if stage.get("is_required", True) else "Сделать обязательным",
                                            on_click=lambda _, stage_id=stage["id"], required=not bool(stage.get("is_required", True)): on_set_stage_required(selected_scenario_id, stage_id, required)
                                            if on_set_stage_required
                                            else None,
                                            height=34,
                                        ),
                                        secondary_button(
                                            "Редактировать",
                                            icon=ft.Icons.EDIT_OUTLINED,
                                            on_click=lambda _, stage_id=stage["id"]: on_edit_stage(selected_scenario_id, stage_id) if on_edit_stage else None,
                                            height=34,
                                        ),
                                        ft.TextButton(
                                            "Удалить",
                                            icon=ft.Icons.DELETE_OUTLINE,
                                            style=ft.ButtonStyle(color=APP_COLORS["danger"]),
                                            on_click=lambda _, stage_id=stage["id"]: on_delete_stage(selected_scenario_id, stage_id) if on_delete_stage else None,
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        ft.Column(spacing=8, controls=step_controls or [ft.Text("Шаги пока не добавлены.", size=ts(13), color=APP_COLORS["muted"])]),
                    ],
                ),
                padding=14,
            )
        )

    return app_card(
        ft.Column(
            spacing=10,
            controls=[
                ft.Text("Этапы и шаги сценария", size=ts(18), weight=ft.FontWeight.BOLD, color=APP_COLORS["text"]),
                *stage_controls,
            ],
        )
    )


# ============================================================
# TAB NAVIGATION
# ============================================================

EDITOR_TABS = [
    ("problems",    "Проблемы",     ft.Icons.HELP_OUTLINE),
    ("scenarios",   "Сценарии",     ft.Icons.ROUTE_OUTLINED),
    ("law_updates", "Закон-апдейты", ft.Icons.BALANCE_OUTLINED),
    ("documents",   "Документы",    ft.Icons.DESCRIPTION_OUTLINED),
    ("authorities", "Учреждения",   ft.Icons.ACCOUNT_BALANCE_OUTLINED),
    ("sources",     "Источники",    ft.Icons.LINK_OUTLINED),
]

ADMIN_ONLY_TABS = [
    ("users",         "Пользователи",  ft.Icons.PEOPLE_OUTLINE),
    ("directories",   "Справочники",   ft.Icons.MENU_BOOK_OUTLINED),
    ("notifications", "Уведомления",   ft.Icons.NOTIFICATIONS_NONE_OUTLINED),
    ("audit",         "Аудит",         ft.Icons.HISTORY_OUTLINED),
]

VALID_EDITOR_TABS  = {t[0] for t in EDITOR_TABS}
VALID_ADMIN_TABS   = {t[0] for t in ADMIN_ONLY_TABS}


def _tab_nav(tabs: list, current_tab: str, on_tab_change, label: str = "") -> ft.Column:
    """Горизонтальная панель вкладок с опциональным заголовком-разделителем."""
    chips = [
        ft.Container(
            ink=True,
            border_radius=12,
            padding=padding_symmetric(horizontal=14, vertical=8),
            bgcolor=APP_COLORS["primary"] if key == current_tab else APP_COLORS["surface_alt"],
            border=border_all(APP_COLORS["primary"] if key == current_tab else APP_COLORS["border_soft"]),
            on_click=lambda _, k=key: on_tab_change(k) if on_tab_change else None,
            content=ft.Row(
                spacing=6,
                tight=True,
                controls=[
                    ft.Icon(icon, size=ts(14), color="#FFFFFF" if key == current_tab else APP_COLORS["muted"]),
                    ft.Text(
                        lbl, size=ts(13), weight=ft.FontWeight.W_700,
                        color="#FFFFFF" if key == current_tab else APP_COLORS["text"],
                    ),
                ],
            ),
        )
        for key, lbl, icon in tabs
    ]
    controls: list[ft.Control] = []
    if label:
        controls.append(
            ft.Text(label, size=ts(11), weight=ft.FontWeight.W_700,
                    color=APP_COLORS["muted"],
                    style=ft.TextStyle(letter_spacing=0.8))
        )
    controls.append(ft.Row(wrap=True, spacing=6, run_spacing=6, controls=chips))
    return ft.Column(spacing=6, controls=controls)


# ============================================================
# ADMIN-ONLY SECTIONS
# ============================================================

_BELARUS_REGIONS = [
    "Брестская область", "Витебская область", "Гомельская область",
    "Гродненская область", "Минск (город)", "Минская область", "Могилёвская область",
]

_DEFAULT_CATEGORIES = [
    {"id": "docs",     "name": "Документы",   "icon": "ARTICLE_OUTLINED"},
    {"id": "home",     "name": "ЖКХ",          "icon": "HOME_WORK_OUTLINED"},
    {"id": "taxes",    "name": "Налоги",        "icon": "ACCOUNT_BALANCE_OUTLINED"},
    {"id": "family",   "name": "Семья",         "icon": "FAMILY_RESTROOM_OUTLINED"},
    {"id": "work",     "name": "Работа",        "icon": "WORK_OUTLINE"},
    {"id": "health",   "name": "Здоровье",      "icon": "MEDICAL_SERVICES_OUTLINED"},
    {"id": "auto",     "name": "Авто",          "icon": "DIRECTIONS_CAR_OUTLINED"},
    {"id": "business", "name": "Бизнес/ИП",     "icon": "BUSINESS_CENTER_OUTLINED"},
]

_DEFAULT_NOTIFICATION_RULES = [
    {
        "id": "task_due", "title": "Срок задачи",
        "desc": "Напомнить, когда до срока задачи ≤ N дней",
        "type": "task", "enabled": True, "threshold_days": 7,
    },
    {
        "id": "doc_expiry", "title": "Истечение документа",
        "desc": "Напомнить, когда до истечения документа ≤ N дней",
        "type": "document", "enabled": True, "threshold_days": 30,
    },
    {
        "id": "utility_payment", "title": "Оплата ЖКХ",
        "desc": "Напомнить о предстоящих платежах ЖКХ",
        "type": "utility", "enabled": True, "threshold_days": 30,
    },
    {
        "id": "tax_deadline", "title": "Налоговый срок",
        "desc": "Напомнить о налоговых обязательствах",
        "type": "tax", "enabled": True, "threshold_days": 30,
    },
    {
        "id": "law_high", "title": "Важный закон-апдейт",
        "desc": "Уведомить о законах с высоким приоритетом",
        "type": "law", "enabled": True, "threshold_days": None,
    },
    {
        "id": "law_profile", "title": "Персональный закон-апдейт",
        "desc": "Уведомить, если теги закона совпадают с профилем пользователя",
        "type": "law", "enabled": True, "threshold_days": None,
    },
]

_RULE_TYPE_TONE = {
    "task": "blue", "document": "purple",
    "utility": "cyan", "tax": "orange", "law": "green",
}


def _build_users_tab(
    state: dict,
    on_update_user_role=None,
    on_toggle_user_status=None,
    on_create_admin_user=None,
) -> ft.Control:
    roles = state.get("roles", [])
    users = state.get("admin_users", [])
    role_options = [ft.dropdown.Option(r["id"], r["title"]) for r in roles if r["id"] != "citizen"]

    def _user_row(user: dict) -> ft.Container:
        uid  = user.get("id", "")
        active = user.get("status", "active") == "active"
        return app_card(
            ft.Row(
                spacing=14,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    icon_circle(
                        ft.Icons.PERSON_OUTLINE,
                        color=APP_COLORS["primary"] if active else APP_COLORS["muted"],
                        bgcolor=APP_COLORS["primary_light"] if active else APP_COLORS["surface_alt"],
                        size=42,
                    ),
                    ft.Column(
                        spacing=2,
                        expand=True,
                        controls=[
                            ft.Text(user.get("name", "—"), size=ts(15), weight=ft.FontWeight.W_800,
                                    color=APP_COLORS["text"]),
                            ft.Text(user.get("email", ""), size=ts(12), color=APP_COLORS["muted"]),
                        ],
                    ),
                    ft.Dropdown(
                        value=user.get("role_id", "content_editor"),
                        options=role_options,
                        border_radius=10,
                        dense=True,
                        width=220,
                        on_select=lambda e, _uid=uid: on_update_user_role(_uid, e.control.value)
                        if on_update_user_role else None,
                    ),
                    ft.Container(
                        ink=True,
                        border_radius=10,
                        padding=padding_symmetric(horizontal=12, vertical=7),
                        bgcolor=APP_COLORS["warning_light"] if active else APP_COLORS["primary_light"],
                        border=border_all(
                            APP_COLORS["warning"] if active else APP_COLORS["primary"]
                        ),
                        on_click=lambda _, _uid=uid: on_toggle_user_status(_uid)
                        if on_toggle_user_status else None,
                        content=ft.Text(
                            "Деактивировать" if active else "Активировать",
                            size=ts(12),
                            weight=ft.FontWeight.W_700,
                            color=APP_COLORS["warning"] if active else APP_COLORS["primary"],
                        ),
                    ),
                    badge("активен" if active else "отключён",
                          "success" if active else "default"),
                ],
            ),
            padding=14,
        )

    # New user form
    name_field  = ft.TextField(label="Имя", border_radius=10, dense=True, expand=True)
    email_field = ft.TextField(label="Email", border_radius=10, dense=True, expand=True)
    role_dd     = ft.Dropdown(
        label="Роль",
        value="content_editor",
        options=role_options,
        border_radius=10,
        dense=True,
        width=210,
    )

    def _do_create(_):
        if on_create_admin_user:
            on_create_admin_user(
                name_field.value or "",
                email_field.value or "",
                role_dd.value or "content_editor",
            )

    create_form = app_card(
        ft.Column(
            spacing=12,
            controls=[
                ft.Row(
                    spacing=8,
                    controls=[
                        ft.Icon(ft.Icons.PERSON_ADD_OUTLINED, size=ts(18), color=APP_COLORS["primary"]),
                        ft.Text("Добавить пользователя", size=ts(15), weight=ft.FontWeight.BOLD,
                                color=APP_COLORS["text"]),
                    ],
                ),
                ft.Row(spacing=10, controls=[name_field, email_field, role_dd]),
                primary_button("Создать", on_click=_do_create, height=40, width=140),
            ],
        ),
        padding=18,
        border_color=APP_COLORS["primary"],
        bgcolor=APP_COLORS["primary_light"],
    )

    user_rows = [_user_row(u) for u in users] or [
        ft.Text("Пользователей пока нет.", size=ts(13), color=APP_COLORS["muted"])
    ]

    return ft.Column(
        spacing=16,
        controls=[
            ft.Row(
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.PEOPLE_OUTLINE, size=ts(20), color=APP_COLORS["primary"]),
                    ft.Text("Пользователи и роли", size=ts(20), weight=ft.FontWeight.BOLD,
                            color=APP_COLORS["text"]),
                    ft.Text(f"({len(users)})", size=ts(14), color=APP_COLORS["muted"]),
                ],
            ),
            create_form,
            ft.Column(spacing=10, controls=user_rows),
        ],
    )


def _build_directories_tab(
    state: dict,
    on_add_category=None,
    on_delete_category=None,
) -> ft.Control:
    categories = state.get("categories", _DEFAULT_CATEGORIES)
    new_cat_name = ft.TextField(label="Название категории", border_radius=10,
                                dense=True, expand=True)
    new_cat_id   = ft.TextField(label="ID (eng)", border_radius=10, dense=True, width=140)

    def _do_add(_):
        if on_add_category:
            on_add_category(new_cat_id.value or "", new_cat_name.value or "")

    cat_rows = [
        ft.Container(
            border_radius=12,
            bgcolor=APP_COLORS["surface_alt"],
            border=border_all(APP_COLORS["border_soft"]),
            padding=padding_symmetric(horizontal=14, vertical=10),
            content=ft.Row(
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(ft.Icons.FOLDER_OUTLINED, size=ts(18), color=APP_COLORS["primary"]),
                    ft.Text(cat["name"], size=ts(14), weight=ft.FontWeight.W_700,
                            color=APP_COLORS["text"], expand=True),
                    ft.Text(cat["id"], size=ts(12), color=APP_COLORS["muted"]),
                    ft.IconButton(
                        ft.Icons.DELETE_OUTLINE,
                        icon_color=APP_COLORS["danger"],
                        icon_size=18,
                        on_click=lambda _, cid=cat["id"]: on_delete_category(cid)
                        if on_delete_category else None,
                        style=ft.ButtonStyle(padding=ft.Padding(left=4, top=4, right=4, bottom=4)),
                    ),
                ],
            ),
        )
        for cat in categories
    ]

    regions_rows = [
        ft.Container(
            border_radius=10,
            bgcolor=APP_COLORS["surface_alt"],
            border=border_all(APP_COLORS["border_soft"]),
            padding=padding_symmetric(horizontal=14, vertical=9),
            content=ft.Row(
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.PLACE_OUTLINED, size=ts(16), color=APP_COLORS["muted"]),
                    ft.Text(region, size=ts(13), weight=ft.FontWeight.W_600, color=APP_COLORS["text"]),
                ],
            ),
        )
        for region in _BELARUS_REGIONS
    ]

    tags_list = list({
        tag
        for u in state.get("admin_users", [])
        for tag in (u.get("interest_tags") or [])
    }) or ["семья", "ip", "housing_owner", "has_children", "utility"]

    tags_chips = ft.Row(
        wrap=True, spacing=8, run_spacing=8,
        controls=[
            ft.Container(
                border_radius=999,
                bgcolor=APP_COLORS["primary_light"],
                border=border_all(APP_COLORS["primary"]),
                padding=padding_symmetric(horizontal=12, vertical=5),
                content=ft.Text(tag, size=ts(12), weight=ft.FontWeight.W_700,
                                color=APP_COLORS["primary"]),
            )
            for tag in tags_list
        ],
    )

    sections = [
        app_card(
            ft.Column(
                spacing=12,
                controls=[
                    ft.Row(
                        spacing=8,
                        controls=[
                            ft.Icon(ft.Icons.CATEGORY_OUTLINED, size=ts(18), color=APP_COLORS["primary"]),
                            ft.Text("Категории проблем и сценариев", size=ts(16),
                                    weight=ft.FontWeight.BOLD, color=APP_COLORS["text"]),
                        ],
                    ),
                    ft.Row(spacing=8, controls=[new_cat_name, new_cat_id,
                                                primary_button("Добавить", on_click=_do_add,
                                                               height=40, width=110)]),
                    ft.Column(spacing=6, controls=cat_rows),
                ],
            ),
            padding=18,
        ),
        app_card(
            ft.Column(
                spacing=12,
                controls=[
                    ft.Row(
                        spacing=8,
                        controls=[
                            ft.Icon(ft.Icons.MAP_OUTLINED, size=ts(18), color=APP_COLORS["primary"]),
                            ft.Text("Регионы Беларуси", size=ts(16), weight=ft.FontWeight.BOLD,
                                    color=APP_COLORS["text"]),
                            badge("только просмотр", "default"),
                        ],
                    ),
                    ft.Column(spacing=6, controls=regions_rows),
                ],
            ),
            padding=18,
        ),
        app_card(
            ft.Column(
                spacing=10,
                controls=[
                    ft.Row(
                        spacing=8,
                        controls=[
                            ft.Icon(ft.Icons.LABEL_OUTLINE, size=ts(18), color=APP_COLORS["primary"]),
                            ft.Text("Теги интересов / релевантности", size=ts(16),
                                    weight=ft.FontWeight.BOLD, color=APP_COLORS["text"]),
                        ],
                    ),
                    ft.Text("Теги из профилей пользователей:", size=ts(12),
                            color=APP_COLORS["muted"]),
                    tags_chips,
                ],
            ),
            padding=18,
        ),
    ]

    return ft.Column(spacing=16, controls=[
        ft.Row(
            spacing=8,
            controls=[
                ft.Icon(ft.Icons.MENU_BOOK_OUTLINED, size=ts(20), color=APP_COLORS["primary"]),
                ft.Text("Справочники", size=ts(20), weight=ft.FontWeight.BOLD,
                        color=APP_COLORS["text"]),
            ],
        ),
        *sections,
    ])


def _build_notifications_tab(
    state: dict,
    on_toggle_rule=None,
    on_edit_rule_days=None,
) -> ft.Control:
    rules = state.get("notification_rules", _DEFAULT_NOTIFICATION_RULES)

    def _rule_row(rule: dict) -> ft.Container:
        tone    = _RULE_TYPE_TONE.get(rule.get("type", "task"), "blue")
        enabled = rule.get("enabled", True)
        days    = rule.get("threshold_days")

        day_row: list[ft.Control] = []
        if days is not None:
            day_field = ft.TextField(
                value=str(days),
                width=64,
                dense=True,
                border_radius=8,
                suffix=ft.Text("дн.", size=ts(12), color=APP_COLORS["muted"]),
                on_submit=lambda e, rid=rule["id"]: on_edit_rule_days(rid, e.control.value)
                if on_edit_rule_days else None,
                keyboard_type=ft.KeyboardType.NUMBER,
            )
            day_row = [
                ft.Text("Порог:", size=ts(12), color=APP_COLORS["muted"]),
                day_field,
            ]

        return app_card(
            ft.Row(
                spacing=14,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    icon_circle(
                        ft.Icons.NOTIFICATIONS_OUTLINED,
                        color=APP_COLORS[tone],
                        bgcolor=APP_COLORS["surface_alt"],
                        size=40,
                    ),
                    ft.Column(
                        spacing=3,
                        expand=True,
                        controls=[
                            ft.Text(rule.get("title", "Правило"), size=ts(14),
                                    weight=ft.FontWeight.W_800, color=APP_COLORS["text"]),
                            ft.Text(rule.get("desc", ""), size=ts(12),
                                    color=APP_COLORS["muted"], max_lines=2),
                            ft.Row(spacing=6, controls=day_row) if day_row else ft.Container(),
                        ],
                    ),
                    badge(rule.get("type", ""), tone),
                    ft.Switch(
                        value=enabled,
                        active_color=APP_COLORS["primary"],
                        on_change=lambda e, rid=rule["id"]: on_toggle_rule(rid, e.control.value)
                        if on_toggle_rule else None,
                    ),
                ],
            ),
            padding=14,
        )

    return ft.Column(
        spacing=16,
        controls=[
            ft.Row(
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.NOTIFICATIONS_NONE_OUTLINED, size=ts(20),
                            color=APP_COLORS["primary"]),
                    ft.Text("Правила уведомлений", size=ts(20), weight=ft.FontWeight.BOLD,
                            color=APP_COLORS["text"]),
                ],
            ),
            app_card(
                ft.Column(
                    spacing=6,
                    controls=[
                        ft.Row(
                            spacing=8,
                            controls=[
                                ft.Icon(ft.Icons.INFO_OUTLINE, size=ts(16),
                                        color=APP_COLORS["primary"]),
                                ft.Text(
                                    "Включите / выключите каждый тип уведомлений. "
                                    "Порог (в днях) — за сколько дней до события "
                                    "отправлять напоминание.",
                                    size=ts(13), color=APP_COLORS["muted"], expand=True,
                                ),
                            ],
                        ),
                    ],
                ),
                padding=14,
                bgcolor=APP_COLORS["primary_light"],
                border_color=APP_COLORS["primary"],
            ),
            ft.Column(spacing=10, controls=[_rule_row(r) for r in rules]),
        ],
    )


def _build_audit_tab(state: dict) -> ft.Control:
    return ft.Column(
        spacing=16,
        controls=[
            ft.Row(
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.HISTORY_OUTLINED, size=ts(20), color=APP_COLORS["primary"]),
                    ft.Text("Аудит действий", size=ts(20), weight=ft.FontWeight.BOLD,
                            color=APP_COLORS["text"]),
                ],
            ),
            _full_audit_log_card(state.get("audit_logs", [])),
        ],
    )


# ============================================================
# TAB CONTENT DISPATCHER
# ============================================================

def _tab_body(tab: str, state: dict, **cb) -> ft.Control:
    """Отдаёт нужный контент для выбранной вкладки."""
    problems   = state.get("problems",   [])
    scenarios  = state.get("scenarios",  [])
    documents  = state.get("documents",  [])
    authorities= state.get("authorities",[])
    law_updates= state.get("law_updates",[])
    sources    = state.get("official_sources", state.get("sources", []))
    sel_id     = state.get("selected_scenario_id")
    detail     = state.get("scenario_detail")

    if tab == "problems":
        return ft.Column(spacing=16, controls=[
            ft.ResponsiveRow(columns=12, spacing=12, run_spacing=12, controls=[
                ft.Container(col={"xs": 12, "sm": 5},
                             content=_problem_create_card(cb.get("on_create_problem"))),
                ft.Container(col={"xs": 12, "sm": 7},
                             content=_problems_list_card(problems,
                                                         cb.get("on_set_problem_status"))),
            ]),
        ])

    if tab == "scenarios":
        return ft.Column(spacing=16, controls=[
            ft.ResponsiveRow(columns=12, spacing=12, run_spacing=12, controls=[
                ft.Container(col={"xs": 12, "sm": 5},
                             content=_scenario_create_card(problems,
                                                           cb.get("on_create_scenario"))),
                ft.Container(col={"xs": 12, "sm": 7},
                             content=_scenarios_list_card(
                                 scenarios,
                                 cb.get("on_set_scenario_status"),
                                 cb.get("on_select_scenario"),
                                 cb.get("on_edit_scenario"),
                                 cb.get("on_delete_scenario"),
                             )),
            ]),
            _scenario_builder_header(scenarios, sel_id, detail,
                                     cb.get("on_select_scenario"),
                                     cb.get("on_verify_scenario")),
            ft.ResponsiveRow(columns=12, spacing=12, run_spacing=12, controls=[
                ft.Container(col={"xs": 12, "sm": 6},
                             content=_stage_create_card(sel_id, detail,
                                                        cb.get("on_create_stage"))),
                ft.Container(col={"xs": 12, "sm": 6},
                             content=_step_create_card(sel_id, detail, authorities,
                                                       [], documents,
                                                       cb.get("on_create_step"))),
            ]),
            _scenario_stage_tree(
                sel_id, detail,
                cb.get("on_set_stage_required"), cb.get("on_set_step_required"),
                cb.get("on_edit_stage"),   cb.get("on_delete_stage"),
                cb.get("on_edit_step"),    cb.get("on_delete_step"),
                cb.get("on_move_stage"),   cb.get("on_move_step"),
                cb.get("on_add_dependency"), cb.get("on_delete_dependency"),
            ),
            _related_scenarios_card(detail, scenarios, sel_id,
                                    cb.get("on_add_related"), cb.get("on_delete_related")),
            _source_references_card(detail, cb.get("on_add_source_ref"),
                                    cb.get("on_delete_source_ref")),
        ])

    if tab == "law_updates":
        return ft.Column(spacing=16, controls=[
            ft.ResponsiveRow(columns=12, spacing=12, run_spacing=12, controls=[
                ft.Container(col={"xs": 12, "sm": 5},
                             content=_law_update_create_card(cb.get("on_create_law_update"))),
                ft.Container(col={"xs": 12, "sm": 7},
                             content=_law_updates_list_card(
                                 law_updates,
                                 cb.get("on_set_law_update_status"),
                                 cb.get("on_delete_law_update"),
                                 cb.get("on_edit_law_update"),
                             )),
            ]),
        ])

    if tab == "documents":
        return ft.Column(spacing=16, controls=[
            ft.ResponsiveRow(columns=12, spacing=12, run_spacing=12, controls=[
                ft.Container(col={"xs": 12, "sm": 5},
                             content=_document_create_card(cb.get("on_create_document"))),
                ft.Container(col={"xs": 12, "sm": 7},
                             content=_documents_list_card(documents,
                                                          cb.get("on_edit_document"),
                                                          cb.get("on_delete_document"))),
            ]),
        ])

    if tab == "authorities":
        return ft.Column(spacing=16, controls=[
            ft.ResponsiveRow(columns=12, spacing=12, run_spacing=12, controls=[
                ft.Container(col={"xs": 12, "sm": 5},
                             content=_authority_create_card(cb.get("on_create_authority"))),
                ft.Container(col={"xs": 12, "sm": 7},
                             content=_authorities_list_card(authorities,
                                                            cb.get("on_edit_authority"),
                                                            cb.get("on_delete_authority"))),
            ]),
        ])

    if tab == "sources":
        return ft.Column(spacing=16, controls=[
            ft.ResponsiveRow(columns=12, spacing=12, run_spacing=12, controls=[
                ft.Container(col={"xs": 12, "sm": 5},
                             content=_source_create_card(cb.get("on_create_source"))),
                ft.Container(col={"xs": 12, "sm": 7},
                             content=_sources_list_card(sources,
                                                        cb.get("on_edit_source"),
                                                        cb.get("on_delete_source"),
                                                        cb.get("on_set_source_status"))),
            ]),
        ])

    # Admin-only tabs
    if tab == "users":
        return _build_users_tab(
            state,
            cb.get("on_update_user_role"),
            cb.get("on_toggle_user_status"),
            cb.get("on_create_admin_user"),
        )

    if tab == "directories":
        return _build_directories_tab(
            state,
            cb.get("on_add_category"),
            cb.get("on_delete_category"),
        )

    if tab == "notifications":
        return _build_notifications_tab(
            state,
            cb.get("on_toggle_notification_rule"),
            cb.get("on_edit_rule_days"),
        )

    if tab == "audit":
        return _build_audit_tab(state)

    # Fallback
    return ft.Text("Раздел не найден.", size=ts(14), color=APP_COLORS["muted"])


def _content(
    desktop: bool,
    state: dict,
    on_refresh=None,
    on_open_workspace=None,
    on_select_admin_role=None,
    on_tab_change=None,
    # content editor callbacks
    on_create_problem=None,
    on_set_problem_status=None,
    on_create_scenario=None,
    on_set_scenario_status=None,
    on_edit_scenario=None,
    on_delete_scenario=None,
    on_create_law_update=None,
    on_set_law_update_status=None,
    on_delete_law_update=None,
    on_edit_law_update=None,
    on_create_source=None,
    on_edit_source=None,
    on_delete_source=None,
    on_set_source_status=None,
    on_select_scenario=None,
    on_verify_scenario=None,
    on_create_stage=None,
    on_create_step=None,
    on_set_stage_required=None,
    on_set_step_required=None,
    on_edit_stage=None,
    on_delete_stage=None,
    on_edit_step=None,
    on_delete_step=None,
    on_move_stage=None,
    on_move_step=None,
    on_add_dependency=None,
    on_delete_dependency=None,
    on_add_related=None,
    on_delete_related=None,
    on_add_source_ref=None,
    on_delete_source_ref=None,
    on_create_authority=None,
    on_edit_authority=None,
    on_delete_authority=None,
    on_create_document=None,
    on_edit_document=None,
    on_delete_document=None,
    # platform_admin callbacks
    on_update_user_role=None,
    on_toggle_user_status=None,
    on_create_admin_user=None,
    on_add_category=None,
    on_delete_category=None,
    on_toggle_notification_rule=None,
    on_edit_rule_days=None,
) -> ft.Column:
    current_role = state.get("current_role", "content_editor")
    current_tab  = state.get("current_tab", "problems")

    # ── Заголовок страницы ────────────────────────────────────────────────
    role_label = {
        "platform_admin": "Администратор площадки",
        "content_editor":  "Редактор контента",
    }.get(current_role, "Гражданин")
    role_tone = "blue" if current_role == "platform_admin" else "cyan"

    header = ft.Column(
        spacing=6,
        controls=[
            ft.Row(
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(ft.Icons.ADMIN_PANEL_SETTINGS_OUTLINED, size=ts(30),
                            color=APP_COLORS["primary"]),
                    ft.Column(
                        spacing=2,
                        expand=True,
                        controls=[
                            ft.Text("Панель управления", size=ts(30) if desktop else 24,
                                    weight=ft.FontWeight.BOLD, color=APP_COLORS["text"]),
                            ft.Text("Белпомощник · административный интерфейс",
                                    size=ts(13), color=APP_COLORS["muted"]),
                        ],
                    ),
                    badge(role_label, role_tone),
                ],
            ),
        ],
    )

    # ── Заблокированный доступ для гражданина ────────────────────────────
    if current_role == "citizen":
        return ft.Column(
            spacing=18,
            controls=[
                header,
                _role_access_card(state, on_select_admin_role),
                app_card(
                    ft.Column(
                        spacing=8,
                        controls=[
                            ft.Row(
                                spacing=8,
                                controls=[
                                    ft.Icon(ft.Icons.LOCK_OUTLINED, size=ts(22),
                                            color=APP_COLORS["warning"]),
                                    ft.Text("Доступ закрыт", size=ts(18),
                                            weight=ft.FontWeight.BOLD,
                                            color=APP_COLORS["text"]),
                                ],
                            ),
                            ft.Text(
                                "Роль «Гражданин» не имеет доступа к административным функциям. "
                                "Создание сценариев, публикация законов и управление пользователями "
                                "доступны редактору или администратору площадки.",
                                size=ts(14), color=APP_COLORS["muted"],
                            ),
                        ],
                    ),
                    border_color=APP_COLORS["warning"],
                    bgcolor=APP_COLORS["warning_light"],
                    padding=20,
                ),
            ],
        )

    # ── Собираем набор вкладок по роли ───────────────────────────────────
    if current_role == "platform_admin":
        all_tabs = EDITOR_TABS + ADMIN_ONLY_TABS
    else:
        all_tabs = EDITOR_TABS
        if current_tab not in VALID_EDITOR_TABS:
            current_tab = "problems"

    # ── Верхняя строка: статус API + переключатель роли ──────────────────
    top_bar = ft.ResponsiveRow(
        columns=12,
        spacing=12,
        run_spacing=12,
        controls=[
            ft.Container(col={"xs": 12, "md": 8},
                         content=_api_status_card(state, on_refresh)),
            ft.Container(col={"xs": 12, "md": 4},
                         content=_role_access_card(state, on_select_admin_role)),
        ],
    )

    # ── Workspace-банер (только для редактора/контент) ────────────────────
    workspace_banner = ft.Container(
        content=ft.Row(
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(ft.Icons.WORKSPACES_OUTLINE, size=ts(20), color=APP_COLORS["primary"]),
                ft.Column(
                    spacing=2, expand=True,
                    controls=[
                        ft.Text("Workspace — inline-редактор контента",
                                size=ts(13), weight=ft.FontWeight.W_700, color=APP_COLORS["text"]),
                        ft.Text("Дерево сценариев/шагов без перезагрузки страницы.",
                                size=ts(12), color=APP_COLORS["muted"]),
                    ],
                ),
                ft.FilledButton("Открыть", icon=ft.Icons.OPEN_IN_NEW,
                                on_click=on_open_workspace),
            ],
        ),
        padding=padding_symmetric(horizontal=16, vertical=12),
        border_radius=12,
        bgcolor=APP_COLORS["primary_light"],
        border=border_all(APP_COLORS["primary"], 1),
    )

    # ── Разделители вкладок: контент / администрирование ─────────────────
    if current_role == "platform_admin":
        editor_nav = _tab_nav(EDITOR_TABS, current_tab, on_tab_change,
                              label="РЕДАКТОР КОНТЕНТА")
        admin_nav  = _tab_nav(ADMIN_ONLY_TABS, current_tab, on_tab_change,
                              label="АДМИНИСТРИРОВАНИЕ")
        tabs_block = ft.Column(
            spacing=8,
            controls=[
                app_card(
                    ft.Column(spacing=12, controls=[editor_nav, admin_nav]),
                    padding=16,
                ),
            ],
        )
    else:
        tabs_block = app_card(
            _tab_nav(EDITOR_TABS, current_tab, on_tab_change),
            padding=16,
        )

    # ── Содержимое активной вкладки ───────────────────────────────────────
    cb = dict(
        on_create_problem=on_create_problem,
        on_set_problem_status=on_set_problem_status,
        on_create_scenario=on_create_scenario,
        on_set_scenario_status=on_set_scenario_status,
        on_edit_scenario=on_edit_scenario,
        on_delete_scenario=on_delete_scenario,
        on_create_law_update=on_create_law_update,
        on_set_law_update_status=on_set_law_update_status,
        on_delete_law_update=on_delete_law_update,
        on_edit_law_update=on_edit_law_update,
        on_create_source=on_create_source,
        on_edit_source=on_edit_source,
        on_delete_source=on_delete_source,
        on_set_source_status=on_set_source_status,
        on_select_scenario=on_select_scenario,
        on_verify_scenario=on_verify_scenario,
        on_create_stage=on_create_stage,
        on_create_step=on_create_step,
        on_set_stage_required=on_set_stage_required,
        on_set_step_required=on_set_step_required,
        on_edit_stage=on_edit_stage,
        on_delete_stage=on_delete_stage,
        on_edit_step=on_edit_step,
        on_delete_step=on_delete_step,
        on_move_stage=on_move_stage,
        on_move_step=on_move_step,
        on_add_dependency=on_add_dependency,
        on_delete_dependency=on_delete_dependency,
        on_add_related=on_add_related,
        on_delete_related=on_delete_related,
        on_add_source_ref=on_add_source_ref,
        on_delete_source_ref=on_delete_source_ref,
        on_create_authority=on_create_authority,
        on_edit_authority=on_edit_authority,
        on_delete_authority=on_delete_authority,
        on_create_document=on_create_document,
        on_edit_document=on_edit_document,
        on_delete_document=on_delete_document,
        on_update_user_role=on_update_user_role,
        on_toggle_user_status=on_toggle_user_status,
        on_create_admin_user=on_create_admin_user,
        on_add_category=on_add_category,
        on_delete_category=on_delete_category,
        on_toggle_notification_rule=on_toggle_notification_rule,
        on_edit_rule_days=on_edit_rule_days,
    )
    body = _tab_body(current_tab, state, **cb)

    return ft.Column(
        spacing=18,
        controls=[
            header,
            top_bar,
            workspace_banner if current_tab in VALID_EDITOR_TABS else ft.Container(),
            tabs_block,
            body,
        ],
    )


def build_admin_page(
    is_desktop: bool = False,
    admin_state: dict | None = None,
    on_refresh=None,
    on_open_workspace=None,
    on_select_admin_role=None,
    on_create_problem=None,
    on_set_problem_status=None,
    on_create_scenario=None,
    on_set_scenario_status=None,
    on_edit_scenario=None,
    on_delete_scenario=None,
    on_create_law_update=None,
    on_set_law_update_status=None,
    on_delete_law_update=None,
    on_edit_law_update=None,
    on_create_source=None,
    on_edit_source=None,
    on_delete_source=None,
    on_set_source_status=None,
    on_select_scenario=None,
    on_verify_scenario=None,
    on_create_stage=None,
    on_create_step=None,
    on_set_stage_required=None,
    on_set_step_required=None,
    on_edit_stage=None,
    on_delete_stage=None,
    on_edit_step=None,
    on_delete_step=None,
    on_move_stage=None,
    on_move_step=None,
    on_add_dependency=None,
    on_delete_dependency=None,
    on_add_related=None,
    on_delete_related=None,
    on_add_source_ref=None,
    on_delete_source_ref=None,
    on_create_authority=None,
    on_edit_authority=None,
    on_delete_authority=None,
    on_create_document=None,
    on_edit_document=None,
    on_delete_document=None,
    # platform_admin
    on_tab_change=None,
    on_update_user_role=None,
    on_toggle_user_status=None,
    on_create_admin_user=None,
    on_add_category=None,
    on_delete_category=None,
    on_toggle_notification_rule=None,
    on_edit_rule_days=None,
) -> ft.Control:
    content = _content(
        desktop=is_desktop,
        state=admin_state or {},
        on_refresh=on_refresh,
        on_open_workspace=on_open_workspace,
        on_select_admin_role=on_select_admin_role,
        on_tab_change=on_tab_change,
        on_create_problem=on_create_problem,
        on_set_problem_status=on_set_problem_status,
        on_create_scenario=on_create_scenario,
        on_set_scenario_status=on_set_scenario_status,
        on_edit_scenario=on_edit_scenario,
        on_delete_scenario=on_delete_scenario,
        on_create_law_update=on_create_law_update,
        on_set_law_update_status=on_set_law_update_status,
        on_delete_law_update=on_delete_law_update,
        on_edit_law_update=on_edit_law_update,
        on_create_source=on_create_source,
        on_edit_source=on_edit_source,
        on_delete_source=on_delete_source,
        on_set_source_status=on_set_source_status,
        on_select_scenario=on_select_scenario,
        on_verify_scenario=on_verify_scenario,
        on_create_stage=on_create_stage,
        on_create_step=on_create_step,
        on_set_stage_required=on_set_stage_required,
        on_set_step_required=on_set_step_required,
        on_edit_stage=on_edit_stage,
        on_delete_stage=on_delete_stage,
        on_edit_step=on_edit_step,
        on_delete_step=on_delete_step,
        on_move_stage=on_move_stage,
        on_move_step=on_move_step,
        on_add_dependency=on_add_dependency,
        on_delete_dependency=on_delete_dependency,
        on_add_related=on_add_related,
        on_delete_related=on_delete_related,
        on_add_source_ref=on_add_source_ref,
        on_delete_source_ref=on_delete_source_ref,
        on_create_authority=on_create_authority,
        on_edit_authority=on_edit_authority,
        on_delete_authority=on_delete_authority,
        on_create_document=on_create_document,
        on_edit_document=on_edit_document,
        on_delete_document=on_delete_document,
        on_update_user_role=on_update_user_role,
        on_toggle_user_status=on_toggle_user_status,
        on_create_admin_user=on_create_admin_user,
        on_add_category=on_add_category,
        on_delete_category=on_delete_category,
        on_toggle_notification_rule=on_toggle_notification_rule,
        on_edit_rule_days=on_edit_rule_days,
    )
    return desktop_content(content, width=1060, top=54) if is_desktop else content
