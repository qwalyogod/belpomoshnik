from __future__ import annotations

from datetime import date, datetime
from typing import Any


COMPLETED_STATUSES = {"Завершено", "Завершена"}


def parse_due_date(value: str | None) -> date | None:
    if not value:
        return None
    raw_value = value.strip()
    for date_format in ("%Y-%m-%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(raw_value, date_format).date()
        except ValueError:
            continue
    return None


def format_due_date(value: date | None, fallback: str = "Без срока") -> str:
    return value.strftime("%d.%m.%Y") if value else fallback


def _tasks_for_situation(tasks: list[dict[str, Any]], situation_id: str) -> list[dict[str, Any]]:
    return [task for task in tasks if task.get("situation_id") == situation_id]


def calculate_progress(tasks: list[dict[str, Any]]) -> int:
    if not tasks:
        return 0
    completed = len([task for task in tasks if task.get("completed")])
    return round(completed / len(tasks) * 100)


def status_from_progress(progress: int) -> str:
    if progress <= 0:
        return "Не начата"
    if progress >= 100:
        return "Завершена"
    return "В процессе"


def sync_situation_progress(situations: list[dict[str, Any]], tasks: list[dict[str, Any]]) -> None:
    for situation in situations:
        situation_tasks = _tasks_for_situation(tasks, situation.get("id", ""))
        progress = calculate_progress(situation_tasks)
        situation["progress"] = progress
        situation["status"] = status_from_progress(progress)


def build_dashboard_data(
    situations: list[dict[str, Any]],
    tasks: list[dict[str, Any]],
    today: date | None = None,
    documents: list[dict[str, Any]] | None = None,
    reminder_days: int = 30,
    utility_payments: list[dict[str, Any]] | None = None,
    tax_obligations: list[dict[str, Any]] | None = None,
    utility_reminder_days: int = 7,
    tax_reminder_days: int = 14,
) -> dict[str, Any]:
    current_date = today or date.today()
    sync_situation_progress(situations, tasks)

    active_situations = [
        situation
        for situation in situations
        if situation.get("progress", 0) < 100 and situation.get("status") not in COMPLETED_STATUSES
    ]
    completed_situations = [
        situation
        for situation in situations
        if situation.get("progress", 0) >= 100 or situation.get("status") in COMPLETED_STATUSES
    ]
    active_progress = (
        round(sum(int(situation.get("progress", 0)) for situation in active_situations) / len(active_situations))
        if active_situations
        else 0
    )

    situation_titles = {situation.get("id"): situation.get("title", "Ситуация") for situation in situations}
    task_rows: list[dict[str, Any]] = []
    for task in tasks:
        if task.get("completed"):
            continue
        situation_id = task.get("situation_id")
        if situation_id not in situation_titles:
            continue
        due_date = parse_due_date(task.get("due_date")) or parse_due_date(task.get("deadline"))
        if due_date is None:
            continue
        row = {
            "id": task.get("id"),
            "title": task.get("title", "Задача"),
            "situation_id": situation_id,
            "situation_title": situation_titles[situation_id],
            "due_date": due_date,
            "due_date_display": format_due_date(due_date),
        }
        task_rows.append(row)

    upcoming_tasks = sorted(
        [task for task in task_rows if task["due_date"] >= current_date],
        key=lambda task: task["due_date"],
    )[:5]
    overdue_tasks = sorted(
        [task for task in task_rows if task["due_date"] < current_date],
        key=lambda task: task["due_date"],
    )[:5]

    situation_summaries: list[dict[str, Any]] = []
    for situation in active_situations[:3]:
        situation_tasks = _tasks_for_situation(tasks, situation.get("id", ""))
        completed = len([task for task in situation_tasks if task.get("completed")])
        total = len(situation_tasks)
        situation_summaries.append(
            {
                "id": situation.get("id"),
                "title": situation.get("title", "Ситуация"),
                "status": situation.get("status", status_from_progress(int(situation.get("progress", 0)))),
                "progress": int(situation.get("progress", 0)),
                "completed_tasks": completed,
                "total_tasks": total,
            }
        )

    documents_map: dict[tuple[str, bool], dict[str, Any]] = {}
    active_ids = {situation.get("id") for situation in active_situations}
    for task in tasks:
        if task.get("completed") or task.get("situation_id") not in active_ids:
            continue
        for document in task.get("documents", []) or []:
            title = document.get("title")
            if not title:
                continue
            required = bool(document.get("required"))
            key = (title, required)
            item = documents_map.setdefault(
                key,
                {
                    "title": title,
                    "required": required,
                    "situations": set(),
                },
            )
            item["situations"].add(situation_titles.get(task.get("situation_id"), "Ситуация"))

    documents_to_prepare = [
        {
            "title": item["title"],
            "required": item["required"],
            "situation_title": ", ".join(sorted(item["situations"])),
        }
        for item in documents_map.values()
    ][:8]

    expiring_documents: list[dict[str, Any]] = []
    overdue_documents: list[dict[str, Any]] = []
    for doc in (documents or []):
        expiry = parse_due_date(doc.get("expiry_date"))
        if not expiry:
            continue
        days_left = (expiry - current_date).days
        entry = {
            "id": doc.get("id", ""),
            "title": doc.get("title", "Документ"),
            "expiry_date": expiry.strftime("%d.%m.%Y"),
            "days_left": days_left,
        }
        if days_left < 0:
            overdue_documents.append(entry)
        elif days_left <= reminder_days:
            expiring_documents.append(entry)
    expiring_documents.sort(key=lambda d: d["days_left"])
    overdue_documents.sort(key=lambda d: d["days_left"])

    utility_events: list[dict[str, Any]] = []
    for payment in utility_payments or []:
        if payment.get("status") == "Оплачено":
            continue
        for field, event_title in [
            ("readings_deadline", "Передать показания ЖКХ"),
            ("payment_deadline", "Оплатить ЖКХ"),
        ]:
            due = parse_due_date(payment.get(field))
            if not due:
                continue
            days_left = (due - current_date).days
            if days_left > utility_reminder_days:
                continue
            utility_events.append(
                {
                    "id": f"{payment.get('id', '')}-{field}",
                    "title": event_title,
                    "subtitle": payment.get("period", "Период ЖКХ"),
                    "due_date": due,
                    "due_date_display": format_due_date(due),
                    "days_left": days_left,
                    "amount": payment.get("amount", 0),
                    "status": "Просрочено" if days_left < 0 else "Предстоит",
                    "route": "/utility",
                    "kind": "utility",
                }
            )

    tax_events: list[dict[str, Any]] = []
    for obligation in tax_obligations or []:
        if obligation.get("status") == "Оплачено":
            continue
        due = parse_due_date(obligation.get("deadline"))
        if not due:
            continue
        days_left = (due - current_date).days
        if days_left > tax_reminder_days:
            continue
        tax_events.append(
            {
                "id": obligation.get("id", ""),
                "title": obligation.get("title", "Налоговое обязательство"),
                "subtitle": obligation.get("period", "Налоги"),
                "due_date": due,
                "due_date_display": format_due_date(due),
                "days_left": days_left,
                "amount": obligation.get("amount", 0),
                "status": "Просрочено" if days_left < 0 or obligation.get("status") == "Просрочено" else "Предстоит",
                "route": "/taxes",
                "kind": "tax",
            }
        )

    obligation_events = sorted(
        utility_events + tax_events,
        key=lambda item: (item["due_date"], 0 if item["status"] == "Просрочено" else 1, item["title"]),
    )
    overdue_obligations = [item for item in obligation_events if item["status"] == "Просрочено"][:5]
    upcoming_obligations = [item for item in obligation_events if item["status"] != "Просрочено"][:5]

    return {
        "active_count": len(active_situations),
        "completed_count": len(completed_situations),
        "active_progress": active_progress,
        "situations": situation_summaries,
        "upcoming_tasks": upcoming_tasks,
        "overdue_tasks": overdue_tasks,
        "documents_to_prepare": documents_to_prepare,
        "expiring_documents": expiring_documents,
        "overdue_documents": overdue_documents,
        "utility_events": utility_events,
        "tax_events": tax_events,
        "overdue_obligations": overdue_obligations,
        "upcoming_obligations": upcoming_obligations,
        "obligations_count": len(obligation_events),
    }
