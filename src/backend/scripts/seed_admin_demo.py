"""scripts/seed_admin_demo.py — компактный сид для admin-демо.

Наполняет:
  • authorities — 5-7 реальных белорусских учреждений (МФЦ, налоговая, МВД и т.д.).
  • extremist_entries — 3-4 записи в разных статусах (draft/published).
  • scenarios / problems / scenario_stages / scenario_steps — минимальный
    «Каталог помощи», чтобы в табах админки было что показать.

Идемпотентен: повторный запуск не дублирует записи (проверка по title/url).

Использование:
    PYTHONPATH=src .venv/bin/python -m backend.scripts.seed_admin_demo
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.enums import ActionType, ContentStatus, DifficultyLevel, DurationUnit
from backend.models import (
    Authority,
    ExtremistEntry,
    Problem,
    Scenario,
    ScenarioStage,
    ScenarioStep,
)


AUTHORITIES: list[dict] = [
    {
        "title": "Единый портал электронных услуг (portal.gov.by)",
        "type": "Госпортал",
        "phone": "141",
        "website_url": "https://portal.gov.by",
        "address": "Республика Беларусь",
        "working_hours": "24/7",
    },
    {
        "title": "МФЦ Первомайского района г. Минска",
        "type": "МФЦ",
        "phone": "+375 17 200-14-44",
        "website_url": "https://mfc.by",
        "address": "г. Минск, ул. Ленина, 1",
        "working_hours": "Пн-Пт 09:00–20:00, Сб 10:00–15:00",
    },
    {
        "title": "ИМНС по г. Минску",
        "type": "Налоговая",
        "phone": "+375 17 229-30-00",
        "website_url": "https://nalog.gov.by",
        "address": "г. Минск, ул. К. Маркса, 38",
        "working_hours": "Пн-Пт 08:30–19:00",
    },
    {
        "title": "ОГиМ Первомайского РУВД г. Минска",
        "type": "МВД",
        "phone": "+375 17 280-10-00",
        "website_url": "https://mvd.gov.by",
        "address": "г. Минск, ул. Кнорина, 5",
        "working_hours": "Пн-Сб 08:00–20:00",
    },
    {
        "title": "Центр «Одно окно» г. Гомеля",
        "type": "МФЦ",
        "phone": "+375 232 50-50-50",
        "website_url": "https://gomel.gov.by",
        "address": "г. Гомель, ул. Советская, 12",
        "working_hours": "Пн-Пт 08:00–19:00, Сб 09:00–14:00",
    },
]


EXTREMIST: list[dict] = [
    {
        "title": "Канал «N» в реестре экстремистских формирований",
        "category": "registry",
        "source_url": "https://minjust.gov.by/ru/extremist-list/12345",
        "source_name": "Министерство юстиции РБ",
        "status": "published",
        "short_description": "Включён в реестр экстремистских формирований согласно решению Верховного Суда от 01.01.2026.",
    },
    {
        "title": "Telegram-канал «X»",
        "category": "registry",
        "source_url": "https://minjust.gov.by/ru/extremist-list/12346",
        "source_name": "Министерство юстиции РБ",
        "status": "published",
        "short_description": "Признан экстремистским материалом.",
    },
    {
        "title": "Издание «Y»",
        "category": "registry",
        "source_url": "https://minjust.gov.by/ru/extremist-list/12347",
        "source_name": "Министерство юстиции РБ",
        "status": "published",
        "short_description": "Запрещено к распространению на территории РБ.",
    },
    {
        "title": "Сообщество «Z» (плановая проверка)",
        "category": "registry",
        "source_url": "https://minjust.gov.by/ru/extremist-list/12348",
        "source_name": "Министерство юстиции РБ",
        "status": "draft",
        "short_description": "Находится на проверке, статус будет обновлён после подтверждения.",
    },
]


SCENARIOS: list[dict] = [
    {
        "problem_title": "Получение паспорта",
        "problem_category": "documents",
        "problem_short": "Как получить паспорт гражданина РБ: документы, сроки, МВД.",
        "scenarios": [
            {
                "title": "Получение паспорта в 14 лет (впервые)",
                "slug": "passport-14-first",
                "short_description": "Сценарий для подростка, получающего паспорт впервые.",
                "target_audience": "Подростки 14 лет и их родители",
                "difficulty": DifficultyLevel.EASY,
                "stages": [
                    {
                        "title": "Подготовка документов",
                        "steps": [
                            {"title": "Собрать свидетельство о рождении", "order": 0, "action": ActionType.INFO},
                            {"title": "Получить справку о регистрации (форма 1)", "order": 1, "action": ActionType.DOCUMENT_PREPARE},
                            {"title": "Оплатить госпошлину (1 БВ)", "order": 2, "action": ActionType.PAYMENT},
                        ],
                    },
                    {
                        "title": "Подача в ОГиМ",
                        "steps": [
                            {"title": "Записаться на приём через portal.gov.by", "order": 0, "action": ActionType.ONLINE_REQUEST},
                            {"title": "Подать документы и сфотографироваться", "order": 1, "action": ActionType.VISIT_OFFICE},
                        ],
                    },
                    {
                        "title": "Получение",
                        "steps": [
                            {"title": "Дождаться изготовления (до 7 рабочих дней)", "order": 0, "action": ActionType.WAITING},
                            {"title": "Получить паспорт и проверить данные", "order": 1, "action": ActionType.VISIT_OFFICE},
                        ],
                    },
                ],
            },
        ],
    },
    {
        "problem_title": "Рождение ребёнка",
        "problem_category": "family",
        "problem_short": "Регистрация рождения, пособия, документы для новорождённого.",
        "scenarios": [
            {
                "title": "Регистрация рождения и оформление пособий",
                "slug": "childbirth-registration",
                "short_description": "Пошаговый план: ЗАГС, пособия, СНИЛС, медкарта.",
                "target_audience": "Молодые родители",
                "difficulty": DifficultyLevel.MEDIUM,
                "stages": [
                    {
                        "title": "Регистрация в ЗАГСе",
                        "steps": [
                            {"title": "Подать заявление в ЗАГС в течение 3 месяцев", "order": 0, "action": ActionType.VISIT_OFFICE},
                            {"title": "Получить свидетельство о рождении", "order": 1, "action": ActionType.VISIT_OFFICE},
                        ],
                    },
                    {
                        "title": "Документы новорождённого",
                        "steps": [
                            {"title": "Оформить СНИЛС (через МФЦ или УП «Центр информационных технологий»)", "order": 0, "action": ActionType.ONLINE_REQUEST},
                            {"title": "Оформить медполис", "order": 1, "action": ActionType.VISIT_OFFICE},
                            {"title": "Прикрепить к поликлинике", "order": 2, "action": ActionType.VISIT_OFFICE},
                        ],
                    },
                    {
                        "title": "Пособия",
                        "steps": [
                            {"title": "Подать на единовременное пособие при рождении", "order": 0, "action": ActionType.ONLINE_REQUEST},
                            {"title": "Оформить ежемесячное пособие по уходу до 3 лет", "order": 1, "action": ActionType.ONLINE_REQUEST},
                        ],
                    },
                ],
            },
        ],
    },
    {
        "problem_title": "Жилищно-коммунальные услуги",
        "problem_category": "housing",
        "problem_short": "Оплата ЖКХ, субсидии, тарифы, обращения в ЖЭС.",
        "scenarios": [
            {
                "title": "Оформление субсидии на ЖКХ",
                "slug": "housing-subsidy",
                "short_description": "Как получить субсидию, если коммуналка > 20% дохода.",
                "target_audience": "Малообеспеченные семьи",
                "difficulty": DifficultyLevel.MEDIUM,
                "stages": [
                    {
                        "title": "Проверка права на субсидию",
                        "steps": [
                            {"title": "Посчитать расходы на ЖКУ за последние 6 месяцев", "order": 0, "action": ActionType.INFO},
                            {"title": "Сравнить с доходами семьи (> 20% даёт право)", "order": 1, "action": ActionType.INFO},
                        ],
                    },
                    {
                        "title": "Подача документов",
                        "steps": [
                            {"title": "Собрать справки о доходах всех членов семьи", "order": 0, "action": ActionType.DOCUMENT_PREPARE},
                            {"title": "Подать заявление в МФЦ или через portal.gov.by", "order": 1, "action": ActionType.ONLINE_REQUEST},
                        ],
                    },
                ],
            },
        ],
    },
]


def _ensure_authority(db: Session, data: dict) -> bool:
    existing = db.scalar(select(Authority).where(Authority.title == data["title"]))
    if existing:
        return False
    db.add(Authority(**data))
    return True


def _ensure_extremist(db: Session, data: dict) -> bool:
    existing = db.scalar(select(ExtremistEntry).where(ExtremistEntry.title == data["title"]))
    if existing:
        return False
    entry = ExtremistEntry(
        title=data["title"],
        category=data["category"],
        source_url=data["source_url"],
        source_name=data.get("source_name", ""),
        short_description=data.get("short_description", ""),
        status=data.get("status", "draft"),
        media_urls="[]",
        attachment_urls="[]",
        filters_json="{}",
    )
    db.add(entry)
    return True


def _ensure_scenarios(db: Session) -> int:
    added = 0
    for prob_data in SCENARIOS:
        prob = db.scalar(select(Problem).where(Problem.title == prob_data["problem_title"]))
        if not prob:
            prob = Problem(
                title=prob_data["problem_title"],
                slug=prob_data["problem_title"].lower().replace(" ", "-"),
                short_description=prob_data["problem_short"],
                category=prob_data["problem_category"],
                status=ContentStatus.PUBLISHED,
            )
            db.add(prob)
            db.flush()
            added += 1
        for scn in prob_data["scenarios"]:
            existing = db.scalar(select(Scenario).where(Scenario.slug == scn["slug"]))
            if existing:
                continue
            scn_obj = Scenario(
                problem_id=prob.id,
                title=scn["title"],
                slug=scn["slug"],
                short_description=scn["short_description"],
                target_audience=scn["target_audience"],
                difficulty_level=scn["difficulty"],
                status=ContentStatus.PUBLISHED,
                priority=0,
            )
            db.add(scn_obj)
            db.flush()
            for i, stg in enumerate(scn["stages"]):
                stg_obj = ScenarioStage(
                    scenario_id=scn_obj.id,
                    title=stg["title"],
                    order_index=i,
                )
                db.add(stg_obj)
                db.flush()
                for step in stg["steps"]:
                    db.add(ScenarioStep(
                        stage_id=stg_obj.id,
                        title=step["title"],
                        order_index=step["order"],
                        action_type=step["action"],
                    ))
            added += 1
    return added


def main() -> int:
    db = SessionLocal()
    try:
        auth_added = sum(1 for a in AUTHORITIES if _ensure_authority(db, a))
        ext_added = sum(1 for e in EXTREMIST if _ensure_extremist(db, e))
        scn_added = _ensure_scenarios(db)
        db.commit()
        print(f"[seed_admin_demo] authorities: +{auth_added}; extremist: +{ext_added}; scenarios/problems: +{scn_added}")
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
