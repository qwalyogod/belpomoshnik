from __future__ import annotations

from datetime import date

import flet as ft

from components.buttons import ghost_button
from components.cards import app_card, badge, empty_state_card, icon_circle, page_heading, search_box
from components.layout import desktop_content
from services.dashboard import parse_due_date
from theme.app_theme import APP_COLORS, SPACING, border_all, get_badge_palette, padding_symmetric, ts


FILTERS = [
    ("all", "Все"),
    ("unread", "Непрочитанные"),
    ("task", "Задачи"),
    ("document", "Документы"),
    ("law", "Законы"),
    ("utility", "ЖКХ"),
    ("tax", "Налоги"),
]

GROUP_TITLES = [
    ("today", "Сегодня"),
    ("week", "На этой неделе"),
    ("earlier", "Раньше"),
]


def _icon(notification_type: str, source: str = "") -> str:
    if source.startswith("util-"):
        return ft.Icons.HOME_WORK_OUTLINED
    if source == "tax_deadline":
        return ft.Icons.RECEIPT_LONG_OUTLINED
    if notification_type == "document":
        return ft.Icons.DESCRIPTION_OUTLINED
    if notification_type == "task":
        return ft.Icons.TASK_ALT_OUTLINED
    if notification_type == "law":
        return ft.Icons.BALANCE_OUTLINED
    if notification_type == "email_demo":
        return ft.Icons.MARK_EMAIL_UNREAD_OUTLINED
    return ft.Icons.NOTIFICATIONS_NONE_OUTLINED


def _tone(notification: dict) -> str:
    source = str(notification.get("source") or "")
    notification_type = str(notification.get("type") or "")
    if _is_urgent(notification):
        return "red"
    if source.startswith("util-"):
        return "cyan"
    if source == "tax_deadline":
        return "orange"
    if notification_type == "document":
        return "green"
    if notification_type == "law":
        return "purple"
    if notification_type == "email_demo":
        return "blue"
    return "blue"


def _type_label(notification: dict) -> str:
    source = str(notification.get("source") or "")
    notification_type = str(notification.get("type") or "")
    if source.startswith("util-"):
        return "ЖКХ"
    if source == "tax_deadline":
        return "Налоги"
    if notification_type == "document":
        return "Документ"
    if notification_type == "law":
        return "Закон"
    if notification_type == "email_demo":
        return "Email"
    return "Задача"


def _is_urgent(notification: dict) -> bool:
    label = str(notification.get("date") or "").lower()
    days_left = notification.get("days_left")
    if isinstance(days_left, int) and days_left < 0:
        return True
    if "просроч" in label:
        return True
    due_date = parse_due_date(notification.get("due_date"))
    return bool(due_date and due_date < date.today() and not notification.get("is_read"))


def _group_key(notification: dict) -> str:
    label = str(notification.get("date") or "").lower()
    due_date = parse_due_date(notification.get("due_date") or notification.get("expiry_date"))
    if "сегодня" in label or "просроч" in label:
        return "today"
    if due_date:
        delta = (due_date - date.today()).days
        if delta <= 0:
            return "today"
        if delta <= 7:
            return "week"
    if "завтра" in label or "через" in label or "авто" in label:
        return "week"
    return "earlier"


def _sort_key(notification: dict) -> tuple[int, date, str]:
    group_order = {"today": 0, "week": 1, "earlier": 2}
    due_date = parse_due_date(notification.get("due_date") or notification.get("expiry_date")) or date.max
    return (group_order.get(_group_key(notification), 3), due_date, str(notification.get("title") or ""))


def _matches_filter(notification: dict, filter_key: str) -> bool:
    source = str(notification.get("source") or "")
    notification_type = str(notification.get("type") or "")
    if filter_key == "all":
        return True
    if filter_key == "unread":
        return not notification.get("is_read")
    if filter_key == "utility":
        return source.startswith("util-")
    if filter_key == "tax":
        return source == "tax_deadline" or "налог" in str(notification.get("title", "")).lower()
    if filter_key == "task":
        return notification_type == "task" and not source.startswith("util-")
    if filter_key == "document":
        return notification_type in {"document", "email_demo"}
    if filter_key == "law":
        return notification_type == "law" and source != "tax_deadline"
    return True


