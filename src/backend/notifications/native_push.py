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
    token: str,
    platform: str,
    payload: dict[str, str],
) -> dict:
    """Отправить native push. В заглушечном режиме возвращает skipped."""
    if not is_native_push_ready():
        return {"status": "skipped", "reason": "credentials_not_configured"}

    # В реальной production-сборке здесь httpx-запросы к FCM/APNs.
    # Не пишем имитацию — это вводит в заблуждение на демо.
    # Не логируем device token и персональные поля. Payload уже очищен сервисом.
    logger.info("send_native_push (stub): platform=%s type=%s", platform, payload.get("type", ""))
    return {"status": "skipped", "reason": "implementation_pending"}
