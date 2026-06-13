"""Оркестрация внешней доставки после обязательной in-app записи."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models import User, UserNotification, UserPushToken
from backend.notifications.native_push import is_native_push_ready, send_native_push
from backend.notifications.preferences import get_notification_preferences, notification_type_enabled
from backend.notifications.service import safe_push_payload
from backend.security import DocumentCryptoError, decrypt_field


def deliver_notification(db: Session, notification: UserNotification) -> dict:
    user = db.get(User, notification.user_id)
    if user is None:
        return {"system_delivered": False, "reason": "user_not_found", "deliveries": []}

    preferences = get_notification_preferences(user)
    if not preferences.get("system_notifications_enabled", False):
        return {"system_delivered": False, "reason": "permission_not_granted", "deliveries": []}
    if not notification_type_enabled(preferences, notification.notification_type):
        return {"system_delivered": False, "reason": "notification_type_disabled", "deliveries": []}
    if not preferences.get("native_push_enabled", False):
        return {"system_delivered": False, "reason": "native_push_disabled", "deliveries": []}

    tokens = db.scalars(
        select(UserPushToken).where(
            UserPushToken.user_id == user.id,
            UserPushToken.is_active == True,  # noqa: E712
        )
    ).all()
    if not tokens:
        return {"system_delivered": False, "reason": "token_not_registered", "deliveries": []}
    if not is_native_push_ready():
        return {"system_delivered": False, "reason": "credentials_not_configured", "deliveries": []}

    payload = safe_push_payload(notification)
    deliveries: list[dict] = []
    for token in tokens:
        try:
            raw_token = decrypt_field(token.token_encrypted)
        except DocumentCryptoError:
            deliveries.append({"token_id": token.id, "status": "skipped", "reason": "encryption_not_configured"})
            continue
        result = send_native_push(
            token=raw_token,
            platform=token.platform,
            payload=payload,
        )
        deliveries.append({"token_id": token.id, **result})

    delivered = any(item.get("status") == "delivered" for item in deliveries)
    reason = "delivered" if delivered else (deliveries[0].get("reason", "delivery_skipped") if deliveries else "delivery_skipped")
    return {"system_delivered": delivered, "reason": reason, "deliveries": deliveries}
