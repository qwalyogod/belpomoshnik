import flet as ft

from components.buttons import ghost_button, primary_button, secondary_button
from components.cards import app_card, badge, empty_state_card, icon_circle
from components.layout import desktop_content
from data.mock_data import ACHIEVEMENTS, LEARNING_STATS, MOCK_USER, SCENARIO_TEMPLATES
from theme.app_theme import APP_COLORS, CENTER, SPACING, border_all, get_badge_palette, padding_symmetric


EMPLOYMENT_OPTIONS = [
    ("employee", "Наёмный", "работа по договору"),
    ("entrepreneur", "ИП", "бизнес и налоги"),
    ("student", "Студент", "учёба и льготы"),
    ("retired", "Пенсионер", "пенсия и помощь"),
    ("unemployed", "Безработный", "поиск работы"),
]

HOUSEHOLD_OPTIONS = [
    ("has_children", "Есть дети", "семья, школа, пособия", ft.Icons.CHILD_CARE_OUTLINED),
    ("has_car", "Есть авто", "транспорт и документы", ft.Icons.DIRECTIONS_CAR_OUTLINED),
    ("is_homeowner", "Собственник жилья", "ЖКХ и недвижимость", ft.Icons.HOUSE_OUTLINED),
    ("is_tenant", "Арендатор", "договор найма", ft.Icons.APARTMENT_OUTLINED),
]

INTEREST_TAGS = [
    ("documents", "Документы", "blue"),
    ("family", "Семья", "green"),
    ("housing", "ЖКХ", "purple"),
    ("taxes", "Налоги", "orange"),
    ("health", "Здоровье", "red"),
    ("employment", "Работа", "cyan"),
    ("auto", "Авто", "blue"),
    ("business", "Бизнес/ИП", "purple"),
]

PROFILE_SECTIONS = [
    ("learning", "Подробнее об обучении", "Прогресс, тесты, категории", "/learning", ft.Icons.SCHOOL_OUTLINED, "green"),
    ("about", "О приложении", "Версия 0.1 beta и справка", "/about", ft.Icons.INFO_OUTLINE, "blue"),
    ("reset", "Сбросить демо-данные", "Вернуть тестовое состояние", "", ft.Icons.RESTORE, "orange"),
]

_EVENT_ICONS = {
    "situation_created": (ft.Icons.ADD_TASK, "green"),
    "task_completed": (ft.Icons.CHECK_CIRCLE_OUTLINED, "green"),
    "doc_added": (ft.Icons.NOTE_ADD_OUTLINED, "blue"),
    "doc_deleted": (ft.Icons.DELETE_OUTLINED, "red"),
    "profile_updated": (ft.Icons.MANAGE_ACCOUNTS_OUTLINED, "blue"),
}


def _user_initial(user: dict) -> str:
    name = str(user.get("name") or "Пользователь").strip()
    return name[:1].upper() or "П"


def _field_value(user: dict, key: str, fallback: str = "Не указано") -> str:
    value = str(user.get(key) or "").strip()
    return value or fallback


def _panel_title(title: str, icon=None, subtitle: str | None = None) -> ft.Column:
    header = ft.Row(
        spacing=10,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            icon_circle(icon or ft.Icons.INFO_OUTLINE, size=34, color=APP_COLORS["blue_text"], bgcolor=APP_COLORS["active"]),
            ft.Text(title, size=20, weight=ft.FontWeight.W_900, color=APP_COLORS["text"], expand=True),
        ],
    )
    controls: list[ft.Control] = [header]
    if subtitle:
        controls.append(ft.Text(subtitle, size=13, color=APP_COLORS["muted"]))
    return ft.Column(spacing=7, controls=controls)


