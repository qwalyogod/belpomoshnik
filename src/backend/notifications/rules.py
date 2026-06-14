"""Генерация уведомлений по срокам документов, задач, ЖКХ и налогов."""
from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models import TaxObligation, UserDocument, UserSituation, UserSituationTask, UtilityAccount, UtilityPayment
from backend.notifications.delivery import deliver_notification
from backend.notifications.preferences import get_notification_preferences, notification_type_enabled
from backend.notifications.service import create_in_app_notification


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value[:10]).date()
    except (TypeError, ValueError):
        return None


def _within_window(value: str | None, *, days_before: int) -> bool:
    target = _parse_date(value)
    if target is None:
        return False
    delta = (target - date.today()).days
    return -7 <= delta <= days_before


def _create_and_deliver(db: Session, *, user_id: int, notification_type: str, **kwargs) -> bool:
    notification, created = create_in_app_notification(
        db,
        user_id=user_id,
        notification_type=notification_type,
        **kwargs,
    )
    if created:
        deliver_notification(db, notification)
    return created


def generate_document_expiry_notifications(db: Session) -> int:
    created = 0
    documents = db.scalars(select(UserDocument).where(UserDocument.expiry_date != "")).all()
    for document in documents:
        preferences = get_notification_preferences(document.user)
        if not notification_type_enabled(preferences, "doc_expiry") or not _within_window(document.expiry_date, days_before=90):
            continue
        created += int(_create_and_deliver(
            db,
            user_id=document.user_id,
            notification_type="doc_expiry",
            title=f"Срок документа: {document.title}",
            description="Проверьте срок действия документа в разделе «Мои документы».",
            source="documents",
            route="/documents",
            due_date=document.expiry_date,
            dedupe_key=f"doc-expiry:{document.id}:{document.expiry_date}",
        ))
    db.commit()
    return created


def generate_task_due_notifications(db: Session) -> int:
    created = 0
    rows = db.execute(
        select(UserSituationTask, UserSituation).join(UserSituation, UserSituation.id == UserSituationTask.situation_id)
        .where(UserSituationTask.completed == False, UserSituationTask.due_date != "")  # noqa: E712
    ).all()
    for task, situation in rows:
        if not _within_window(task.due_date, days_before=30):
            continue
        created += int(_create_and_deliver(
            db,
            user_id=situation.user_id,
            notification_type="task_due",
            title=f"Срок задачи: {task.title}",
            description=f"Откройте ситуацию «{situation.title}» и проверьте следующий шаг.",
            source="situations",
            route=f"/situations/{situation.id}",
            due_date=task.due_date,
            dedupe_key=f"task-due:{task.id}:{task.due_date}",
        ))
    db.commit()
    return created


def generate_utility_due_notifications(db: Session) -> int:
    created = 0
    rows = db.execute(
        select(UtilityPayment, UtilityAccount).join(UtilityAccount, UtilityAccount.id == UtilityPayment.account_id)
        .where(UtilityPayment.status != "Оплачено")
    ).all()
    for payment, account in rows:
        for kind, due, title in (
            ("utility_due", payment.payment_deadline, "Срок оплаты ЖКХ"),
            ("utility_readings", payment.readings_deadline, "Срок передачи показаний"),
        ):
            if not _within_window(due, days_before=30):
                continue
            created += int(_create_and_deliver(
                db,
                user_id=account.user_id,
                notification_type=kind,
                title=title,
                description="Проверьте обязательство в разделе «ЖКХ и налоги».",
                source="finance",
                route="/finance",
                due_date=due,
                dedupe_key=f"{kind}:{payment.id}:{due}",
            ))
    db.commit()
    return created


def generate_tax_due_notifications(db: Session) -> int:
    created = 0
    taxes = db.scalars(select(TaxObligation).where(TaxObligation.status != "Оплачено")).all()
    for tax in taxes:
        if not _within_window(tax.deadline, days_before=60):
            continue
        created += int(_create_and_deliver(
            db,
            user_id=tax.user_id,
            notification_type="tax_due",
            title=f"Срок налога: {tax.title}",
            description="Проверьте обязательство и официальный источник в разделе «ЖКХ и налоги».",
            source="finance",
            route="/finance",
            due_date=tax.deadline,
            dedupe_key=f"tax-due:{tax.id}:{tax.deadline}",
        ))
    db.commit()
    return created


def generate_all_due_notifications(db: Session) -> dict[str, int]:
    return {
        "documents": generate_document_expiry_notifications(db),
        "tasks": generate_task_due_notifications(db),
        "utility": generate_utility_due_notifications(db),
        "taxes": generate_tax_due_notifications(db),
    }
