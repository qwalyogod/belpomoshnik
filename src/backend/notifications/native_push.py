"""
Промпт 6: native push delivery (FCM/APNs).

В текущей сборке credentials FCM/APNs не настроены, поэтому функция
`send_native_push` возвращает статус `skipped` с причиной
`credentials_not_configured`. Production-доставка требует:
- Android: Firebase Cloud Messaging + google-services.json
- iOS: Apple Developer Account, APNs key/certificate
"""
from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


def is_native_push_ready() -> bool:
    """True если хоть какой-то провайдер FCM/APNs настроен."""
    return bool(os.getenv("FCM_SERVER_KEY") or os.getenv("FCM_CREDENTIALS_JSON") or os.getenv("APNS_KEY_PATH"))


def send_native_push(
    *,
    user_id: int,
    platform: str,
    title: str,
    body: str,
    route: str = "",
    notification_id: str = "",
    notification_type: str = "",
) -> dict:
    """Отправить native push. В заглушечном режиме возвращает skipped."""
    if not is_native_push_ready():
        return {"status": "skipped", "reason": "credentials_not_configured"}

    # В реальной production-сборке здесь httpx-запросы к FCM/APNs.
    # Не пишем имитацию — это вводит в заблуждение на демо.
    logger.info("send_native_push (stub): user=%s platform=%s type=%s", user_id, platform, notification_type)
    return {"status": "skipped", "reason": "implementation_pending"}
