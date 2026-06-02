import flet as ft

from components.buttons import primary_button, secondary_button
from components.cards import app_card, badge, empty_state_card, hint_card, info_card, page_heading
from components.layout import desktop_content
from services.dashboard import parse_due_date
from theme.app_theme import APP_COLORS, border_all, padding_symmetric, ts


_STATUS_VARIANT = {
    "Оплачено": "success",
    "Просрочено": "error",
    "Предстоит": "warning",
}

_USER_TYPE_LABELS = {
    "individual": "Физлицо",
    "ip": "ИП",
}

_EMPLOYMENT_TO_USER_TYPE = {
    "ip": "ip",
    "employee": "individual",
    "student": "individual",
    "pensioner": "individual",
    "unemployed": "individual",
}


def _days_label(deadline_raw: str | None) -> tuple[str, str]:
    from datetime import date
    d = parse_due_date(deadline_raw)
    if not d:
        return "", APP_COLORS["muted"]
    days = (d - date.today()).days
    if days < 0:
        return "Просрочено на " + str(-days) + " дн.", APP_COLORS["danger"]
    if days == 0:
        return "Срок сегодня", APP_COLORS["warning"]
    if days <= 7:
        return "Через " + str(days) + " дн.", APP_COLORS["warning"]
    if days <= 30:
        return "Через " + str(days) + " дн.", APP_COLORS["primary"]
    return "до " + d.strftime("%d.%m.%Y"), APP_COLORS["muted"]


def _obligation_card(
    obligation: dict,
    on_edit=None,
    on_delete=None,
    on_mark_paid=None,
) -> ft.Container:
    status = obligation.get("status", "Предстоит")
    days_text, days_color = _days_label(obligation.get("deadline"))
    amount = obligation.get("amount", 0)
    amount_text = (str(amount) + " руб.") if amount else "сумма не указана"
    user_type = _USER_TYPE_LABELS.get(obligation.get("user_type", "individual"), "Физлицо")

    border_color = {
        "Просрочено": APP_COLORS["danger"],
        "Предстоит": APP_COLORS["warning"] if days_text and "дн." in days_text and int(days_text.split()[1]) <= 30 else APP_COLORS["border_soft"],
    }.get(status, APP_COLORS["border_soft"])

    return app_card(
        ft.Column(
            spacing=10,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    controls=[
                        ft.Column(
                            spacing=6,
                            expand=True,
                            controls=[
                                ft.Row(
                                    wrap=True,
                                    spacing=6,
                                    controls=[
                                        badge(status, _STATUS_VARIANT.get(status, "default")),
                                        badge(user_type, "active" if obligation.get("user_type") == "ip" else "default"),
                                        badge(obligation.get("period", ""), "default") if obligation.get("period") else ft.Container(),
                                    ],
                                ),
                                ft.Text(obligation.get("title", "Налоговое обязательство"), size=ts(16), weight=ft.FontWeight.BOLD, color=APP_COLORS["text"]),
                            ],
                        ),
                        ft.Row(
                            spacing=4,
                            controls=[
                                ft.IconButton(ft.Icons.EDIT_OUTLINED, icon_size=18, icon_color=APP_COLORS["muted"], tooltip="Редактировать", on_click=lambda _, oid=obligation["id"]: on_edit(oid) if on_edit else None),
                                ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_size=18, icon_color=APP_COLORS["danger"], tooltip="Удалить", on_click=lambda _, oid=obligation["id"]: on_delete(oid) if on_delete else None),
                            ],
                        ),
                    ],
                ),
                ft.Row(
                    wrap=True,
                    spacing=16,
                    run_spacing=4,
                    controls=[
                        ft.Row(spacing=4, controls=[ft.Icon(ft.Icons.CALENDAR_TODAY_OUTLINED, size=ts(14), color=APP_COLORS["muted"]), ft.Text("Срок: " + (obligation.get("deadline") or "—"), size=ts(12), color=APP_COLORS["muted"])]),
                        ft.Row(spacing=4, controls=[ft.Icon(ft.Icons.MONETIZATION_ON_OUTLINED, size=ts(14), color=APP_COLORS["muted"]), ft.Text("Сумма: " + amount_text, size=ts(12), color=APP_COLORS["muted"])]),
                        *([ft.Row(spacing=4, controls=[ft.Icon(ft.Icons.ATTACH_FILE_OUTLINED, size=ts(14), color=APP_COLORS["muted"]), ft.Text("Квитанция прикреплена", size=ts(12), color=APP_COLORS["muted"])])] if obligation.get("receipt_path") else []),
                    ],
                ),
                *([ft.Text(days_text, size=ts(13), color=days_color, weight=ft.FontWeight.W_600)] if days_text else []),
                *([ft.Text(obligation.get("comment", ""), size=ts(12), color=APP_COLORS["muted"])] if obligation.get("comment") else []),
                ft.Row(
                    spacing=8,
                    controls=[
                        secondary_button("Отметить оплаченным", icon=ft.Icons.CHECK_CIRCLE_OUTLINE, on_click=lambda _, oid=obligation["id"]: on_mark_paid(oid) if on_mark_paid else None, expand=True)
                        if status != "Оплачено"
                        else ft.Container(),
                    ],
                ) if status != "Оплачено" else ft.Container(),
            ],
        ),
        padding=16,
        border_color=border_color,
    )