def _filter_notifications(notifications: list[dict], query: str, filter_key: str) -> list[dict]:
    query_text = query.strip().lower()
    result: list[dict] = []
    for notification in notifications:
        if not _matches_filter(notification, filter_key):
            continue
        haystack = " ".join(
            [
                str(notification.get("title") or ""),
                str(notification.get("desc") or ""),
                str(notification.get("date") or ""),
                _type_label(notification),
            ]
        ).lower()
        if query_text and query_text not in haystack:
            continue
        result.append(notification)
    return sorted(result, key=_sort_key)


def _open_notification(notification: dict, on_mark_read=None, go_to=None, on_open_email_preview=None) -> None:
    if on_mark_read and not notification.get("is_read"):
        on_mark_read(notification.get("id"))
    source = str(notification.get("source") or "")
    notification_type = str(notification.get("type") or "")
    if notification_type == "email_demo" and on_open_email_preview:
        on_open_email_preview(notification)
        return
    if not go_to:
        return
    if source.startswith("util-"):
        go_to("/utility")
    elif source == "tax_deadline":
        go_to("/taxes")
    elif notification_type == "document":
        go_to("/documents")
    elif notification_type == "law":
        go_to("/legal-updates")
    else:
        go_to("/situations")


def _filter_chip(label: str, selected: bool, on_click=None) -> ft.Container:
    return ft.Container(
        content=ft.Text(
            label,
            size=ts(13),
            weight=ft.FontWeight.W_800,
            color=APP_COLORS["on_accent"] if selected else APP_COLORS["text"],
            no_wrap=True,
        ),
        padding=padding_symmetric(horizontal=14, vertical=8),
        border_radius=18,
        bgcolor=APP_COLORS["blue"] if selected else APP_COLORS["surface2"],
        border=border_all(APP_COLORS["blue"] if selected else APP_COLORS["stroke2"]),
        on_click=on_click,
        ink=True,
    )


def _stats_tile(label: str, value: int, hint: str, icon: str, tone: str, compact: bool = False) -> ft.Container:
    palette = get_badge_palette()
    bg, fg = palette.get(tone, palette["blue"])
    if compact:
        return ft.Container(
            padding=12,
            border_radius=18,
            bgcolor=APP_COLORS["surface"],
            border=border_all(APP_COLORS["stroke2"]),
            content=ft.Column(
                spacing=4,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text(str(value), size=ts(18), weight=ft.FontWeight.W_900, color=fg),
                    ft.Text(label, size=ts(10), weight=ft.FontWeight.W_800, color=APP_COLORS["muted"], text_align=ft.TextAlign.CENTER),
                ],
            ),
        )
    return app_card(
        ft.Row(
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                icon_circle(icon, size=42, color=fg, bgcolor=bg),
                ft.Column(
                    spacing=2,
                    controls=[
                        ft.Text(str(value), size=ts(26), weight=ft.FontWeight.W_900, color=fg),
                        ft.Text(label, size=ts(12), weight=ft.FontWeight.W_800, color=APP_COLORS["text"]),
                        ft.Text(hint, size=ts(11), color=APP_COLORS["muted2"]),
                    ],
                ),
            ],
        ),
        padding=16,
    )


def _stats_row(notifications: list[dict], desktop: bool) -> ft.Control:
    unread_count = len([item for item in notifications if not item.get("is_read")])
    urgent_count = len([item for item in notifications if _is_urgent(item)])
    document_count = len([item for item in notifications if _matches_filter(item, "document")])
    law_count = len([item for item in notifications if _matches_filter(item, "law")])
    tiles = [
        _stats_tile("Непрочитанные", unread_count, "требуют внимания", ft.Icons.MARKUNREAD_OUTLINED, "blue", not desktop),
        _stats_tile("Срочные", urgent_count, "сегодня и просрочка", ft.Icons.PRIORITY_HIGH_OUTLINED, "red", not desktop),
        _stats_tile("Документы", document_count, "сроки и файлы", ft.Icons.DESCRIPTION_OUTLINED, "green", not desktop),
        _stats_tile("Закон-апдейты", law_count, "новые изменения", ft.Icons.BALANCE_OUTLINED, "purple", not desktop),
    ]
    if desktop:
        return ft.Row(spacing=12, controls=[ft.Container(expand=True, content=tile) for tile in tiles])
    return ft.Column(
        spacing=10,
        controls=[
            ft.Row(spacing=10, controls=[ft.Container(expand=True, content=tiles[0]), ft.Container(expand=True, content=tiles[1])]),
            ft.Row(spacing=10, controls=[ft.Container(expand=True, content=tiles[2]), ft.Container(expand=True, content=tiles[3])]),
        ],
    )