def _initials_avatar(user: dict, size: int = 72) -> ft.Container:
    return ft.Container(
        width=size,
        height=size,
        border_radius=size // 2,
        bgcolor=APP_COLORS["blue"],
        alignment=CENTER,
        content=ft.Text(
            _user_initial(user),
            size=max(22, size // 3),
            weight=ft.FontWeight.W_900,
            color=APP_COLORS["on_accent"],
        ),
    )


def _soft_circle(size: int, right: int, top: int, opacity: float = 0.48) -> ft.Container:
    return ft.Container(
        width=size,
        height=size,
        right=right,
        top=top,
        border_radius=size // 2,
        bgcolor=ft.Colors.with_opacity(opacity, APP_COLORS["active"]),
        animate=ft.Animation(280, ft.AnimationCurve.EASE_OUT),
    )


def _profile_hero(user: dict, settings: dict, desktop: bool, on_logout=None, on_save=None) -> ft.Container:
    def hero_action(text: str, icon, on_click, active: bool = False, width: int = 118) -> ft.Container:
        return ft.Container(
            width=width,
            height=38,
            padding=padding_symmetric(horizontal=14, vertical=8),
            border_radius=12,
            bgcolor=APP_COLORS["blue"] if active else APP_COLORS["surface"],
            border=border_all(APP_COLORS["blue"] if active else APP_COLORS["stroke2"]),
            on_click=on_click,
            ink=True,
            content=ft.Row(
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(icon, size=15, color=APP_COLORS["on_accent"] if active else APP_COLORS["blue_text"]),
                    ft.Text(
                        text,
                        size=12,
                        weight=ft.FontWeight.W_900,
                        color=APP_COLORS["on_accent"] if active else APP_COLORS["text"],
                        no_wrap=True,
                    ),
                ],
            ),
        )

    actions: list[ft.Control] = []
    if on_save:
        actions.append(hero_action("Сохранить", ft.Icons.CHECK, on_save, True, 126))
    if on_logout:
        actions.append(hero_action("Выйти", ft.Icons.LOGOUT, on_logout, False, 94))

    text_block = ft.Column(
        spacing=8,
        expand=desktop,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER if not desktop else ft.CrossAxisAlignment.START,
        controls=[
            ft.Text(
                _field_value(user, "name", "Пользователь"),
                size=28 if desktop else 19,
                weight=ft.FontWeight.W_900,
                color=APP_COLORS["text"],
                max_lines=2,
                text_align=ft.TextAlign.CENTER if not desktop else ft.TextAlign.START,
            ),
            ft.Text(_field_value(user, "email", "email не указан"), size=13, color=APP_COLORS["muted"], max_lines=1),
            ft.Row(
                wrap=True,
                alignment=ft.MainAxisAlignment.CENTER if not desktop else ft.MainAxisAlignment.START,
                spacing=7,
                run_spacing=7,
                controls=[
                    badge(_field_value(user, "city", "Город"), "blue"),
                    badge("Гражданин", "green"),
                    badge(("Режим обучения" if desktop else "Обучение") if settings.get("learning_mode", False) else "Обычный режим", "purple"),
                ],
            ),
            ft.Row(alignment=ft.MainAxisAlignment.CENTER if not desktop else ft.MainAxisAlignment.START, wrap=True, spacing=8, run_spacing=8, controls=actions) if actions else ft.Container(),
        ],
    )

    if desktop:
        hero_content = ft.Row(
            spacing=18,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[_initials_avatar(user, 78), text_block],
        )
    else:
        hero_content = ft.Column(
            spacing=12,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[_initials_avatar(user, 66), text_block],
        )

    return ft.Container(
        width=float("inf"),
        padding=24 if desktop else 16,
        border_radius=28,
        bgcolor=APP_COLORS["surface3"],
        border=border_all(APP_COLORS["stroke2"]),
        shadow=[],
        content=hero_content,
    )


def _stat_tile(label: str, value: str | int, hint: str, icon, tone: str = "blue", width: int | float | None = None, route: str | None = None, go_to=None) -> ft.Container:
    palette = get_badge_palette()
    bg, fg = palette.get(tone, palette["blue"])
    card = app_card(
        ft.Row(
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                icon_circle(icon, size=40, color=fg, bgcolor=bg),
                ft.Column(
                    spacing=1,
                    expand=True,
                    controls=[
                        ft.Text(str(value), size=22, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                        ft.Text(label, size=12, weight=ft.FontWeight.W_800, color=APP_COLORS["muted"]),
                        ft.Text(hint, size=11, color=APP_COLORS["muted2"]),
                    ],
                ),
            ],
        ),
        padding=14,
        width=width,
    )
    if route and go_to:
        card.ink = True
        card.on_click = lambda _: go_to(route)

        def _hover(e: ft.HoverEvent) -> None:
            card.bgcolor = APP_COLORS["surface2"] if e.data == "true" else APP_COLORS["surface"]
            card.update()

        card.on_hover = _hover
    return card


