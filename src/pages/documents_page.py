"""Documents page — passport-card hero design with animated switching."""
from __future__ import annotations

from datetime import date

import flet as ft

from components.layout import desktop_content
from data.mock_data import MOCK_USER
from services.dashboard import parse_due_date
from theme.app_theme import (
    ts,
    ANIM_FAST,
    ANIM_NORMAL,
    APP_COLORS,
    APP_RADIUS,
    CENTER,
    GRADIENT_MIDNIGHT_SURGE,
    border_all,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _document_status(doc: dict, reminder_days: int = 30) -> str:
    expiry = parse_due_date(doc.get("expiry_date"))
    if not expiry:
        return doc.get("status", "Активен")
    days_left = (expiry - date.today()).days
    if days_left < 0:
        return "Истёк"
    if days_left <= reminder_days:
        return "Истекает скоро"
    return "Активен"


def _days_left(doc: dict) -> int | None:
    expiry = parse_due_date(doc.get("expiry_date"))
    if not expiry:
        return None
    return (expiry - date.today()).days


def _status_color(status: str) -> str:
    if status == "Активен":
        return APP_COLORS["green"]
    if status == "Истекает скоро":
        return APP_COLORS["orange"]
    return APP_COLORS["red"]


def _mask_number(value: str) -> str:
    clean = (value or "").strip()
    if not clean:
        return "Не указан"
    parts = clean.split()
    if len(parts) >= 2:
        # "КН 1234567" → "КН •••• 567"
        prefix = parts[0]
        num = parts[-1]
        suffix = num[-3:] if len(num) > 3 else num
        return f"{prefix} •••• {suffix}"
    if len(clean) <= 4:
        return "•" * len(clean)
    return f"{clean[:2]}{'•' * 4}{clean[-3:]}"


def _fmt_date(raw: str) -> str:
    """Format ISO or dotted date for display."""
    if not raw:
        return "—"
    try:
        from datetime import datetime
        if "-" in raw:
            return datetime.strptime(raw, "%Y-%m-%d").strftime("%d.%m.%Y")
        return raw  # already formatted
    except ValueError:
        return raw


def _display_number(doc: dict, hide_sensitive: bool, visible: bool) -> str:
    number = doc.get("document_number") or doc.get("details", "")
    if not number:
        return "Не указан"
    if hide_sensitive and not visible:
        return _mask_number(number)
    return number


def _enrich(docs: list[dict], reminder_days: int = 30) -> list[dict]:
    result = []
    for doc in docs:
        d = dict(doc)
        d["_status"] = _document_status(d, reminder_days)
        d["_days"] = _days_left(d)
        result.append(d)
    return result


# ---------------------------------------------------------------------------
# Security banner
# ---------------------------------------------------------------------------

def _security_banner() -> ft.Container:
    return ft.Container(
        border_radius=APP_RADIUS["card"],
        bgcolor=APP_COLORS["surface2"],
        padding=ft.Padding(left=18, top=14, right=18, bottom=14),
        content=ft.Row(
            spacing=14,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    width=38, height=38, border_radius=19,
                    bgcolor=APP_COLORS["active"],
                    alignment=CENTER,
                    content=ft.Icon(ft.Icons.SHIELD_OUTLINED, size=ts(20), color=APP_COLORS["blue"]),
                ),
                ft.Column(
                    spacing=2, expand=True,
                    controls=[
                        ft.Text("Защищено биометрией", size=ts(14), weight=ft.FontWeight.W_700, color=APP_COLORS["text"]),
                        ft.Text("Сканы хранятся локально на устройстве и шифруются ключом МСИ.", size=ts(12), color=APP_COLORS["muted"]),
                    ],
                ),
                ft.Icon(ft.Icons.FINGERPRINT, size=ts(28), color=APP_COLORS["blue_text"]),
            ],
        ),
    )


# ---------------------------------------------------------------------------
# Hero passport card
# ---------------------------------------------------------------------------