def _notification_action_text(notification: dict) -> str:
    source = str(notification.get("source") or "")
    if source.startswith("util-"):
        return "К ЖКХ"
    if source == "tax_deadline":
        return "К налогам"
    if notification.get("type") == "document":
        return "К документам"
    if notification.get("type") == "email_demo":
        return "Открыть"
    if notification.get("type") == "law":
        return "К законам"
    return "К задаче"


def _mini_action(text: str, on_click=None) -> ft.Container:
    return ft.Container(
        height=32,
        padding=padding_symmetric(horizontal=12, vertical=7),
        border_radius=12,
        bgcolor=APP_COLORS["surface"],
        border=border_all(APP_COLORS["stroke2"]),
        on_click=on_click,
        ink=True,
        content=ft.Row(
            spacing=5,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text(text, size=ts(12), weight=ft.FontWeight.W_900, color=APP_COLORS["blue_text"], no_wrap=True),
                ft.Icon(ft.Icons.CHEVRON_RIGHT, size=ts(15), color=APP_COLORS["blue_text"]),
            ],
        ),
    )


def _notification_card(
    notification: dict,
    desktop: bool,
    on_mark_read=None,
    go_to=None,
    on_open_email_preview=None,
) -> ft.Container:
    tone = _tone(notification)
    palette = get_badge_palette()
    icon_bg, icon_fg = palette.get(tone, palette["blue"])
    unread = not notification.get("is_read")
    urgent = _is_urgent(notification)
    card_border = APP_COLORS["blue"] if unread else APP_COLORS["stroke2"]
    if urgent:
        card_border = APP_COLORS["red"]

    def mark_read(event=None) -> None:
        if on_mark_read:
            on_mark_read(notification.get("id"))

    def open_note(event=None) -> None:
        _open_notification(notification, on_mark_read, go_to, on_open_email_preview)

    badge_controls: list[ft.Control] = [badge(_type_label(notification), tone)]
    if urgent:
        badge_controls.append(badge("Срочно", "urgent"))
    if unread:
        badge_controls.append(badge("Новое", "blue"))

    right_controls: list[ft.Control] = [
        ft.Text(
            str(notification.get("date") or ""),
            size=ts(12),
            weight=ft.FontWeight.W_700,
            color=APP_COLORS["muted"],
            text_align=ft.TextAlign.RIGHT,
        )
    ]
    if unread:
        right_controls.append(
            ft.IconButton(
                icon=ft.Icons.CHECK,
                icon_size=17,
                icon_color=APP_COLORS["blue_text"],
                tooltip="Отметить прочитанным",
                width=34,
                height=34,
                on_click=mark_read,
            )
        )
    else:
        right_controls.append(ft.Icon(ft.Icons.DONE, size=ts(18), color=APP_COLORS["green"]))

    title_row = ft.Row(
        spacing=10,
        vertical_alignment=ft.CrossAxisAlignment.START,
        controls=[
            ft.Text(
                str(notification.get("title") or "Уведомление"),
                size=ts(17) if desktop else 15,
                weight=ft.FontWeight.W_900,
                color=APP_COLORS["text"],
                expand=True,
                max_lines=2,
            ),
            ft.Column(spacing=4, horizontal_alignment=ft.CrossAxisAlignment.END, controls=right_controls),
        ],
    )
    body = ft.Column(
        spacing=9,
        expand=True,
        controls=[
            title_row,
            ft.Text(
                str(notification.get("desc") or ""),
                size=ts(14) if desktop else 12,
                color=APP_COLORS["muted"],
                max_lines=3,
            ),
            ft.Row(spacing=8, run_spacing=8, wrap=True, controls=badge_controls),
            ft.Row(alignment=ft.MainAxisAlignment.END, controls=[_mini_action(_notification_action_text(notification), open_note)]),
        ],
    )
    content = ft.Row(
        spacing=12,
        vertical_alignment=ft.CrossAxisAlignment.START,
        controls=[
            ft.Stack(
                width=48 if desktop else 42,
                height=48 if desktop else 42,
                controls=[
                    icon_circle(
                        _icon(str(notification.get("type") or ""), str(notification.get("source") or "")),
                        color=icon_fg,
                        bgcolor=icon_bg,
                        size=48 if desktop else 42,
                    ),
                    ft.Container(width=9, height=9, border_radius=5, bgcolor=APP_COLORS["blue"], left=0, top=1) if unread else ft.Container(),
                ],
            ),
            body,
        ],
    )
    return ft.Container(
        animate=ft.Animation(220, ft.AnimationCurve.EASE_OUT),
        content=app_card(
            content,
            padding=18 if desktop else 14,
            bgcolor=APP_COLORS["active"] if unread else APP_COLORS["surface"],
            border_color=card_border,
        ),
        on_click=open_note,
        ink=True,
    )