def _stats_row(favorite_ids: list[str] | set[str] | None = None, desktop: bool = False, go_to=None) -> ft.Control:
    earned = len([item for item in ACHIEVEMENTS if item.get("earned")])
    stats = [
        ("Ситуации", 3, "активные планы", ft.Icons.TASK_ALT_OUTLINED, "blue", "/situations"),
        ("Избранное", len(set(favorite_ids or [])), "сценарии", ft.Icons.STAR_OUTLINE, "orange", "/scenarios"),
        ("Достижения", earned, "получено", ft.Icons.EMOJI_EVENTS_OUTLINED, "purple", "/learning"),
        ("Документы", 6, "в сейфе", ft.Icons.FOLDER_OUTLINED, "green", "/documents"),
    ]
    tiles = [_stat_tile(label, value, hint, icon, tone, route=route, go_to=go_to) for label, value, hint, icon, tone, route in stats]
    if desktop:
        return ft.Row(spacing=12, controls=[ft.Container(expand=True, content=tile) for tile in tiles])
    mobile_tiles = [_stat_tile(label, value, hint, icon, tone, width=164, route=route, go_to=go_to) for label, value, hint, icon, tone, route in stats]
    return ft.Column(spacing=10, controls=[
        ft.Row(spacing=10, alignment=ft.MainAxisAlignment.CENTER, controls=[mobile_tiles[0], mobile_tiles[1]]),
        ft.Row(spacing=10, alignment=ft.MainAxisAlignment.CENTER, controls=[mobile_tiles[2], mobile_tiles[3]]),
    ])


def _profile_text_field(label: str, value: str, icon=None) -> tuple[ft.Column, ft.TextField]:
    text_field = ft.TextField(
        value=value,
        prefix_icon=icon,
        height=54,
        border_radius=14,
        border_color=APP_COLORS["stroke2"],
        focused_border_color=APP_COLORS["blue"],
        bgcolor=APP_COLORS["surface2"],
        color=APP_COLORS["text"],
        text_size=14,
        content_padding=padding_symmetric(horizontal=14, vertical=0),
    )
    control = ft.Column(
        spacing=7,
        controls=[
            ft.Text(label, size=12, weight=ft.FontWeight.W_800, color=APP_COLORS["muted"]),
            text_field,
        ],
    )
    return control, text_field


def _personal_data_card(user: dict, desktop: bool) -> tuple[ft.Container, dict[str, ft.TextField]]:
    field_defs = [
        ("name", "Имя", _field_value(user, "name"), ft.Icons.PERSON_OUTLINE),
        ("birth_date", "Дата рождения", _field_value(user, "birth_date", "12.04.1998"), ft.Icons.CAKE_OUTLINED),
        ("email", "Email", _field_value(user, "email"), ft.Icons.MAIL_OUTLINE),
        ("region", "Регион", _field_value(user, "region"), ft.Icons.MAP_OUTLINED),
        ("city", "Город", _field_value(user, "city"), ft.Icons.LOCATION_CITY_OUTLINED),
        ("district", "Район", _field_value(user, "district"), ft.Icons.MAP_OUTLINED),
        ("address", "Адрес", _field_value(user, "address"), ft.Icons.HOME_OUTLINED),
    ]
    refs: dict[str, ft.TextField] = {}
    fields: list[ft.Control] = []
    for key, label, value, icon in field_defs:
        control, ref = _profile_text_field(label, value, icon)
        refs[key] = ref
        fields.append(control)

    rows: list[ft.Control] = []
    if desktop:
        for index in range(0, len(fields), 2):
            row_controls = [ft.Container(expand=True, content=field) for field in fields[index:index + 2]]
            if len(row_controls) == 1:
                row_controls.append(ft.Container(expand=True))
            rows.append(ft.Row(spacing=12, controls=row_controls))
    else:
        rows = fields

    return app_card(
        ft.Column(
            spacing=16,
            controls=[
                _panel_title("Данные пользователя", ft.Icons.BADGE_OUTLINED, "Личные данные используются только для локальной персонализации."),
                ft.Column(spacing=12, controls=rows),
            ],
        ),
        padding=22 if desktop else 16,
        width=float("inf"),
    ), refs


