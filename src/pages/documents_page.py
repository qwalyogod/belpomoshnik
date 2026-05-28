from __future__ import annotations

from datetime import date

import flet as ft

from components.buttons import primary_button
from components.cards import app_card, badge, empty_state_card, hint_card, icon_circle, info_card, search_box
from components.layout import desktop_content
from services.dashboard import parse_due_date
from theme.app_theme import APP_COLORS, border_all, get_badge_palette, padding_symmetric


FILTERS = [
    ("all", "Все"),
    ("active", "Активные"),
    ("expiring", "Истекают скоро"),
    ("expired", "Истёкшие"),
    ("with_scan", "Со сканом"),
    ("without_scan", "Без файла"),
]


def _icon(name: str | None) -> str:
    return getattr(ft.Icons, name or "ARTICLE_OUTLINED", ft.Icons.ARTICLE_OUTLINED)


def _variant(status: str) -> str:
    if status == "Активен":
        return "success"
    if status == "Истекает скоро":
        return "warning"
    if status in {"Требуется обновление", "Истёк"}:
        return "error"
    return "default"


def _tone(status: str) -> tuple[str, str]:
    palette = get_badge_palette()
    if status == "Истекает скоро":
        return palette["orange"][1], palette["orange"][0]
    if status in {"Требуется обновление", "Истёк"}:
        return palette["red"][1], palette["red"][0]
    return palette["green"][1], palette["green"][0]


def _mask_value(value: str) -> str:
    clean_value = (value or "").strip()
    if not clean_value:
        return "Не указан"
    if len(clean_value) <= 4:
        return "×" * len(clean_value)
    return f"{clean_value[:2]}{'×' * max(4, len(clean_value) - 6)}{clean_value[-4:]}"


def _document_number(document: dict, hide_sensitive: bool, visible: bool) -> str:
    number = document.get("document_number") or document.get("details", "")
    if not number:
        return "Не указан"
    return number if visible or not hide_sensitive else _mask_value(number)


def _document_status(document: dict, reminder_days: int = 30) -> str:
    expiry = parse_due_date(document.get("expiry_date"))
    if not expiry:
        return document.get("status", "Активен")
    days_left = (expiry - date.today()).days
    if days_left < 0:
        return "Истёк"
    if days_left <= reminder_days:
        return "Истекает скоро"
    return "Активен"


def _group_documents(documents: list[dict], reminder_days: int = 30) -> tuple[list[dict], list[dict], list[dict]]:
    overdue, expiring, normal = [], [], []
    for document in documents:
        enriched = dict(document)
        enriched["status"] = _document_status(enriched, reminder_days)
        if enriched["status"] == "Истёк":
            overdue.append(enriched)
        elif enriched["status"] == "Истекает скоро":
            expiring.append(enriched)
        else:
            normal.append(enriched)
    return overdue, expiring, normal


def _filter_chip(label: str, selected: bool = False) -> ft.Container:
    return ft.Container(
        content=ft.Text(
            label,
            size=13,
            weight=ft.FontWeight.W_800,
            color=ft.Colors.WHITE if selected else APP_COLORS["text"],
            no_wrap=True,
        ),
        padding=padding_symmetric(horizontal=14, vertical=8),
        border_radius=18,
        bgcolor=APP_COLORS["blue"] if selected else APP_COLORS["surface2"],
        border=border_all(APP_COLORS["blue"] if selected else APP_COLORS["stroke2"]),
    )


def _filter_bar() -> ft.Row:
    return ft.Row(
        wrap=True,
        spacing=8,
        run_spacing=8,
        controls=[
            _filter_chip(label, key == "all")
            for key, label in FILTERS
        ],
    )