def _empty_state(go_to=None) -> ft.Container:
    return empty_state_card(
        "Уведомлений по выбранному фильтру нет",
        "Здесь будут появляться задачи, документы, закон-апдейты и системные события.",
        "На главную",
        lambda _: go_to("/") if go_to else None,
        ft.Icons.DONE_ALL_OUTLINED,
    )


def _grouped_notifications(
    notifications: list[dict],
    desktop: bool,
    on_mark_read=None,
    go_to=None,
    on_open_email_preview=None,
) -> list[ft.Control]:
    if not notifications:
        return [_empty_state(go_to)]

    sections: list[ft.Control] = []
    for group_key, group_title in GROUP_TITLES:
        group_items = [item for item in notifications if _group_key(item) == group_key]
        if not group_items:
            continue
        group_cards = [
            _notification_card(item, desktop, on_mark_read, go_to, on_open_email_preview)
            for item in group_items
        ]
        sections.append(
            ft.Column(
                spacing=12,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Text(group_title, size=ts(20) if desktop else 17, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                            ft.Text(str(len(group_items)), size=ts(13), weight=ft.FontWeight.W_800, color=APP_COLORS["muted"]),
                        ],
                    ),
                    ft.Column(spacing=12, controls=group_cards),
                ],
            )
        )
    return sections