def _employment_card(user: dict, on_change=None, desktop: bool = False) -> ft.Container:
    current = str((user or {}).get("employment_status") or "employee")
    controls: list[ft.Control] = []
    for key, label, hint in EMPLOYMENT_OPTIONS:
        selected = current == key
        controls.append(
            ft.Container(
                padding=padding_symmetric(horizontal=14, vertical=10),
                border_radius=999,
                bgcolor=APP_COLORS["blue"] if selected else APP_COLORS["surface2"],
                border=border_all(APP_COLORS["blue"] if selected else APP_COLORS["stroke2"]),
                on_click=(lambda _, value=key: on_change(value)) if on_change else None,
                ink=True,
                content=ft.Column(
                    spacing=1,
                    controls=[
                        ft.Text(
                            label,
                            size=13,
                            weight=ft.FontWeight.W_900,
                            color=APP_COLORS["on_accent"] if selected else APP_COLORS["text"],
                            max_lines=1,
                            no_wrap=True,
                        ),
                        ft.Text(
                            hint,
                            size=10,
                            color=APP_COLORS["on_accent"] if selected else APP_COLORS["muted"],
                            max_lines=1,
                            no_wrap=True,
                        ),
                    ],
                ),
            )
        )

    return app_card(
        ft.Column(
            spacing=14,
            controls=[
                _panel_title("Статус занятости", ft.Icons.WORK_OUTLINE, "Влияет на рекомендации по налогам, льготам и сценариям."),
                ft.Row(wrap=True, spacing=8, run_spacing=8, controls=controls),
            ],
        ),
        padding=22 if desktop else 16,
        width=float("inf"),
    )


def _household_card(user: dict, on_change=None, desktop: bool = False) -> ft.Container:
    rows: list[ft.Control] = []
    for key, label, hint, icon in HOUSEHOLD_OPTIONS:
        value = bool((user or {}).get(key, False))
        rows.append(
            ft.Container(
                padding=12,
                border_radius=16,
                bgcolor=APP_COLORS["surface2"],
                border=border_all(APP_COLORS["stroke2"]),
                content=ft.Row(
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        icon_circle(icon, size=34, color=APP_COLORS["muted2"], bgcolor=APP_COLORS["surface"]),
                        ft.Column(
                            spacing=1,
                            expand=True,
                            controls=[
                                ft.Text(label, size=14, weight=ft.FontWeight.W_800, color=APP_COLORS["text"]),
                                ft.Text(hint, size=12, color=APP_COLORS["muted"], max_lines=2),
                            ],
                        ),
                        ft.Checkbox(
                            value=value,
                            active_color=APP_COLORS["blue"],
                            check_color=APP_COLORS["on_accent"],
                            on_change=(lambda ev, value_key=key: on_change(value_key, bool(ev.control.value))) if on_change else None,
                        ),
                    ],
                ),
            )
        )

    return app_card(
        ft.Column(
            spacing=14,
            controls=[
                _panel_title("Семья и имущество", ft.Icons.FAMILY_RESTROOM, "Эти признаки помогают формировать персональные подсказки."),
                ft.Column(spacing=8, controls=rows),
            ],
        ),
        padding=22 if desktop else 16,
        width=float("inf"),
    )


def _interests_card(user: dict, on_add_interest=None, on_toggle_tag=None, desktop: bool = False) -> ft.Container:
    selected_tags = set((user or {}).get("interest_tags", []) or [])
    label_to_key = {label: key for key, label, _ in INTEREST_TAGS}
    custom_interests = [
        item for item in (user or {}).get("interests", [])
        if item and item not in label_to_key
    ]

    chips: list[ft.Control] = []
    palette = get_badge_palette()
    for key, label, tone in INTEREST_TAGS:
        active = key in selected_tags
        bg, fg = palette.get(tone, palette["blue"])
        chips.append(
            ft.Container(
                padding=padding_symmetric(horizontal=13, vertical=7),
                border_radius=999,
                bgcolor=bg if active else APP_COLORS["surface2"],
                border=border_all(fg if active else APP_COLORS["stroke2"]),
                on_click=(lambda _, tag_key=key: on_toggle_tag(tag_key)) if on_toggle_tag else None,
                ink=True,
                content=ft.Text(
                    label,
                    size=12,
                    weight=ft.FontWeight.W_900,
                    color=fg if active else APP_COLORS["muted"],
                    max_lines=1,
                    no_wrap=True,
                ),
            )
        )

    extra_controls: list[ft.Control] = []
    if custom_interests:
        extra_controls.append(ft.Row(wrap=True, spacing=8, run_spacing=8, controls=[badge(item, "default") for item in custom_interests]))

    extra_controls.append(
        ft.Container(
            content=badge("+ Добавить", "default"),
            on_click=on_add_interest,
            ink=True,
        )
    )

    return app_card(
        ft.Column(
            spacing=14,
            controls=[
                _panel_title("Интересы и персонализация", ft.Icons.LOCAL_OFFER_OUTLINED, "Влияют на рекомендации, закон-апдейты и быстрые сценарии."),
                ft.Row(wrap=True, spacing=8, run_spacing=8, controls=chips),
                *extra_controls,
            ],
        ),
        padding=22 if desktop else 16,
        width=float("inf"),
    )