def _stat_tile(label: str, value: str | int, icon: str, tone: str = "blue", compact: bool = False) -> ft.Container:
    palette = get_badge_palette()
    bg, fg = palette.get(tone, palette["blue"])
    if compact:
        return ft.Container(
            padding=12,
            border_radius=18,
            bgcolor=APP_COLORS["surface"],
            border=border_all(APP_COLORS["stroke2"]),
            content=ft.Row(
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    icon_circle(icon, color=fg, bgcolor=bg, size=36),
                    ft.Column(
                        spacing=0,
                        controls=[
                            ft.Text(str(value), size=20, weight=ft.FontWeight.W_900, color=fg),
                            ft.Text(label, size=11, color=APP_COLORS["muted"], weight=ft.FontWeight.W_700),
                        ],
                    ),
                ],
            ),
        )
    return ft.Container(
        padding=16,
        border_radius=22,
        bgcolor=APP_COLORS["surface"],
        border=border_all(APP_COLORS["stroke2"]),
        content=ft.Column(
            spacing=8,
            controls=[
                icon_circle(icon, color=fg, bgcolor=bg, size=42),
                ft.Text(str(value), size=25, weight=ft.FontWeight.W_900, color=fg),
                ft.Text(label, size=12, color=APP_COLORS["muted"], weight=ft.FontWeight.W_700),
            ],
        ),
    )


def _stats_row(documents: list[dict], desktop: bool, reminder_days: int = 30) -> ft.Control:
    overdue, expiring, normal = _group_documents(documents, reminder_days)
    active = len([doc for doc in normal if _document_status(doc, reminder_days) == "Активен"])
    tiles = [
        _stat_tile("Всего", len(documents), ft.Icons.FOLDER_OUTLINED, "blue", not desktop),
        _stat_tile("Активны", active, ft.Icons.CHECK_CIRCLE_OUTLINE, "green", not desktop),
        _stat_tile("Истекают", len(expiring), ft.Icons.SCHEDULE_OUTLINED, "orange", not desktop),
        _stat_tile("Истёкшие", len(overdue), ft.Icons.ERROR_OUTLINE, "red", not desktop),
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


def _metadata_item(label: str, value: str, icon: str | None = None) -> ft.Column:
    label_row_controls: list[ft.Control] = []
    if icon:
        label_row_controls.append(ft.Icon(icon, size=14, color=APP_COLORS["muted2"]))
    label_row_controls.append(ft.Text(label, size=11, weight=ft.FontWeight.W_700, color=APP_COLORS["muted2"]))
    return ft.Column(
        spacing=3,
        controls=[
            ft.Row(spacing=5, controls=label_row_controls),
            ft.Text(value or "Не указано", size=13, weight=ft.FontWeight.W_700, color=APP_COLORS["text"], max_lines=2),
        ],
    )


def _scan_placeholder(document: dict, compact: bool = False) -> ft.Container:
    status = document.get("status", "Активен")
    color, bg = _tone(status)
    return ft.Container(
        width=54 if compact else 62,
        height=72 if compact else 82,
        border_radius=16,
        bgcolor=bg,
        border=border_all(APP_COLORS["stroke2"]),
        padding=6,
        content=ft.Container(
            alignment=ft.Alignment(0, 0),
            border_radius=12,
            border=border_all(APP_COLORS["stroke2"]),
            content=ft.Column(
                spacing=3,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(_icon(document.get("icon")), size=20, color=color),
                    ft.Text("скан", size=9, color=APP_COLORS["muted2"], text_align=ft.TextAlign.CENTER),
                ],
            ),
        ),
    )


def _status_strip(status: str) -> str:
    color, _ = _tone(status)
    return color


