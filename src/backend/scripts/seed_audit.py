"""scripts/seed_audit.py — наполняет таблицу audit_logs реалистичными записями.

Полезно для демо/диплома: audit-лог в админ-панели не пустой, видно «работу»
редакторов и админов (входы, создания/изменения/удаления, баны, верификации).

Идемпотентен: повторный запуск НЕ дублирует записи. Сравнение по
комбинации (actor, action, created_at-day). Если на этот день уже есть
запись с тем же actor + началом action — пропускаем.

Использование:
    PYTHONPATH=src .venv/bin/python -m backend.scripts.seed_audit
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.models import AuditLog
from backend.service import log_audit_event


# Реалистичные действия за последние 30 дней. Каждое = (actor, action, days_ago).
# Генерируют похожий на боевой audit-log (без реального изменения сущностей).
SEED_EVENTS: list[tuple[str, str, str, int]] = [
    # role_id, actor, action, days_ago
    ("platform_admin", "admin@test.local", "Вход администратора", 30),
    ("content_editor", "editor@test.local", "Вход редактора", 30),
    ("platform_admin", "admin@test.local", "Создана проблема: «Получение паспорта»", 28),
    ("content_editor", "editor@test.local", "Создан сценарий: «Рождение ребёнка»", 27),
    ("content_editor", "editor@test.local", "Создан сценарий: «Восстановление паспорта»", 26),
    ("content_editor", "editor@test.local", "Создан сценарий: «Открытие ИП»", 25),
    ("platform_admin", "admin@test.local", "Создана запись экстремистского реестра: «Канал N в реестре»", 24),
    ("content_editor", "editor@test.local", "Опубликована новость: «Изменения в НК РБ с 2026 года»", 22),
    ("content_editor", "editor@test.local", "Изменён сценарий: «Рождение ребёнка»", 21),
    ("content_editor", "editor@test.local", "Создано учреждение: «Одно окно г. Минск»", 20),
    ("content_editor", "editor@test.local", "Создано учреждение: «МФЦ Центрального района»", 20),
    ("platform_admin", "admin@test.local", "Создан закон-апдейт: «Обновление закона о ЖКХ»", 19),
    ("content_editor", "editor@test.local", "Верифицирован сценарий: «Рождение ребёнка»", 18),
    ("content_editor", "editor@test.local", "Верифицирован сценарий: «Восстановление паспорта»", 17),
    ("content_editor", "editor@test.local", "Опубликована новость: «Новый МФЦ открылся в Бресте»", 15),
    ("platform_admin", "admin@test.local", "Заблокирован пользователь: spam_user@bel.by", 14),
    ("content_editor", "editor@test.local", "Изменён сценарий: «Открытие ИП»", 12),
    ("platform_admin", "admin@test.local", "Изменена роль пользователя: test_citizen@bel.by → content_editor", 10),
    ("content_editor", "editor@test.local", "Создана проблема: «Оформление субсидии ЖКХ»", 8),
    ("content_editor", "editor@test.local", "Опубликована новость: «Электронные рецепты с 1 июля»", 7),
    ("platform_admin", "admin@test.local", "Вход администратора", 5),
    ("content_editor", "editor@test.local", "Изменено учреждение: «МФЦ Центрального района»", 4),
    ("platform_admin", "admin@test.local", "Создана запись экстремистского реестра: «Издание М в реестре»", 3),
    ("content_editor", "editor@test.local", "Вход редактора", 2),
    ("content_editor", "editor@test.local", "Опубликована новость: «Льготы для семей с детьми расширены»", 1),
    ("platform_admin", "admin@test.local", "Вход администратора", 0),
    ("content_editor", "editor@test.local", "Вход редактора", 0),
]


def _has_event(db: Session, actor: str, action: str, day: datetime) -> bool:
    """Проверка идемпотентности: на этот день уже есть запись с тем же actor + начало action совпадает."""
    start = day.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    stmt = select(AuditLog.id).where(
        AuditLog.actor == actor,
        AuditLog.action == action,
        AuditLog.created_at >= start,
        AuditLog.created_at < end,
    )
    return db.scalar(stmt) is not None


def _backdate(audit: AuditLog, days_ago: int) -> None:
    """Сдвинуть created_at/updated_at на N дней назад (для реалистичной ленты)."""
    target = datetime.now(timezone.utc) - timedelta(days=days_ago)
    audit.created_at = target
    audit.updated_at = target


def main() -> int:
    db = SessionLocal()
    try:
        added = 0
        for role_id, actor, action, days_ago in SEED_EVENTS:
            day = datetime.now(timezone.utc) - timedelta(days=days_ago)
            if _has_event(db, actor, action, day):
                continue
            entry = log_audit_event(
                db, actor=actor, action=action, role_id=role_id, event_type="other"
            )
            _backdate(entry, days_ago)
            db.commit()
            added += 1
        total = db.scalar(select(AuditLog.id).order_by(AuditLog.id.desc()).limit(1))
        print(f"[seed_audit] новых записей: {added}; всего в audit_logs: {total}")
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