def _setting_row(title: str, subtitle: str, value: bool = False, icon=None, on_change=None) -> ft.Container:
    return ft.Container(
        padding=10,
        border_radius=16,
        bgcolor=APP_COLORS["surface2"],
        border=border_all(APP_COLORS["stroke2"]),
        animate=ft.Animation(280, ft.AnimationCurve.EASE_OUT),
        content=ft.Row(
            spacing=10,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Row(
                    spacing=10,
                    expand=True,
                    controls=[
                        icon_circle(icon or ft.Icons.TUNE, size=34, color=APP_COLORS["blue_text"], bgcolor=APP_COLORS["active"]),
                        ft.Column(
                            spacing=1,
                            expand=True,
                            controls=[
                                ft.Text(title, size=13, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                                ft.Text(subtitle, size=11, color=APP_COLORS["muted"], max_lines=2),
                            ],
                        ),
                    ],
                ),
                ft.Switch(
                    value=value,
                    active_color=APP_COLORS["blue"],
                    on_change=lambda event: on_change(bool(event.control.value)) if on_change else None,
                ),
            ],
        ),
    )


def _settings_card(settings: dict, on_setting_change=None, desktop: bool = False) -> ft.Container:
    rows = [
        _setting_row("Крупный шрифт", "Увеличить текст интерфейса", settings.get("large_text", False), ft.Icons.TEXT_FIELDS, lambda value: on_setting_change("large_text", value) if on_setting_change else None),
        _setting_row("Высокий контраст", "Усилить читаемость", settings.get("high_contrast", False), ft.Icons.CONTRAST, lambda value: on_setting_change("high_contrast", value) if on_setting_change else None),
        _setting_row("Тёмная тема", "Переключить оформление", settings.get("dark_theme", False), ft.Icons.DARK_MODE_OUTLINED, lambda value: on_setting_change("dark_theme", value) if on_setting_change else None),
        _setting_row("Режим обучения", "Показывать микро-тесты", settings.get("learning_mode", False), ft.Icons.SCHOOL_OUTLINED, lambda value: on_setting_change("learning_mode", value) if on_setting_change else None),
        _setting_row("Email-уведомления", "Демо-напоминания о сроках", settings.get("email_notifications", True), ft.Icons.NOTIFICATIONS_NONE_OUTLINED, lambda value: on_setting_change("email_notifications", value) if on_setting_change else None),
    ]
    language = ft.Container(
        padding=12,
        border_radius=16,
        bgcolor=APP_COLORS["surface2"],
        border=border_all(APP_COLORS["stroke2"]),
        content=ft.Row(
            spacing=10,
            controls=[
                icon_circle(ft.Icons.LANGUAGE, size=34, color=APP_COLORS["blue_text"], bgcolor=APP_COLORS["active"]),
                ft.Column(
                    spacing=1,
                    expand=True,
                    controls=[
                        ft.Text("Язык интерфейса", size=13, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                        ft.Text("Русский", size=11, color=APP_COLORS["muted"]),
                    ],
                ),
                badge("RU", "blue"),
            ],
        ),
    )
    return app_card(
        ft.Column(
            spacing=12,
            controls=[
                _panel_title("Настройки", ft.Icons.SETTINGS_OUTLINED),
                *rows,
                language,
            ],
        ),
        padding=22 if desktop else 16,
        width=float("inf"),
    )


def _favorite_card(template: dict, width: int | None, on_open_scenario=None) -> ft.Container:
    category = template.get("category", "Сценарий")
    duration = template.get("estimated_duration", "уточняется")
    return ft.Container(
        width=width,
        content=ft.Container(
            padding=14,
            border_radius=18,
            bgcolor=APP_COLORS["surface2"],
            border=border_all(APP_COLORS["stroke2"]),
            on_click=lambda _: on_open_scenario(template.get("id")) if on_open_scenario else None,
            ink=True,
            content=ft.Row(
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    icon_circle(ft.Icons.ROUTE_OUTLINED, size=36, color=APP_COLORS["green"], bgcolor=get_badge_palette()["green"][0]),
                    ft.Column(
                        spacing=2,
                        expand=True,
                        controls=[
                            ft.Text(template.get("title", "Сценарий"), size=14, weight=ft.FontWeight.W_900, color=APP_COLORS["text"], max_lines=2),
                            ft.Text(f"{category} • {duration}", size=11, color=APP_COLORS["muted"], max_lines=1),
                        ],
                    ),
                    ft.Icon(ft.Icons.STAR, size=18, color=APP_COLORS["orange"]),
                    ft.Icon(ft.Icons.CHEVRON_RIGHT, size=18, color=APP_COLORS["muted2"]),
                ],
            ),
        ),
    )