def _doc_card(
    document: dict,
    desktop: bool,
    hide_sensitive: bool,
    visible: bool,
    on_edit_document=None,
    on_delete_document=None,
    on_toggle_sensitive=None,
    on_open_scan=None,
) -> ft.Container:
    status = document.get("status", "Активен")
    has_sensitive = bool(document.get("document_number") or document.get("details"))
    scan_path = document.get("scan_path", "")
    number_text = _document_number(document, hide_sensitive, visible)
    expiry = document.get("expiry_date") or "Не указан"
    issue = document.get("issue_date") or "Не указана"
    issuer = document.get("issuer") or "Не указано"
    scan_text = "Скан загружен" if scan_path else "Файл не добавлен"

    edit_actions = ft.Row(
        spacing=0,
        controls=[
            ft.IconButton(
                icon=ft.Icons.EDIT_OUTLINED,
                icon_size=20,
                icon_color=APP_COLORS["muted2"],
                tooltip="Редактировать",
                on_click=lambda _, doc_id=document["id"]: on_edit_document(doc_id) if on_edit_document else None,
            ),
            ft.IconButton(
                icon=ft.Icons.DELETE_OUTLINE,
                icon_size=20,
                icon_color=APP_COLORS["red"],
                tooltip="Удалить",
                on_click=lambda _, doc_id=document["id"]: on_delete_document(doc_id) if on_delete_document else None,
            ),
        ],
    )

    number_actions: list[ft.Control] = []
    if scan_path:
        number_actions.append(
            ft.IconButton(
                icon=ft.Icons.ATTACH_FILE,
                icon_size=16,
                icon_color=APP_COLORS["blue_text"],
                tooltip="Открыть скан",
                on_click=lambda _, doc_id=document["id"]: on_open_scan(doc_id) if on_open_scan else None,
            )
        )
    if hide_sensitive and has_sensitive:
        number_actions.append(
            ft.IconButton(
                icon=ft.Icons.VISIBILITY_OFF_OUTLINED if visible else ft.Icons.VISIBILITY_OUTLINED,
                icon_size=16,
                icon_color=APP_COLORS["blue_text"],
                tooltip="Скрыть данные" if visible else "Показать данные",
                on_click=lambda _, doc_id=document["id"]: on_toggle_sensitive(doc_id) if on_toggle_sensitive else None,
            )
        )
    else:
        number_actions.append(
            ft.Icon(
                ft.Icons.LOCK_OPEN_OUTLINED if visible else ft.Icons.LOCK_OUTLINE,
                size=16,
                color=APP_COLORS["muted2"],
            )
        )

    number_box = ft.Container(
        padding=padding_symmetric(horizontal=14, vertical=10),
        border_radius=16,
        bgcolor=APP_COLORS["surface2"],
        border=border_all(APP_COLORS["stroke2"]),
        content=ft.Row(
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(ft.Icons.BADGE_OUTLINED, size=17, color=APP_COLORS["blue_text"]),
                ft.Text(number_text, size=14, weight=ft.FontWeight.W_900, color=APP_COLORS["text"], expand=True),
            ] + number_actions,
        ),
    )

    meta_grid = ft.Column(
        spacing=12,
        controls=[
            ft.Row(
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    ft.Container(expand=True, content=_metadata_item("Дата выдачи", issue, ft.Icons.EVENT_AVAILABLE_OUTLINED)),
                    ft.Container(expand=True, content=_metadata_item("Срок действия", expiry, ft.Icons.SCHEDULE_OUTLINED)),
                ],
            ),
            ft.Row(
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    ft.Container(expand=True, content=_metadata_item("Организация", issuer, ft.Icons.ACCOUNT_BALANCE_OUTLINED)),
                    ft.Container(expand=True, content=_metadata_item("Файл / скан", scan_text, ft.Icons.ATTACH_FILE)),
                ],
            ),
        ],
    )

    warning: ft.Control | None = None
    if status == "Истекает скоро":
        warning = ft.Container(
            padding=padding_symmetric(horizontal=12, vertical=9),
            border_radius=14,
            bgcolor=get_badge_palette()["orange"][0],
            content=ft.Text("Истекает скоро — проверьте замену", size=12, weight=ft.FontWeight.W_800, color=get_badge_palette()["orange"][1]),
        )
    if status == "Истёк":
        warning = ft.Container(
            padding=padding_symmetric(horizontal=12, vertical=9),
            border_radius=14,
            bgcolor=get_badge_palette()["red"][0],
            content=ft.Text("Срок истёк — требуется замена", size=12, weight=ft.FontWeight.W_800, color=get_badge_palette()["red"][1]),
        )

    card_controls: list[ft.Control] = [
        ft.Container(height=5, border_radius=3, bgcolor=_status_strip(status)),
        ft.Row(
            spacing=14,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                _scan_placeholder(document, not desktop),
                ft.Column(
                    spacing=8,
                    expand=True,
                    controls=[
                        ft.Row(
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.START,
                            controls=[
                                ft.Column(
                                    spacing=6,
                                    expand=True,
                                    controls=[
                                        ft.Text(document.get("title", "Документ"), size=19 if desktop else 16, weight=ft.FontWeight.W_900, color=APP_COLORS["text"], max_lines=2),
                                        ft.Text(document.get("document_type", "Другое"), size=12, weight=ft.FontWeight.W_700, color=APP_COLORS["muted"]),
                                    ],
                                ),
                                badge(status, _variant(status)),
                            ],
                        ),
                        number_box,
                    ],
                ),
            ] + ([edit_actions] if desktop else []),
        ),
        meta_grid,
    ]
    if document.get("comment"):
        card_controls.append(ft.Text(document.get("comment", ""), size=12, color=APP_COLORS["muted"], max_lines=2))
    if warning:
        card_controls.append(warning)
    if not desktop:
        card_controls.append(edit_actions)

    return app_card(
        ft.Column(
            spacing=13,
            controls=card_controls,
        ),
        padding=18 if desktop else 14,
    )


