"""
Фоновый планировщик на asyncio (без внешних зависимостей).

Запускается через FastAPI lifespan. Каждые INTERVAL_SECONDS секунд:
  - отправляет pending email из очереди (email_service.send_pending_emails)
  - удаляет просроченные refresh-токены (cleanup_expired_tokens)
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

EMAIL_INTERVAL_SECONDS: int = 60
TOKEN_CLEANUP_INTERVAL_SECONDS: int = 3600
NOTIFICATION_RULES_INTERVAL_SECONDS: int = 6 * 3600


async def _email_sender_loop() -> None:
    from backend.database import SessionLocal
    from backend.email_service import send_pending_emails

    while True:
        try:
            await asyncio.sleep(EMAIL_INTERVAL_SECONDS)
            db = SessionLocal()
            try:
                result = send_pending_emails(db)
                if result["sent"] or result["failed"]:
                    logger.info("email scheduler: %s", result)
            finally:
                db.close()
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.error("email scheduler error: %s", exc)


async def _token_cleanup_loop() -> None:
    from sqlalchemy import delete
    from backend.database import SessionLocal
    from backend.models import RefreshToken

    while True:
        try:
            await asyncio.sleep(TOKEN_CLEANUP_INTERVAL_SECONDS)
            db = SessionLocal()
            try:
                now = datetime.now(timezone.utc)
                result = db.execute(
                    delete(RefreshToken).where(
                        (RefreshToken.expires_at < now) | (RefreshToken.revoked == True)  # noqa: E712
                    )
                )
                db.commit()
                if result.rowcount:
                    logger.info("token cleanup: removed %d tokens", result.rowcount)
            finally:
                db.close()
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.error("token cleanup error: %s", exc)


async def _notification_rules_loop() -> None:
    from backend.database import SessionLocal
    from backend.notifications.rules import generate_all_due_notifications

    while True:
        try:
            await asyncio.sleep(NOTIFICATION_RULES_INTERVAL_SECONDS)
            db = SessionLocal()
            try:
                result = generate_all_due_notifications(db)
                if any(result.values()):
                    logger.info("notification rules: %s", result)
            finally:
                db.close()
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.error("notification rules error: %s", exc)


_tasks: list[asyncio.Task] = []


def start_background_tasks() -> None:
    _tasks.append(asyncio.create_task(_email_sender_loop(), name="email_sender"))
    _tasks.append(asyncio.create_task(_token_cleanup_loop(), name="token_cleanup"))
    _tasks.append(asyncio.create_task(_notification_rules_loop(), name="notification_rules"))
    logger.info("background scheduler started (%d tasks)", len(_tasks))


def stop_background_tasks() -> None:
    for task in _tasks:
        task.cancel()
    _tasks.clear()
    logger.info("background scheduler stopped")
