import flet as ft

from components.buttons import primary_button, secondary_button
from components.cards import app_card, badge, empty_state_card, hint_card, page_heading, section_title
from components.layout import desktop_content
from services.dashboard import parse_due_date
from theme.app_theme import APP_COLORS, border_all, padding_symmetric, ts


def _payment_status_variant(status: str) -> str:
    return {"Оплачено": "success", "Просрочено": "error", "Ожидает": "warning"}.get(status, "default")


def _days_label(deadline_raw: str) -> str:
    from datetime import date
    d = parse_due_date(deadline_raw)
    if not d:
        return ""
    days = (d - date.today()).days
    if days < 0:
        return "Просрочено на " + str(-days) + " дн."
    if days == 0:
        return "Сегодня"
    return "Через " + str(days) + " дн."


def _payment_row(payment: dict, on_edit=None, on_delete=None) -> ft.Container:
    status = payment.get("status", "Ожидает")
    amount = payment.get("amount", 0)
    amount_text = (str(amount) + " руб.") if amount else "не указана"
    readings_deadline = payment.get("readings_deadline", "")
    payment_deadline = payment.get("payment_deadline", "")
    days_hint = _days_label(payment_deadline) if status != "Оплачено" else ""

    return ft.Container(
        border_radius=12,
        bgcolor=APP_COLORS["surface"],
        border=border_all(APP_COLORS["border_soft"]),
        padding=padding_symmetric(horizontal=16, vertical=12),
        content=ft.Column(
            spacing=8,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Row(
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Text(payment.get("period", "Период"), size=ts(15), weight=ft.FontWeight.W_600, color=APP_COLORS["text"]),
                                badge(status, _payment_status_variant(status)),
                            ],
                        ),
                        ft.Row(
                            spacing=4,
                            controls=[
                                ft.IconButton(ft.Icons.EDIT_OUTLINED, icon_size=18, icon_color=APP_COLORS["muted"], tooltip="Редактировать", on_click=lambda _, pid=payment["id"]: on_edit(pid) if on_edit else None),
                                ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_size=18, icon_color=APP_COLORS["danger"], tooltip="Удалить", on_click=lambda _, pid=payment["id"]: on_delete(pid) if on_delete else None),
                            ],
                        ),
                    ],
                ),
                ft.Row(
                    wrap=True,
                    spacing=16,
                    run_spacing=4,
                    controls=[
                        ft.Row(spacing=4, controls=[ft.Icon(ft.Icons.SPEED_OUTLINED, size=ts(14), color=APP_COLORS["muted"]), ft.Text("Показания: " + (payment.get("readings_date") or "не переданы"), size=ts(12), color=APP_COLORS["muted"])]),
                        ft.Row(spacing=4, controls=[ft.Icon(ft.Icons.PAYMENT_OUTLINED, size=ts(14), color=APP_COLORS["muted"]), ft.Text("Оплата: " + (payment.get("payment_date") or "не выполнена"), size=ts(12), color=APP_COLORS["muted"])]),
                        ft.Row(spacing=4, controls=[ft.Icon(ft.Icons.MONETIZATION_ON_OUTLINED, size=ts(14), color=APP_COLORS["muted"]), ft.Text("Сумма: " + amount_text, size=ts(12), color=APP_COLORS["muted"])]),
                    ],
                ),
                *([ft.Text(days_hint, size=ts(12), color=APP_COLORS["warning"], weight=ft.FontWeight.W_600)] if days_hint else []),
                *([ft.Text(payment.get("comment", ""), size=ts(12), color=APP_COLORS["muted"])] if payment.get("comment") else []),
            ],
        ),
    )