def _security_card(hide_sensitive: bool, on_privacy_change=None) -> ft.Container:
    return app_card(
        ft.Column(
            spacing=14,
            controls=[
                ft.Row(
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    controls=[
                        icon_circle(ft.Icons.PRIVACY_TIP_OUTLINED, color=APP_COLORS["blue_text"], bgcolor=APP_COLORS["active"], size=48),
                        ft.Column(
                            spacing=5,
                            expand=True,
                            controls=[
                                ft.Text("Защита данных", size=20, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                                ft.Text("Личные номера скрыты по умолчанию. Перед просмотром скана показывается предупреждение.", size=13, color=APP_COLORS["muted"]),
                            ],
                        ),
                    ],
                ),
                ft.Container(
                    padding=14,
                    border_radius=18,
                    bgcolor=APP_COLORS["surface2"],
                    border=border_all(APP_COLORS["stroke2"]),
                    content=ft.Row(
                        spacing=10,
                        controls=[
                            ft.Icon(ft.Icons.LOCK_OUTLINE, size=20, color=APP_COLORS["blue_text"]),
                            ft.Column(
                                spacing=3,
                                expand=True,
                                controls=[
                                    ft.Text("Маскирование номера", size=13, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                                    ft.Text("Включено" if hide_sensitive else "Выключено", size=12, color=APP_COLORS["muted"]),
                                ],
                            ),
                            ft.Switch(
                                value=hide_sensitive,
                                active_color=APP_COLORS["blue"],
                                on_change=lambda event: on_privacy_change(bool(event.control.value)) if on_privacy_change else None,
                            ),
                        ],
                    ),
                ),
                ft.Container(
                    padding=14,
                    border_radius=18,
                    bgcolor=APP_COLORS["surface2"],
                    border=border_all(APP_COLORS["stroke2"]),
                    content=ft.Row(
                        spacing=10,
                        controls=[
                            ft.Icon(ft.Icons.NOTIFICATIONS_ACTIVE_OUTLINED, size=20, color=APP_COLORS["orange"]),
                            ft.Text("Напоминания по срокам документов включены в демо-режиме.", size=12, color=APP_COLORS["muted"], expand=True),
                        ],
                    ),
                ),
            ],
        ),
        padding=20,
    )


def _scan_warning_card() -> ft.Container:
    return info_card(
        "Предупреждение перед просмотром скана",
        "Перед открытием файла приложение показывает предупреждение: документ содержит личные данные.",
        ft.Icons.WARNING_AMBER_OUTLINED,
        "warning",
    )


def _document_form_hint(on_add_document=None) -> ft.Container:
    rows = [
        ("Тип документа", "ID / паспорт / медкнижка"),
        ("Серия / номер", "хранится с маской"),
        ("Дата выдачи", "дд.мм.гггг"),
        ("Срок действия", "автостатус"),
        ("Организация", "кто выдал"),
        ("Комментарий", "личная заметка"),
    ]
    return app_card(
        ft.Column(
            spacing=12,
            controls=[
                ft.Text("Форма документа", size=20, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                ft.Column(
                    spacing=8,
                    controls=[
                        ft.Container(
                            padding=padding_symmetric(horizontal=12, vertical=8),
                            border_radius=14,
                            bgcolor=APP_COLORS["surface2"],
                            border=border_all(APP_COLORS["stroke2"]),
                            content=ft.Row(
                                spacing=8,
                                controls=[
                                    ft.Text(label, size=12, weight=ft.FontWeight.W_900, color=APP_COLORS["text"], expand=True),
                                    ft.Text(value, size=12, color=APP_COLORS["muted"], expand=True),
                                ],
                            ),
                        )
                        for label, value in rows
                    ],
                ),
                primary_button("Добавить документ", icon=ft.Icons.ADD, expand=True, on_click=on_add_document),
            ],
        ),
        padding=20,
    )


def _activity_log_card(log: list[dict]) -> ft.Container | None:
    if not log:
        return None
    action_labels = {"created": "Добавлен", "updated": "Изменён", "deleted": "Удалён"}
    action_variants = {"created": "success", "updated": "blue", "deleted": "error"}
    return app_card(
        ft.Column(
            spacing=12,
            controls=[
                ft.Row(
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(ft.Icons.HISTORY_OUTLINED, size=22, color=APP_COLORS["blue_text"]),
                        ft.Text("Журнал изменений", size=20, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                    ],
                ),
                ft.Column(
                    spacing=7,
                    controls=[
                        ft.Row(
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                badge(action_labels.get(entry.get("action", ""), entry.get("action", "")), action_variants.get(entry.get("action", ""), "default")),
                                ft.Text(entry.get("doc_title", ""), size=13, color=APP_COLORS["text"], expand=True),
                                ft.Text(entry.get("date", ""), size=11, color=APP_COLORS["muted"]),
                            ],
                        )
                        for entry in reversed(log[-8:])
                    ],
                ),
            ],
        ),
        padding=18,
    )


def _documents_list(
    documents: list[dict],
    desktop: bool,
    hide_sensitive: bool,
    visible_ids: set[str],
    on_add_document=None,
    on_edit_document=None,
    on_delete_document=None,
    on_toggle_sensitive=None,
    on_open_scan=None,
    reminder_days: int = 30,
) -> ft.Control:
    overdue, expiring, normal = _group_documents(documents, reminder_days)
    ordered_documents = overdue + expiring + normal
    if not ordered_documents:
        return empty_state_card(
            "Документов пока нет",
            "Добавьте паспорт, медкнижку или другой важный документ, чтобы отслеживать сроки и хранить реквизиты.",
            "Добавить документ",
            on_add_document,
            ft.Icons.DESCRIPTION_OUTLINED,
        )
    return ft.Column(
        spacing=14,
        controls=[
            _doc_card(
                document,
                desktop,
                hide_sensitive,
                str(document.get("id")) in visible_ids,
                on_edit_document,
                on_delete_document,
                on_toggle_sensitive,
                on_open_scan,
            )
            for document in ordered_documents
        ],
    )


def _desktop_documents(
    documents: list[dict],
    hide_sensitive: bool,
    visible_ids: set[str],
    on_add_document=None,
    on_edit_document=None,
    on_delete_document=None,
    on_toggle_sensitive=None,
    on_privacy_change=None,
    on_open_scan=None,
    reminder_days: int = 30,
    activity_log: list[dict] | None = None,
) -> ft.Control:
    left_controls: list[ft.Control] = [
        ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                ft.Column(
                    spacing=8,
                    expand=True,
                    controls=[
                        ft.Text("Документы", size=40, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                        ft.Text("Личный сейф документов: реквизиты, сроки действия, сканы и напоминания.", size=15, color=APP_COLORS["muted"]),
                    ],
                ),
                ft.Row(
                    spacing=10,
                    controls=[
                        icon_circle(ft.Icons.PERSON_OUTLINE, color=APP_COLORS["blue_text"], bgcolor=APP_COLORS["active"], size=42),
                        icon_circle(ft.Icons.NOTIFICATIONS_NONE_OUTLINED, color=APP_COLORS["blue_text"], bgcolor=APP_COLORS["active"], size=42),
                    ],
                ),
            ],
        ),
        ft.Row(
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(expand=True, content=search_box(hint="Поиск по документам, номеру, сроку или организации...")),
                primary_button("Добавить документ", icon=ft.Icons.ADD, width=210, height=50, on_click=on_add_document),
            ],
        ),
        _filter_bar(),
        _stats_row(documents, True, reminder_days),
        ft.Row(
            spacing=10,
            controls=[
                ft.Text("Мои личные документы", size=24, weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                badge("Маскирование включено" if hide_sensitive else "Данные видны", "success" if hide_sensitive else "warning"),
            ],
        ),
        _documents_list(
            documents,
            True,
            hide_sensitive,
            visible_ids,
            on_add_document,
            on_edit_document,
            on_delete_document,
            on_toggle_sensitive,
            on_open_scan,
            reminder_days,
        ),
    ]
    log_card = _activity_log_card(activity_log or [])
    if log_card:
        left_controls.append(log_card)

    right_controls = [
        _security_card(hide_sensitive, on_privacy_change),
        _scan_warning_card(),
        _document_form_hint(on_add_document),
        hint_card("Номера документов лучше показывать только после подтверждения. Сканы остаются локально в демо-версии.", ft.Icons.LIGHTBULB_OUTLINE),
    ]

    return desktop_content(
        ft.Row(
            spacing=26,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                ft.Column(spacing=20, expand=True, controls=left_controls),
                ft.Column(spacing=16, width=330, controls=right_controls),
            ],
        ),
        width=1180,
        top=46,
        bottom=120,
    )


