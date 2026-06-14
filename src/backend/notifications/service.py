"""Создание надёжных in-app уведомлений с дедупликацией."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models import UserNotification


def create_in_app_notification(
    db: Session,
    *,
    user_id: int,
    title: str,
    description: str = "",
    notification_type: str = "task",
    source: str = "",
    route: str = "/notifications",
    due_date: str | None = None,
    dedupe_key: str = "",
) -> tuple[UserNotification, bool]:
    """Создать уведомление или вернуть существующее по ``dedupe_key``.

    Транзакцией управляет вызывающий код. ``created`` позволяет правилам и
    endpoint'ам не запускать внешнюю доставку повторно.
    """
    if dedupe_key:
        existing = db.scalars(
            select(UserNotification).where(
                UserNotification.user_id == user_id,
                UserNotification.dedupe_key == dedupe_key,
            ).limit(1)
        ).first()
        if existing is not None:
            return existing, False

    notification = UserNotification(
        id=uuid.uuid4().hex,
        user_id=user_id,
        title=title[:255],
        description=description,
        notification_type=notification_type[:64],
        source=source[:255],
        route=(route or "/notifications")[:255],
        due_date=due_date,
        dedupe_key=dedupe_key[:255],
    )
    db.add(notification)
    db.flush()
    return notification, True


def safe_push_payload(notification: UserNotification) -> dict[str, str]:
    """Payload без персональных данных и содержимого документов."""
    return {
        "title": "Белпомощник",
        "body": "У вас есть новое уведомление",
        "notificationId": notification.id,
        "type": notification.notification_type,
        "route": notification.route or "/notifications",
    }