def _account_card(
    account: dict,
    payments: list[dict],
    on_add_payment=None,
    on_edit_payment=None,
    on_delete_payment=None,
    on_edit_account=None,
    on_delete_account=None,
) -> ft.Container:
    account_payments = [p for p in payments if p.get("account_id") == account["id"]]
    account_payments_sorted = sorted(account_payments, key=lambda p: p.get("period", ""), reverse=True)

    overdue_count = sum(1 for p in account_payments if p.get("status") == "Просрочено")
    waiting_count = sum(1 for p in account_payments if p.get("status") == "Ожидает")

    return app_card(
        ft.Column(
            spacing=14,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Row(
                            spacing=10,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Container(
                                    width=40,
                                    height=40,
                                    border_radius=12,
                                    bgcolor=APP_COLORS["primary"] + "22",
                                    alignment=ft.Alignment(0, 0),
                                    content=ft.Icon(ft.Icons.HOME_WORK_OUTLINED, size=ts(20), color=APP_COLORS["primary"]),
                                ),
                                ft.Column(
                                    spacing=2,
                                    controls=[
                                        ft.Text(account.get("address", "Адрес не указан"), size=ts(16), weight=ft.FontWeight.BOLD, color=APP_COLORS["text"]),
                                        ft.Text("Лицевой счёт: " + (account.get("account_number") or "—") + "  ·  " + (account.get("provider") or ""), size=ts(12), color=APP_COLORS["muted"]),
                                    ],
                                ),
                            ],
                        ),
                        ft.Row(
                            spacing=4,
                            controls=[
                                *([badge(str(overdue_count) + " просроч.", "error")] if overdue_count else []),
                                *([badge(str(waiting_count) + " ожидает", "warning")] if waiting_count else []),
                                ft.IconButton(ft.Icons.EDIT_OUTLINED, icon_size=18, icon_color=APP_COLORS["muted"], tooltip="Изменить счёт", on_click=lambda _, aid=account["id"]: on_edit_account(aid) if on_edit_account else None),
                                ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_size=18, icon_color=APP_COLORS["danger"], tooltip="Удалить счёт", on_click=lambda _, aid=account["id"]: on_delete_account(aid) if on_delete_account else None),
                            ],
                        ),
                    ],
                ),
                ft.Divider(height=1, color=APP_COLORS["border_soft"]),
                section_title("Журнал платежей"),
                ft.Column(
                    spacing=8,
                    controls=[_payment_row(p, on_edit_payment, on_delete_payment) for p in account_payments_sorted]
                    if account_payments_sorted
                    else [ft.Text("Записей пока нет.", size=ts(14), color=APP_COLORS["muted"])],
                ),
                secondary_button(
                    "Добавить запись",
                    icon=ft.Icons.ADD,
                    on_click=lambda _, aid=account["id"]: on_add_payment(aid) if on_add_payment else None,
                    expand=True,
                ),
            ],
        ),
        padding=20,
    )


def _build_content(
    accounts: list[dict],
    payments: list[dict],
    on_add_account=None,
    on_edit_account=None,
    on_delete_account=None,
    on_add_payment=None,
    on_edit_payment=None,
    on_delete_payment=None,
    is_desktop: bool = False,
) -> ft.Column:
    controls: list[ft.Control] = [
        ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                page_heading("ЖКХ-трекер", "Локальный учёт показаний и оплаты без подключения к госреестрам."),
                primary_button("Добавить счёт", icon=ft.Icons.ADD, width=200, height=48, on_click=on_add_account) if is_desktop else ft.Container(),
            ],
        ) if is_desktop else page_heading("ЖКХ-трекер", "Локальный учёт показаний и оплаты."),
        hint_card("Данные хранятся локально. Реальная синхронизация с РСЦ не производится."),
    ]

    if not accounts:
        controls.append(
            empty_state_card(
                "Лицевых счётов нет",
                "Добавьте лицевой счёт, чтобы отслеживать показания и платежи.",
                "Добавить счёт",
                on_add_account,
                ft.Icons.HOME_WORK_OUTLINED,
            )
        )
    else:
        for account in accounts:
            controls.append(_account_card(account, payments, on_add_payment, on_edit_payment, on_delete_payment, on_edit_account, on_delete_account))

    if not is_desktop:
        controls.append(primary_button("Добавить счёт", icon=ft.Icons.ADD, expand=True, on_click=on_add_account))

    return ft.Column(spacing=24, controls=controls)


def build_utility_tracker_page(
    is_desktop: bool = False,
    accounts: list[dict] | None = None,
    payments: list[dict] | None = None,
    on_add_account=None,
    on_edit_account=None,
    on_delete_account=None,
    on_add_payment=None,
    on_edit_payment=None,
    on_delete_payment=None,
) -> ft.Control:
    content = _build_content(
        accounts or [],
        payments or [],
        on_add_account,
        on_edit_account,
        on_delete_account,
        on_add_payment,
        on_edit_payment,
        on_delete_payment,
        is_desktop,
    )
    return desktop_content(content, width=960, top=54) if is_desktop else content