def _user_type_hint(user: dict | None) -> ft.Control | None:
    employment = (user or {}).get("employment_status", "")
    mapped = _EMPLOYMENT_TO_USER_TYPE.get(employment, "")
    if mapped == "ip":
        return hint_card("Вы зарегистрированы как ИП. Показаны все обязательства физлица и ИП.", ft.Icons.BUSINESS_CENTER_OUTLINED)
    if mapped == "individual":
        return hint_card("Показаны налоговые обязательства физлица. Если вы ИП — обновите статус занятости в профиле.", ft.Icons.PERSON_OUTLINED)
    return None


def _build_content(
    obligations: list[dict],
    on_add=None,
    on_edit=None,
    on_delete=None,
    on_mark_paid=None,
    user: dict | None = None,
    is_desktop: bool = False,
) -> ft.Column:
    overdue = [o for o in obligations if o.get("status") == "Просрочено"]
    upcoming = [o for o in obligations if o.get("status") == "Предстоит"]
    paid = [o for o in obligations if o.get("status") == "Оплачено"]

    def _sort_by_deadline(lst: list[dict]) -> list[dict]:
        from datetime import date
        return sorted(lst, key=lambda o: parse_due_date(o.get("deadline")) or date.max)

    header_row = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            page_heading("Налоговый трекер", "Локальный учёт налоговых обязательств без подключения к ФНС."),
            primary_button("Добавить обязательство", icon=ft.Icons.ADD, width=240, height=48, on_click=on_add) if is_desktop else ft.Container(),
        ],
    ) if is_desktop else page_heading("Налоговый трекер", "Локальный учёт налоговых обязательств.")

    controls: list[ft.Control] = [
        header_row,
        info_card(
            "Ограничения MVP",
            "Данные хранятся локально. Реальный обмен с налоговой службой не производится. "
            "Production-версия подключится к личному кабинету nalog.gov.by.",
            ft.Icons.INFO_OUTLINE,
            "blue",
        ),
    ]

    user_hint = _user_type_hint(user)
    if user_hint:
        controls.append(user_hint)

    if not obligations:
        controls.append(
            empty_state_card(
                "Обязательств нет",
                "Добавьте налоговое обязательство, чтобы отслеживать сроки и суммы.",
                "Добавить обязательство",
                on_add,
                ft.Icons.RECEIPT_LONG_OUTLINED,
            )
        )
    else:
        if overdue:
            controls.append(ft.Text("Просроченные", size=ts(18), weight=ft.FontWeight.BOLD, color=APP_COLORS["danger"]))
            for o in _sort_by_deadline(overdue):
                controls.append(_obligation_card(o, on_edit, on_delete, on_mark_paid))

        if upcoming:
            controls.append(ft.Text("Предстоят", size=ts(18), weight=ft.FontWeight.BOLD, color=APP_COLORS["text"]))
            for o in _sort_by_deadline(upcoming):
                controls.append(_obligation_card(o, on_edit, on_delete, on_mark_paid))

        if paid:
            controls.append(ft.Text("Оплачено", size=ts(18), weight=ft.FontWeight.BOLD, color=APP_COLORS["success"]))
            for o in paid:
                controls.append(_obligation_card(o, on_edit, on_delete, on_mark_paid))

    if not is_desktop:
        controls.append(primary_button("Добавить обязательство", icon=ft.Icons.ADD, expand=True, on_click=on_add))

    return ft.Column(spacing=20, controls=controls)


def build_tax_tracker_page(
    is_desktop: bool = False,
    obligations: list[dict] | None = None,
    on_add=None,
    on_edit=None,
    on_delete=None,
    on_mark_paid=None,
    user: dict | None = None,
) -> ft.Control:
    content = _build_content(
        obligations or [],
        on_add,
        on_edit,
        on_delete,
        on_mark_paid,
        user,
        is_desktop,
    )
    return desktop_content(content, width=960, top=54) if is_desktop else content