def _hero_card(doc: dict, show_number: bool = True) -> ft.Container:
    """Big gradient passport-style card."""
    status = doc.get("_status", "Активен")
    user_name = MOCK_USER.get("name", "Климович А.В.")

    number = _mask_number(doc.get("document_number") or "") if not show_number else (doc.get("document_number") or "Не указан")

    # Expiry badge
    expiry_badge: list[ft.Control] = []
    if status == "Истёк":
        expiry_badge = [
            ft.Container(
                content=ft.Text("ПРОСРОЧЕН", size=ts(9), weight=ft.FontWeight.W_800, color=APP_COLORS["red"]),
                padding=ft.Padding(left=8, top=3, right=8, bottom=3),
                border_radius=6,
                bgcolor=ft.Colors.with_opacity(0.18, APP_COLORS["red"]),
            )
        ]
    elif status == "Истекает скоро":
        expiry_badge = [
            ft.Container(
                content=ft.Text("ИСТЕКАЕТ", size=ts(9), weight=ft.FontWeight.W_800, color=APP_COLORS["orange"]),
                padding=ft.Padding(left=8, top=3, right=8, bottom=3),
                border_radius=6,
                bgcolor=ft.Colors.with_opacity(0.18, APP_COLORS["orange"]),
            )
        ]

    return ft.Container(
        border_radius=APP_RADIUS["hero"],
        animate=ft.Animation(ANIM_NORMAL, ft.AnimationCurve.EASE_OUT),
        gradient=ft.LinearGradient(
            begin=ft.Alignment(-1, -0.5),
            end=ft.Alignment(1, 1),
            colors=GRADIENT_MIDNIGHT_SURGE,
        ),
        shadow=[
            ft.BoxShadow(
                blur_radius=24,
                offset=ft.Offset(0, 12),
                color=ft.Colors.with_opacity(0.18, APP_COLORS["blue"]),
            )
        ],
        padding=ft.Padding(left=28, top=24, right=28, bottom=28),
        content=ft.Stack(
            expand=True,
            controls=[
                # Card content
                ft.Column(
                    spacing=0,
                    controls=[
                        # Top row: country + verified icon
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.START,
                            controls=[
                                ft.Text(
                                    "РЕСПУБЛИКА БЕЛАРУСЬ",
                                    size=ts(10),
                                    weight=ft.FontWeight.W_700,
                                    color=ft.Colors.with_opacity(0.65, ft.Colors.WHITE),
                                ),
                                ft.Container(
                                    width=34, height=34,
                                    border_radius=17,
                                    bgcolor=ft.Colors.with_opacity(0.18, ft.Colors.WHITE),
                                    alignment=CENTER,
                                    content=ft.Icon(ft.Icons.VERIFIED_OUTLINED, size=ts(18), color=ft.Colors.WHITE),
                                ),
                            ],
                        ),
                        ft.Container(height=6),
                        ft.Text(
                            doc.get("title", "Документ"),
                            size=ts(28),
                            weight=ft.FontWeight.W_900,
                            color=ft.Colors.WHITE,
                        ),
                        ft.Container(height=20),
                        # Field grid row 1: owner + number
                        ft.Row(
                            spacing=0,
                            controls=[
                                ft.Container(
                                    expand=True,
                                    content=ft.Column(
                                        spacing=3,
                                        controls=[
                                            ft.Text("ВЛАДЕЛЕЦ", size=ts(9), color=ft.Colors.with_opacity(0.6, ft.Colors.WHITE), weight=ft.FontWeight.W_700),
                                            ft.Text(user_name, size=ts(15), weight=ft.FontWeight.W_800, color=ft.Colors.WHITE),
                                        ],
                                    ),
                                ),
                                ft.Container(
                                    expand=True,
                                    content=ft.Column(
                                        spacing=3,
                                        controls=[
                                            ft.Text("НОМЕР", size=ts(9), color=ft.Colors.with_opacity(0.6, ft.Colors.WHITE), weight=ft.FontWeight.W_700),
                                            ft.Text(number, size=ts(15), weight=ft.FontWeight.W_800, color=ft.Colors.WHITE),
                                        ],
                                    ),
                                ),
                            ],
                        ),
                        ft.Container(height=16),
                        # Field grid row 2: issued + expiry
                        ft.Row(
                            spacing=0,
                            controls=[
                                ft.Container(
                                    expand=True,
                                    content=ft.Column(
                                        spacing=3,
                                        controls=[
                                            ft.Text("ВЫДАН", size=ts(9), color=ft.Colors.with_opacity(0.6, ft.Colors.WHITE), weight=ft.FontWeight.W_700),
                                            ft.Text(_fmt_date(doc.get("issue_date") or ""), size=ts(14), color=ft.Colors.WHITE),
                                        ],
                                    ),
                                ),
                                ft.Container(
                                    expand=True,
                                    content=ft.Column(
                                        spacing=3,
                                        controls=[
                                            ft.Text("ДО", size=ts(9), color=ft.Colors.with_opacity(0.6, ft.Colors.WHITE), weight=ft.FontWeight.W_700),
                                            ft.Row(
                                                spacing=8,
                                                controls=[
                                                    ft.Text(_fmt_date(doc.get("expiry_date") or ""), size=ts(14), color=ft.Colors.WHITE),
                                                    *expiry_badge,
                                                ],
                                            ),
                                        ],
                                    ),
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
    )


# ---------------------------------------------------------------------------
# Doc list row (right panel / mobile switcher)
# ---------------------------------------------------------------------------

def _validity_bar(status: str, total_days: int = 365 * 10) -> ft.Container:
    color = _status_color(status)
    progress = 0.7 if status == "Активен" else 0.25 if status == "Истекает скоро" else 0.05
    return ft.Container(
        height=4,
        border_radius=2,
        bgcolor=APP_COLORS["stroke2"],
        content=ft.Container(
            width=None,
            height=4,
            border_radius=2,
            bgcolor=color,
            # fraction via padding trick since ProgressBar has color issues in old Flet
        ),
        # Use ProgressBar as inner
        padding=0,
    )


def _doc_list_item(
    doc: dict,
    selected: bool,
    on_select,
) -> ft.Container:
    status = doc.get("_status", "Активен")
    days = doc.get("_days")
    color = _status_color(status)

    # Validity subtitle
    if status == "Истёк":
        subtitle = "Истёк"
    elif status == "Истекает скоро" and days is not None:
        subtitle = f"Истекает через {days} дн."
    else:
        expiry = doc.get("expiry_date")
        subtitle = f"Действует до {_fmt_date(expiry)}" if expiry else "Активен"

    # Validity bar value
    total = 3650  # 10 years default
    expiry = parse_due_date(doc.get("expiry_date"))
    issued = parse_due_date(doc.get("issue_date"))
    if expiry and issued:
        total = max(1, (expiry - issued).days)
    days_left_val = max(0, (days or 0))
    bar_value = min(1.0, days_left_val / max(1, total)) if days is not None else 0.7

    container = ft.Container(
        ink=True,
        border_radius=14,
        padding=ft.Padding(left=12, top=10, right=12, bottom=10),
        bgcolor=APP_COLORS["active"] if selected else None,
        border=border_all(APP_COLORS["blue"] if selected else APP_COLORS["stroke2"], 2 if selected else 1),
        animate=ft.Animation(ANIM_FAST, ft.AnimationCurve.EASE_OUT),
        on_click=lambda _: on_select(doc["id"]),
        content=ft.Column(
            spacing=6,
            controls=[
                ft.Row(
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Container(
                            width=32, height=32, border_radius=10,
                            bgcolor=APP_COLORS["surface2"],
                            alignment=CENTER,
                            content=ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, size=ts(16), color=APP_COLORS["blue"]),
                        ),
                        ft.Column(
                            spacing=1, expand=True,
                            controls=[
                                ft.Text(doc.get("title", "Документ"), size=ts(13), weight=ft.FontWeight.W_700, color=APP_COLORS["text"], max_lines=1, no_wrap=True),
                                ft.Text(subtitle, size=ts(11), color=APP_COLORS["muted"], max_lines=1),
                            ],
                        ),
                    ],
                ),
                ft.ProgressBar(
                    value=bar_value,
                    bar_height=4,
                    border_radius=2,
                    color=color,
                    bgcolor=APP_COLORS["stroke2"],
                ),
            ],
        ),
    )

    def _hover(e: ft.HoverEvent) -> None:
        if not selected:
            container.bgcolor = APP_COLORS["surface2"] if e.data == "true" else None
            container.update()

    container.on_hover = _hover
    return container


# ---------------------------------------------------------------------------
# Action buttons
# ---------------------------------------------------------------------------

def _action_button(label: str, icon, on_click=None, primary: bool = False) -> ft.Container:
    btn = ft.Container(
        ink=True,
        height=48,
        alignment=CENTER,
        border_radius=14,
        padding=ft.Padding(left=16, top=12, right=16, bottom=12),
        bgcolor=APP_COLORS["blue"] if primary else APP_COLORS["surface"],
        border=border_all(APP_COLORS["blue"] if primary else APP_COLORS["stroke2"]),
        animate=ft.Animation(ANIM_FAST, ft.AnimationCurve.EASE_OUT),
        on_click=on_click,
        content=ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(icon, size=ts(18), color=ft.Colors.WHITE if primary else APP_COLORS["blue"]),
                ft.Text(label, size=ts(14), weight=ft.FontWeight.W_700, color=ft.Colors.WHITE if primary else APP_COLORS["text"]),
            ],
        ),
    )

    def _hover(e: ft.HoverEvent) -> None:
        if primary:
            btn.bgcolor = APP_COLORS["blue_text"] if e.data == "true" else APP_COLORS["blue"]
        else:
            btn.bgcolor = APP_COLORS["surface2"] if e.data == "true" else APP_COLORS["surface"]
        btn.update()

    btn.on_hover = _hover
    return btn


def _scan_button(on_click=None) -> ft.Container:
    """Dashed border scan button matching screenshot."""
    return ft.Container(
        ink=True,
        border_radius=APP_RADIUS["card"],
        border=ft.Border(
            top=ft.BorderSide(1.5, APP_COLORS["stroke2"], ft.BorderSideStrokeAlign.CENTER),
            bottom=ft.BorderSide(1.5, APP_COLORS["stroke2"], ft.BorderSideStrokeAlign.CENTER),
            left=ft.BorderSide(1.5, APP_COLORS["stroke2"], ft.BorderSideStrokeAlign.CENTER),
            right=ft.BorderSide(1.5, APP_COLORS["stroke2"], ft.BorderSideStrokeAlign.CENTER),
        ),
        padding=ft.Padding(left=0, top=16, right=0, bottom=16),
        on_click=on_click,
        content=ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
            controls=[
                ft.Icon(ft.Icons.DOCUMENT_SCANNER_OUTLINED, size=ts(20), color=APP_COLORS["muted"]),
                ft.Text("Отсканировать новый документ", size=ts(14), weight=ft.FontWeight.W_600, color=APP_COLORS["muted"]),
            ],
        ),
    )


# ---------------------------------------------------------------------------
# Main builders (desktop / mobile)
# ---------------------------------------------------------------------------

def _build_layout(
    is_desktop: bool,
    docs: list[dict],
    hide_sensitive: bool,
    visible_ids: set,
    on_add_document=None,
    on_edit_document=None,
    on_delete_document=None,
    on_open_scan=None,
    on_toggle_sensitive=None,
    on_export_pdf=None,
    on_import_pdf=None,
    reminder_days: int = 30,
) -> ft.Control:
    if not docs:
        # Empty state
        return ft.Container(
            padding=24,
            content=ft.Column(
                spacing=16,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(ft.Icons.FOLDER_OPEN_OUTLINED, size=ts(56), color=APP_COLORS["muted2"]),
                    ft.Text("Нет документов", size=ts(22), weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                    ft.Text("Добавьте первый документ чтобы отслеживать сроки.", size=ts(14), color=APP_COLORS["muted"]),
                    _action_button("Добавить документ", ft.Icons.ADD, on_click=on_add_document, primary=True),
                ],
            ),
        )

    selected_state = {"id": docs[0]["id"]}
    show_number = {"v": not hide_sensitive or (docs[0]["id"] in visible_ids)}

    # AnimatedSwitcher for hero card transitions
    hero_switcher = ft.AnimatedSwitcher(
        transition=ft.AnimatedSwitcherTransition.FADE,
        duration=280,
        switch_in_curve=ft.AnimationCurve.EASE_OUT,
        switch_out_curve=ft.AnimationCurve.EASE_IN,
        content=_hero_card(docs[0], show_number["v"]),
        expand=True,
    )

    # Doc list column — will be rebuilt on selection
    doc_list_col = ft.Column(spacing=8, controls=[])

    def _rebuild_doc_list(do_update: bool = True) -> None:
        doc_list_col.controls = [
            _doc_list_item(doc, doc["id"] == selected_state["id"], _on_select)
            for doc in docs
        ]
        if do_update:
            doc_list_col.update()

    def _on_select(doc_id: str) -> None:
        if doc_id == selected_state["id"]:
            return
        selected_state["id"] = doc_id
        sel_doc = next((d for d in docs if d["id"] == doc_id), docs[0])
        show_number["v"] = not hide_sensitive or (doc_id in visible_ids)
        hero_switcher.content = _hero_card(sel_doc, show_number["v"])
        hero_switcher.update()
        _rebuild_doc_list()

    _rebuild_doc_list(do_update=False)

    # "Показать реквизиты" toggle
    reveal_btn = ft.Container(
        ink=True,
        border_radius=10,
        padding=ft.Padding(left=12, top=8, right=12, bottom=8),
        bgcolor=APP_COLORS["surface2"],
        content=ft.Row(
            spacing=6,
            controls=[
                ft.Icon(ft.Icons.VISIBILITY_OUTLINED, size=ts(16), color=APP_COLORS["muted"]),
                ft.Text("Показать реквизиты", size=ts(13), weight=ft.FontWeight.W_600, color=APP_COLORS["muted"]),
            ],
        ),
        on_click=lambda _: on_toggle_sensitive(None) if on_toggle_sensitive else None,
    )

    if is_desktop:
        # ── Desktop layout ───────────────────────────────────────────────
        return desktop_content(
            ft.Column(
                spacing=20,
                controls=[
                    # Page heading
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Column(
                                spacing=4,
                                controls=[
                                    ft.Text("Мои документы", size=ts(38), weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                                    ft.Text("Локальное хранилище. Защищено биометрией.", size=ts(15), color=APP_COLORS["muted"]),
                                ],
                            ),
                            reveal_btn,
                        ],
                    ),
                    # Security banner
                    _security_banner(),
                    # Hero + doc list row
                    ft.Row(
                        spacing=20,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                        controls=[
                            # Hero card (left)
                            ft.Container(expand=True, content=hero_switcher),
                            # Doc switcher list (right)
                            ft.Container(
                                width=280,
                                content=ft.Column(
                                    spacing=0,
                                    controls=[
                                        doc_list_col,
                                    ],
                                ),
                            ),
                        ],
                    ),
                    # Action bar
                    _scan_button(on_click=on_open_scan or on_add_document),
                    ft.Row(
                        spacing=12,
                        controls=[
                            ft.Container(expand=True, content=_action_button(
                                "Экспорт PDF", ft.Icons.PICTURE_AS_PDF_OUTLINED, on_click=on_export_pdf,
                            )),
                            ft.Container(expand=True, content=_action_button(
                                "Импорт PDF", ft.Icons.UPLOAD_FILE_OUTLINED, on_click=on_import_pdf,
                            )),
                            ft.Container(expand=True, content=_action_button(
                                "Добавить документ", ft.Icons.ADD, on_click=on_add_document, primary=True,
                            )),
                        ],
                    ),
                ],
            ),
            width=1100,
            top=36,
            bottom=60,
        )

    # ── Mobile layout ────────────────────────────────────────────────────
    return ft.Column(
        spacing=18,
        controls=[
            # Heading
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Column(
                        spacing=2,
                        controls=[
                            ft.Text("Мои документы", size=ts(28), weight=ft.FontWeight.W_900, color=APP_COLORS["text"]),
                            ft.Text("Защищено биометрией.", size=ts(13), color=APP_COLORS["muted"]),
                        ],
                    ),
                    reveal_btn,
                ],
            ),
            # Security banner
            _security_banner(),
            # Hero card
            hero_switcher,
            # Doc list
            doc_list_col,
            # Action bar
            _scan_button(on_click=on_open_scan or on_add_document),
            ft.Row(
                spacing=10,
                controls=[
                    ft.Container(expand=True, content=_action_button(
                        "Экспорт PDF", ft.Icons.PICTURE_AS_PDF_OUTLINED, on_click=on_export_pdf,
                    )),
                    ft.Container(expand=True, content=_action_button(
                        "Импорт PDF", ft.Icons.UPLOAD_FILE_OUTLINED, on_click=on_import_pdf,
                    )),
                ],
            ),
        ],
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

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
    on_export_pdf=None,
    on_import_pdf=None,
) -> ft.Control:
    dataset = _enrich(documents or [], reminder_days)
    visible_ids = set(visible_document_ids or set())
    return _build_layout(
        is_desktop=is_desktop,
        docs=dataset,
        hide_sensitive=hide_sensitive,
        visible_ids=visible_ids,
        on_add_document=on_add_document,
        on_edit_document=on_edit_document,
        on_delete_document=on_delete_document,
        on_open_scan=on_open_scan,
        on_toggle_sensitive=on_toggle_sensitive,
        on_export_pdf=on_export_pdf,
        on_import_pdf=on_import_pdf,
        reminder_days=reminder_days,
    )