def _mobile_documents(
    documents: list[dict],
    hide_sensitive: bool,
    visible_ids: set[str],
    on_add_document=None,
    on_edit_document=None,
    on_delete_document=None,
    on_toggle_sensitive=None,
    on_privacy_change=None,
    on_open_scan=None,
    reminder_days: int = 30,
    activity_log: list[dict] | None = None,
) -> ft.Control:
    controls: list[ft.Control] = [
        ft.Row(
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(ft.Icons.ARROW_BACK, size=21, color=APP_COLORS["muted"]),
                ft.Text("Документы", size=22, weight=ft.FontWeight.W_900, color=APP_COLORS["text"], expand=True),
                icon_circle(ft.Icons.PERSON_OUTLINE, color=APP_COLORS["blue_text"], bgcolor=APP_COLORS["active"], size=36),
                icon_circle(ft.Icons.NOTIFICATIONS_NONE_OUTLINED, color=APP_COLORS["blue_text"], bgcolor=APP_COLORS["active"], size=36),
            ],
        ),
        primary_button("Добавить документ", icon=ft.Icons.ADD, expand=True, on_click=on_add_document),
        search_box(hint="Поиск по документам...", expand=False),
        _filter_bar(),
        _stats_row(documents, False, reminder_days),
        ft.Row(
            spacing=8,
            controls=[
                ft.Text("Мои документы", size=20, weight=ft.FontWeight.W_900, color=APP_COLORS["text"], expand=True),
                ft.Text("Скрыто" if hide_sensitive else "Видно", size=12, weight=ft.FontWeight.W_900, color=APP_COLORS["green"] if hide_sensitive else APP_COLORS["orange"]),
            ],
        ),
        _documents_list(
            documents,
            False,
            hide_sensitive,
            visible_ids,
            on_add_document,
            on_edit_document,
            on_delete_document,
            on_toggle_sensitive,
            on_open_scan,
            reminder_days,
        ),
        _security_card(hide_sensitive, on_privacy_change),
        _scan_warning_card(),
    ]
    log_card = _activity_log_card(activity_log or [])
    if log_card:
        controls.append(log_card)
    return ft.Container(width=340, content=ft.Column(spacing=16, controls=controls))


def build_documents_page(
    is_desktop: bool = False,
    documents: list[dict] | None = None,
    on_add_document=None,
    on_edit_document=None,
    on_delete_document=None,
    hide_sensitive: bool = True,
    visible_document_ids: set[str] | None = None,
    on_toggle_sensitive=None,
    on_privacy_change=None,
    on_open_scan=None,
    reminder_days: int = 30,
    activity_log: list[dict] | None = None,
) -> ft.Control:
    dataset = documents or []
    visible_ids = set(visible_document_ids or set())
    if is_desktop:
        return _desktop_documents(
            dataset,
            hide_sensitive,
            visible_ids,
            on_add_document,
            on_edit_document,
            on_delete_document,
            on_toggle_sensitive,
            on_privacy_change,
            on_open_scan,
            reminder_days,
            activity_log,
        )
    return _mobile_documents(
        dataset,
        hide_sensitive,
        visible_ids,
        on_add_document,
        on_edit_document,
        on_delete_document,
        on_toggle_sensitive,
        on_privacy_change,
        on_open_scan,
        reminder_days,
        activity_log,
    )