def _favorite_scenarios_card(
    favorite_ids: list[str] | set[str] | None = None,
    on_open_scenario=None,
    go_to=None,
    desktop: bool = False,
) -> ft.Container:
    favorite_set = set(favorite_ids or [])
    favorites = [template for template in SCENARIO_TEMPLATES if template.get("id") in favorite_set]
    if not favorites:
        return empty_state_card(
            "Избранных сценариев пока нет",
            "Добавьте сценарий в избранное, чтобы быстро вернуться к нему.",
            "Выбрать сценарий",
            lambda _: go_to("/scenarios") if go_to else None,
            ft.Icons.STAR_BORDER,
        )

    if desktop:
        rows: list[ft.Control] = []
        cards = [_favorite_card(item, None, on_open_scenario) for item in favorites[:4]]
        for index in range(0, len(cards), 2):
            row_controls = [ft.Container(expand=True, content=item) for item in cards[index:index + 2]]
            if len(row_controls) == 1:
                row_controls.append(ft.Container(expand=True))
            rows.append(ft.Row(spacing=10, controls=row_controls))
        list_control = ft.Column(spacing=10, controls=rows)
    else:
        list_control = ft.Row(
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            controls=[_favorite_card(item, 248, on_open_scenario) for item in favorites[:5]],
        )

    return app_card(
        ft.Column(
            spacing=14,
            controls=[
                _panel_title("Избранные сценарии", ft.Icons.STAR_OUTLINE),
                list_control,
                ghost_button("Все избранное", icon=ft.Icons.ARROW_FORWARD, height=42, on_click=lambda _: go_to("/scenarios") if go_to else None),
            ],
        ),
        padding=22 if desktop else 16,
        width=float("inf"),
    )


