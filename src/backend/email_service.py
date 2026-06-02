"""
I3, I4, I5 — Email-сервис «Белпомощник».

I3: SMTP-настройки через переменные окружения.
I4: Очередь отправки — pending-записи в EmailNotification, фоновая задача рассылает.
I5: Журнал доставки + лимиты (MAX_PER_USER_PER_DAY).

Зависимости (уже в stdlib): smtplib, email.mime.
Опционально для production: pip install aiosmtplib jinja2

Использование:
    from backend.email_service import enqueue_email, send_pending_emails, build_doc_expiry_body

    # 1. Поставить в очередь
    enqueue_email(db, user_id=1, recipient="u@example.com", subject="...", body="...", notification_type="doc_expiry")

    # 2. Отправить все pending (вызывать из APScheduler / cron / background task)
    send_pending_emails(db)
"""
from __future__ import annotations

import logging
import os
import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from sqlalchemy import func, select
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# I3 — SMTP-настройки (все через env, дефолты для dev)
# ---------------------------------------------------------------------------

SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER: str = os.getenv("SMTP_USER", "")
SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM: str = os.getenv("SMTP_FROM", "noreply@belpomoshnik.by")
SMTP_TLS: bool = os.getenv("SMTP_TLS", "true").lower() == "true"

APP_NAME: str = os.getenv("APP_NAME", "Белпомощник")

# I5 — лимит: не более N писем на пользователя в сутки
MAX_EMAILS_PER_USER_PER_DAY: int = int(os.getenv("MAX_EMAILS_PER_USER_PER_DAY", "5"))


# ---------------------------------------------------------------------------
# I3 — Отправка одного письма через SMTP
# ---------------------------------------------------------------------------