def _side_panel(notifications: list[dict], on_mark_all_read=None, go_to=None) -> ft.Column:
    type_rows = [
        ("Задачи", len([item for item in notifications if _matches_filter(item, "task")]), ft.Icons.TASK_ALT_OUTLINED, "blue"),
        ("Сроки", len([item for item in notifications if _is_urgent(item)]), ft.Icons.PRIORITY_HIGH_OUTLINED, "orange"),
        ("Документы", len([item for item in notifications if _matches_filter(item, "document")]), ft.Icons.DESCRIPTION_OUTLINED, "green"),
        ("Закон-апдейты", len([item for item in notifications if _matches_filter(item, "law")]), ft.Icons.BALANCE_OUTLINED, "purple"),
    ]
    settings = [
        ("Email", "важные события и сроки", ft.Icons.MARK_EMAIL_UNREAD_OUTLINED, "green"),
        ("Push", "будущий production-этап", ft.Icons.NOTIFICATIONS_ACTIVE_OUTLINED, "blue"),
        ("Законы", "показывать важные изменения", ft.Icons.BALANCE_OUTLINED, "purple"),
    ]

    type_controls: list[ft.Control] = []
    for title, count, icon, tone in type_rows:
        palette = get_badge_palette()
        bg, fg = palette.get(tone, palette["blue"])
        type_controls.append(
            ft.Container(
                padding=12,
                border_radius=16,
                bgcolor=APP_COLORS["surface2"],
                border=border_all(APP_COLORS["stroke2"]),
                content=ft.Row(
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        icon_circle(icon, size=34, color=fg, bgcolor=bg),
                        ft.Text(title, size=ts(13), weight=ft.FontWeight.W_800, color=APP_COLORS["text"], expand=True, max_lines=1),
                        badge(str(count), tone),
                    ],
                ),
            )
        )

    action_controls = [
        ghost_button("Отметить всё прочитанным", icon=ft.Icons.DONE_ALL, on_click=on_mark_all_read, expand=True),
        ghost_button("Открыть документы", icon=ft.Icons.DESCRIPTION_OUTLINED, on_click=lambda _: go_to("/documents") if go_to else None, expand=True),
        ghost_button("Закон-апдейты", icon=ft.Icons.BALANCE_OUTLINED, on_click=lambda _: go_to("/legal-updates") if go_to else None, expand=True),
    ]

    setting_controls: list[ft.Control] = []
    for title, subtitle, icon, tone in settings:
        palette = get_badge_palette()
        bg, fg = palette.get(tone, palette["blue"])
        setting_controls.append(
            ft.Container(
                padding=12,
                border_radius=16,
                bgcolor=APP_COLORS["surface2"],
                border=border_all(APP_COLORS["stroke2"]),
                content=ft.Row(
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        icon_circle(icon, size=34, color=fg, bgcolor=bg),
                        ft.Column(
                            spacing=1,
                            expand=True,
                            controls=[
                                ft.Text(title, size=ts(13), weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                                ft.Text(subtitle, size=ts(11), color=APP_COLORS["muted"], max_lines=1),
                            ],
                        ),
                        ft.Switch(value=title != "Push", active_color=APP_COLORS["blue"], disabled=True),
                    ],
                ),
            )
        )

    return ft.Column(
        spacing=16,
        controls=[
            app_card(
                ft.Column(
                    spacing=12,
                    controls=[
                        ft.Text("Типы уведомлений", size=ts(20), weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                        ft.Column(spacing=9, controls=type_controls),
                    ],
                ),
                padding=18,
            ),
            app_card(
                ft.Column(
                    spacing=10,
                    controls=[
                        ft.Text("Быстрые действия", size=ts(20), weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                        ft.Column(spacing=9, controls=action_controls),
                    ],
                ),
                padding=18,
            ),
            app_card(
                ft.Column(
                    spacing=10,
                    controls=[
                        ft.Text("Настройки уведомлений", size=ts(20), weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                        ft.Column(spacing=9, controls=setting_controls),
                    ],
                ),
                padding=18,
            ),
        ],
    )


def _build_dynamic_content(
    desktop: bool,
    notifications: list[dict],
    state: dict,
    refresh,
    on_mark_all_read=None,
    on_mark_read=None,
    go_to=None,
    on_open_email_preview=None,
) -> list[ft.Control]:
    filtered = _filter_notifications(notifications, state["query"], state["filter"])
    filter_row = ft.Row(
        wrap=True,
        spacing=8,
        run_spacing=8,
        controls=[
            _filter_chip(label, key == state["filter"], on_click=lambda _, filter_key=key: refresh(filter_key=filter_key))
            for key, label in FILTERS
        ],
    )
    main_controls = [
        search_box(
            value=state["query"],
            hint="Поиск по уведомлениям, задачам, документам и законам...",
            on_change=lambda event: refresh(query=event.control.value or ""),
        ),
        filter_row,
        _stats_row(notifications, desktop),
        ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text("Лента уведомлений", size=ts(24), weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                ft.Text("сгруппировано по важности", size=ts(12), color=APP_COLORS["muted2"]),
            ],
        ) if desktop else ft.Text("Лента уведомлений", size=ts(21), weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
        *_grouped_notifications(filtered, desktop, on_mark_read, go_to, on_open_email_preview),
    ]
    if desktop:
        return [
            ft.Row(
                spacing=22,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    ft.Column(spacing=18, expand=True, controls=main_controls),
                    ft.Container(width=320, content=_side_panel(notifications, on_mark_all_read, go_to)),
                ],
            )
        ]
    return [
        ft.Column(
            spacing=16,
            controls=[
                *main_controls,
                app_card(
                    ft.Column(
                        spacing=12,
                        controls=[
                            ft.Text("Настройки уведомлений", size=ts(18), weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                            ft.Container(
                                padding=12,
                                border_radius=16,
                                bgcolor=APP_COLORS["surface2"],
                                border=border_all(APP_COLORS["stroke2"]),
                                content=ft.Row(
                                    spacing=10,
                                    controls=[
                                        icon_circle(ft.Icons.MARK_EMAIL_UNREAD_OUTLINED, size=34, color=APP_COLORS["green"], bgcolor=get_badge_palette()["green"][0]),
                                        ft.Column(
                                            spacing=1,
                                            expand=True,
                                            controls=[
                                                ft.Text("Email", size=ts(13), weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                                                ft.Text("важные события и сроки", size=ts(11), color=APP_COLORS["muted"]),
                                            ],
                                        ),
                                        ft.Switch(value=True, active_color=APP_COLORS["blue"], disabled=True),
                                    ],
                                ),
                            ),
                        ],
                    ),
                    padding=16,
                ),
            ],
        )
    ]


def _page_content(
    desktop: bool,
    notifications: list[dict],
    on_mark_all_read=None,
    on_mark_read=None,
    go_to=None,
    on_open_email_preview=None,
) -> ft.Control:
    unread_count = len([item for item in notifications if not item.get("is_read")])
    state = {"filter": "all", "query": ""}
    dynamic_slot = ft.Column(spacing=18)

    def refresh(filter_key: str | None = None, query: str | None = None) -> None:
        if filter_key is not None:
            state["filter"] = filter_key
        if query is not None:
            state["query"] = query
        dynamic_slot.controls = _build_dynamic_content(
            desktop,
            notifications,
            state,
            refresh,
            on_mark_all_read,
            on_mark_read,
            go_to,
            on_open_email_preview,
        )
        dynamic_slot.update()

    if desktop:
        actions = [
            ft.Container(
                width=44,
                height=44,
                border_radius=22,
                bgcolor=APP_COLORS["active"],
                alignment=ft.Alignment(0, 0),
                content=ft.Text("А", size=ts(13), weight=ft.FontWeight.W_900, color=APP_COLORS["blue_text"]),
            ),
            ft.Container(
                width=44,
                height=44,
                border_radius=22,
                bgcolor=APP_COLORS["active"],
                alignment=ft.Alignment(0, 0),
                content=ft.Text(str(unread_count), size=ts(13), weight=ft.FontWeight.W_900, color=APP_COLORS["blue_text"]),
            ),
            ghost_button("Отметить всё прочитанным", on_click=on_mark_all_read, icon=ft.Icons.DONE_ALL),
        ]
        header = page_heading(
            "Уведомления",
            "Центр событий: задачи, сроки, документы, закон-апдейты и системные напоминания.",
            actions=actions,
        )
    else:
        header = ft.Column(
            spacing=8,
            controls=[
                ft.Text("Уведомления", size=ts(30), weight=ft.FontWeight.W_900, color=APP_COLORS["text"], max_lines=2),
                ft.Text(
                    "Центр событий: задачи, сроки, документы, закон-апдейты и системные напоминания.",
                    size=ts(13),
                    color=APP_COLORS["muted"],
                    max_lines=3,
                ),
                ft.Row(
                    alignment=ft.MainAxisAlignment.START,
                    controls=[_mini_action("Прочитать всё", on_mark_all_read)],
                ),
            ],
        )
    dynamic_slot.controls = _build_dynamic_content(
        desktop,
        notifications,
        state,
        refresh,
        on_mark_all_read,
        on_mark_read,
        go_to,
        on_open_email_preview,
    )
    return ft.Column(
        spacing=20 if desktop else 16,
        controls=[
            header,
            dynamic_slot,
        ],
    )


def build_notifications_page(
    is_desktop: bool = False,
    notifications: list[dict] | None = None,
    on_mark_all_read=None,
    on_mark_read=None,
    go_to=None,
    on_open_email_preview=None,
) -> ft.Control:
    content = _page_content(
        is_desktop,
        notifications or [],
        on_mark_all_read,
        on_mark_read,
        go_to,
        on_open_email_preview,
    )
    if is_desktop:
        return desktop_content(content, width=1120, top=46)
    return ft.Container(width=343, content=content)