def _achievements_card(go_to=None, desktop: bool = False) -> ft.Container:
    rows: list[ft.Control] = []
    for item in ACHIEVEMENTS[:5]:
        earned = bool(item.get("earned"))
        rows.append(
            ft.Container(
                padding=12,
                border_radius=16,
                bgcolor=APP_COLORS["surface2"],
                border=border_all(APP_COLORS["stroke2"]),
                content=ft.Row(
                    spacing=10,
                    controls=[
                        icon_circle(ft.Icons.EMOJI_EVENTS_OUTLINED, size=34, color=APP_COLORS["green"] if earned else APP_COLORS["muted2"], bgcolor=get_badge_palette()["green" if earned else "gray"][0]),
                        ft.Column(
                            spacing=2,
                            expand=True,
                            controls=[
                                ft.Text(item.get("title", "Достижение"), size=13, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                                ft.Text("получено" if earned else "в процессе", size=11, color=APP_COLORS["muted"]),
                            ],
                        ),
                    ],
                ),
            )
        )

    return app_card(
        ft.Column(
            spacing=12,
            controls=[
                _panel_title("Достижения", ft.Icons.EMOJI_EVENTS_OUTLINED),
                ft.Column(spacing=8, controls=rows),
                ft.Text(
                    f"Пройдено тестов: {LEARNING_STATS['completed_tests']}. Средний результат: {LEARNING_STATS['average_score']}.",
                    size=12,
                    color=APP_COLORS["muted"],
                ),
                secondary_button("Подробнее об обучении", icon=ft.Icons.SCHOOL_OUTLINED, on_click=lambda _: go_to("/learning") if go_to else None, expand=not desktop),
            ],
        ),
        padding=22 if desktop else 16,
        width=float("inf"),
    )


def _profile_sections_card(go_to=None, on_reset_demo=None, on_logout=None, desktop: bool = False) -> ft.Container:
    controls: list[ft.Control] = []
    for key, title, subtitle, route, icon, tone in PROFILE_SECTIONS:
        bg, fg = get_badge_palette().get(tone, get_badge_palette()["blue"])
        if key == "reset":
            click = on_reset_demo
        else:
            click = (lambda _, target=route: go_to(target)) if go_to else None
        controls.append(
            ft.Container(
                padding=12,
                border_radius=16,
                bgcolor=APP_COLORS["surface2"],
                border=border_all(APP_COLORS["stroke2"]),
                on_click=click,
                ink=True,
                content=ft.Row(
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        icon_circle(icon, size=34, color=fg, bgcolor=bg),
                        ft.Column(
                            spacing=2,
                            expand=True,
                            controls=[
                                ft.Text(title, size=13, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                                ft.Text(subtitle, size=11, color=APP_COLORS["muted"]),
                            ],
                        ),
                        ft.Icon(ft.Icons.CHEVRON_RIGHT, size=18, color=APP_COLORS["muted2"]),
                    ],
                ),
            )
        )
    controls.append(ghost_button("Выйти из аккаунта", icon=ft.Icons.LOGOUT, on_click=on_logout, expand=True))
    return app_card(
        ft.Column(
            spacing=12,
            controls=[
                _panel_title("Разделы профиля", ft.Icons.APPS_OUTLINED),
                *controls,
            ],
        ),
        padding=22 if desktop else 16,
        width=float("inf"),
    )


def _activity_card(activity_log: list[dict] | None, desktop: bool = False) -> ft.Container:
    entries = list(activity_log or [])[:5]
    if not entries:
        return app_card(
            ft.Column(
                spacing=10,
                controls=[
                    _panel_title("Журнал активности", ft.Icons.HISTORY_OUTLINED),
                    ft.Text("Действия пока не зафиксированы.", size=13, color=APP_COLORS["muted"]),
                ],
            ),
            padding=22 if desktop else 16,
            width=float("inf"),
        )

    rows: list[ft.Control] = []
    for entry in entries:
        icon, tone = _EVENT_ICONS.get(entry.get("event_type", ""), (ft.Icons.RADIO_BUTTON_UNCHECKED, "gray"))
        bg, fg = get_badge_palette().get(tone, get_badge_palette()["gray"])
        rows.append(
            ft.Row(
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    icon_circle(icon, size=34, color=fg, bgcolor=bg),
                    ft.Column(
                        spacing=2,
                        expand=True,
                        controls=[
                            ft.Text(entry.get("title", "Событие"), size=13, weight=ft.FontWeight.W_800, color=APP_COLORS["text"]),
                            ft.Text(entry.get("date", ""), size=11, color=APP_COLORS["muted"]),
                        ],
                    ),
                ],
            )
        )

    return app_card(
        ft.Column(
            spacing=12,
            controls=[
                _panel_title("Журнал активности", ft.Icons.HISTORY_OUTLINED),
                ft.Column(spacing=10, controls=rows),
            ],
        ),
        padding=22 if desktop else 16,
        width=float("inf"),
    )