def _send_smtp(recipient: str, subject: str, body_text: str, body_html: str | None = None) -> None:
    """Отправить email через SMTP. Raises SMTPException при ошибке.

    Аутентификация опциональна: если SMTP_USER/SMTP_PASSWORD не заданы,
    письмо отправляется без login (dev-релеи без auth, напр. MailHog).
    Для production задайте креды в env.
    """
    if not SMTP_HOST:
        raise RuntimeError("SMTP_HOST не задан в переменных окружения.")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{APP_NAME} <{SMTP_FROM}>"
    msg["To"] = recipient

    msg.attach(MIMEText(body_text, "plain", "utf-8"))
    if body_html:
        msg.attach(MIMEText(body_html, "html", "utf-8"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        if SMTP_TLS:
            server.starttls()
        if SMTP_USER and SMTP_PASSWORD:
            server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_FROM, recipient, msg.as_string())


# ---------------------------------------------------------------------------
# I3 — HTML-шаблон письма (inline, без Jinja2)
# ---------------------------------------------------------------------------

def _html_template(subject: str, body_text: str) -> str:
    lines = body_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    items_html = "".join(
        f"<h3 style='margin:16px 0 4px;color:#1E293B'>{l[2:].strip()}</h3>" if l.startswith("##")
        else "<hr style='border:none;border-top:1px solid #E2E8F0;margin:12px 0'>" if l.startswith("---")
        else f"<p style='margin:4px 0;color:#334155'>{l}</p>"
        for l in body_text.splitlines()
    )
    return f"""<!DOCTYPE html>
<html lang='ru'>
<head><meta charset='utf-8'><title>{subject}</title></head>
<body style='margin:0;padding:0;background:#F1F5F9;font-family:system-ui,sans-serif'>
  <table width='100%' cellpadding='0' cellspacing='0'>
    <tr><td align='center' style='padding:32px 16px'>
      <table width='600' cellpadding='0' cellspacing='0'
             style='background:#FFFFFF;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,.08)'>
        <tr><td style='background:#2563EB;padding:24px 32px'>
          <span style='color:#fff;font-size:22px;font-weight:700'>{APP_NAME}</span>
        </td></tr>
        <tr><td style='padding:28px 32px'>{items_html}</td></tr>
        <tr><td style='background:#F8FAFC;padding:16px 32px;font-size:12px;color:#94A3B8'>
          Вы получаете это письмо, так как включены email-уведомления в профиле.
          Для отписки откройте Профиль → Настройки.
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


# ---------------------------------------------------------------------------
# I3 — Шаблон текста для истекающих документов
# ---------------------------------------------------------------------------

def build_doc_expiry_body(doc_titles: list[str]) -> tuple[str, str]:
    """Возвращает (plain_text, html) для письма об истекающих документах."""
    plain_lines = [
        "Здравствуйте!",
        "",
        "## Напоминание о документах",
        "---",
        "Следующие ваши документы истекают в ближайшее время:",
        "",
        *[f"  • {t}" for t in doc_titles],
        "",
        "Рекомендуем заранее подготовить необходимые материалы для продления.",
        "",
        "С уважением,",
        f"Команда {APP_NAME}",
    ]
    plain = "\n".join(plain_lines)
    html = _html_template(f"Напоминание о документах — {APP_NAME}", plain)
    return plain, html


# ---------------------------------------------------------------------------
# I4 — Постановка письма в очередь
# ---------------------------------------------------------------------------

def enqueue_email(
    db: Session,
    recipient: str,
    subject: str,
    body: str,
    notification_type: str = "doc_expiry",
    user_id: int | None = None,
    scheduled_at: datetime | None = None,
) -> "EmailNotification":
    """
    I4 — Поставить email в очередь (status='pending').
    I5 — Проверяет лимит MAX_EMAILS_PER_USER_PER_DAY перед постановкой.
    """
    from backend.models import EmailNotification

    if user_id is not None and _daily_limit_exceeded(db, user_id):
        logger.warning("email limit exceeded for user_id=%s", user_id)
        dummy = EmailNotification(
            user_id=user_id,
            recipient_email=recipient,
            subject=subject,
            body=body,
            notification_type=notification_type,
            status="skipped_limit",
            error_message=f"Превышен дневной лимит {MAX_EMAILS_PER_USER_PER_DAY} писем.",
            scheduled_at=scheduled_at,
        )
        db.add(dummy)
        db.commit()
        db.refresh(dummy)
        return dummy

    entry = EmailNotification(
        user_id=user_id,
        recipient_email=recipient,
        subject=subject,
        body=body,
        notification_type=notification_type,
        status="pending",
        scheduled_at=scheduled_at or datetime.now(timezone.utc),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


# ---------------------------------------------------------------------------
# I5 — Лимит отправки
# ---------------------------------------------------------------------------

def _daily_limit_exceeded(db: Session, user_id: int) -> bool:
    from backend.models import EmailNotification
    from datetime import date, timedelta

    today_start = datetime.combine(date.today(), datetime.min.time()).replace(tzinfo=timezone.utc)
    count = db.scalar(
        select(func.count(EmailNotification.id)).where(
            EmailNotification.user_id == user_id,
            EmailNotification.status.in_(["sent", "pending"]),
            EmailNotification.created_at >= today_start,
        )
    ) or 0
    return count >= MAX_EMAILS_PER_USER_PER_DAY


# ---------------------------------------------------------------------------
# I4 — Обработка очереди (вызывать из планировщика)
# ---------------------------------------------------------------------------

def send_pending_emails(db: Session, batch_size: int = 50) -> dict[str, int]:
    """
    I4 — Отправить все pending-письма из очереди.

    Вызывать из APScheduler / Celery / cron / startup-события FastAPI.
    Возвращает {"sent": N, "failed": N, "skipped": N}.
    """
    from backend.models import EmailNotification

    now = datetime.now(timezone.utc)
    pending = db.scalars(
        select(EmailNotification)
        .where(
            EmailNotification.status == "pending",
            EmailNotification.scheduled_at <= now,
        )
        .limit(batch_size)
    ).all()

    stats = {"sent": 0, "failed": 0, "skipped": 0}

    for entry in pending:
        try:
            _send_smtp(entry.recipient_email, entry.subject, entry.body)
            entry.status = "sent"
            entry.sent_at = datetime.now(timezone.utc)
            entry.error_message = ""
            stats["sent"] += 1
            logger.info("email sent id=%s to=%s", entry.id, entry.recipient_email)
        except Exception as exc:
            entry.status = "failed"
            entry.error_message = str(exc)[:500]
            stats["failed"] += 1
            logger.error("email failed id=%s: %s", entry.id, exc)

    db.commit()
    return stats


# ---------------------------------------------------------------------------
# I5 — Список журнала доставки
# ---------------------------------------------------------------------------

def list_email_log(db: Session, user_id: int | None = None, limit: int = 100) -> list:
    """I5 — Последние записи журнала отправки email."""
    from backend.models import EmailNotification

    stmt = select(EmailNotification).order_by(EmailNotification.created_at.desc()).limit(limit)
    if user_id is not None:
        stmt = stmt.where(EmailNotification.user_id == user_id)
    return list(db.scalars(stmt).all())