def _desktop_profile(
    user: dict,
    settings: dict,
    on_setting_change=None,
    on_save_profile=None,
    on_logout=None,
    on_add_interest=None,
    go_to=None,
    on_reset_demo=None,
    favorite_ids: list[str] | set[str] | None = None,
    on_open_scenario=None,
    on_employment_change=None,
    on_household_change=None,
    on_toggle_tag=None,
    activity_log: list[dict] | None = None,
) -> ft.Control:
    data_card, refs = _personal_data_card(user, True)

    def save(event=None):
        if on_save_profile:
            on_save_profile(refs)

    left = ft.Column(
        spacing=16,
        controls=[
            _profile_hero(user, settings, True, on_logout, save),
            _stats_row(favorite_ids, True, go_to),
            data_card,
            _interests_card(user, on_add_interest, on_toggle_tag, True),
            _favorite_scenarios_card(favorite_ids, on_open_scenario, go_to, True),
            _employment_card(user, on_employment_change, True),
            _household_card(user, on_household_change, True),
        ],
    )
    right = ft.Column(
        spacing=16,
        controls=[
            _settings_card(settings, on_setting_change, True),
            _achievements_card(go_to, True),
            _profile_sections_card(go_to, on_reset_demo, on_logout, True),
            _activity_card(activity_log, True),
        ],
    )

    content = ft.Column(
        spacing=18,
        controls=[
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    ft.Column(
                        spacing=5,
                        expand=True,
                        controls=[
                            ft.Text("Профиль", size=34, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                            ft.Text("Личные данные, интересы, настройки доступности и персональные рекомендации.", size=14, color=APP_COLORS["muted"]),
                        ],
                    ),
                    ft.Row(spacing=10, controls=[icon_circle(ft.Icons.PERSON_OUTLINE, size=42, color=APP_COLORS["blue_text"], bgcolor=APP_COLORS["active"]), badge("4", "blue")]),
                ],
            ),
            ft.Row(
                spacing=18,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    ft.Container(width=680, content=left),
                    ft.Container(width=300, content=right),
                ],
            ),
        ],
    )
    return desktop_content(content, width=1010, top=42)


def _mobile_profile(
    user: dict,
    settings: dict,
    on_setting_change=None,
    on_save_profile=None,
    on_logout=None,
    on_add_interest=None,
    go_to=None,
    on_reset_demo=None,
    favorite_ids: list[str] | set[str] | None = None,
    on_open_scenario=None,
    on_employment_change=None,
    on_household_change=None,
    on_toggle_tag=None,
    activity_log: list[dict] | None = None,
) -> ft.Control:
    data_card, refs = _personal_data_card(user, False)

    def save(event=None):
        if on_save_profile:
            on_save_profile(refs)

    return ft.Container(
        width=343,
        content=ft.Column(
            spacing=14,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text("Профиль", size=24, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                        ft.Row(spacing=8, controls=[icon_circle(ft.Icons.PERSON_OUTLINE, size=36, color=APP_COLORS["blue_text"], bgcolor=APP_COLORS["active"]), badge("4", "blue")]),
                    ],
                ),
                _profile_hero(user, settings, False, on_logout, save),
                _stats_row(favorite_ids, False, go_to),
                data_card,
                _interests_card(user, on_add_interest, on_toggle_tag, False),
                _settings_card(settings, on_setting_change, False),
                _favorite_scenarios_card(favorite_ids, on_open_scenario, go_to, False),
                _achievements_card(go_to, False),
                _employment_card(user, on_employment_change, False),
                _household_card(user, on_household_change, False),
                _profile_sections_card(go_to, on_reset_demo, on_logout, False),
                _activity_card(activity_log, False),
                primary_button("Сохранить профиль", icon=ft.Icons.CHECK_CIRCLE, expand=True, on_click=save),
                ghost_button("Выйти", icon=ft.Icons.LOGOUT, expand=True, on_click=on_logout),
                ft.Container(height=SPACING["xs"]),
            ],
        ),
    )


def build_profile_page(
    is_desktop: bool = False,
    user: dict | None = None,
    settings: dict | None = None,
    on_setting_change=None,
    on_save_profile=None,
    on_logout=None,
    on_add_interest=None,
    go_to=None,
    on_reset_demo=None,
    favorite_ids: list[str] | set[str] | None = None,
    on_open_scenario=None,
    on_employment_change=None,
    on_household_change=None,
    on_toggle_tag=None,
    activity_log: list[dict] | None = None,
) -> ft.Control:
    profile_user = user or MOCK_USER
    profile_settings = settings or {"learning_mode": False, "email_notifications": True}
    if is_desktop:
        return _desktop_profile(
            profile_user,
            profile_settings,
            on_setting_change,
            on_save_profile,
            on_logout,
            on_add_interest,
            go_to,
            on_reset_demo,
            favorite_ids,
            on_open_scenario,
            on_employment_change,
            on_household_change,
            on_toggle_tag,
            activity_log,
        )
    return _mobile_profile(
        profile_user,
        profile_settings,
        on_setting_change,
        on_save_profile,
        on_logout,
        on_add_interest,
        go_to,
        on_reset_demo,
        favorite_ids,
        on_open_scenario,
        on_employment_change,
        on_household_change,
        on_toggle_tag,
        activity_log,
    )
