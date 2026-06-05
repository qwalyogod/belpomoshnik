"""Полный перенос контента из Flet-макета (src/data/mock_data.py) в БД.

Идемпотентно: повторный запуск не дублирует записи (проверка по slug/title/url).
Покрывает: проблемы (справочник), жизненные сценарии со стадиями/шагами/
документами/учреждениями/источниками, учреждения-справочник, правовые обновления.
"""

from __future__ import annotations

import importlib.util
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from backend.enums import ContentStatus, DifficultyLevel
from backend.models import (
    Authority,
    Document,
    LawUpdate,
    Problem,
    Scenario,
    ScenarioStage,
    ScenarioStep,
    SourceReference,
)

_DIFFICULTY = {
    "Лёгкая": DifficultyLevel.EASY,
    "Легкая": DifficultyLevel.EASY,
    "Низкая": DifficultyLevel.EASY,
    "Средняя": DifficultyLevel.MEDIUM,
    "Сложная": DifficultyLevel.HARD,
    "Высокая": DifficultyLevel.HARD,
}


def _load_mock_data():
    root = Path(__file__).resolve().parents[3]
    path = root / "src" / "data" / "mock_data.py"
    spec = importlib.util.spec_from_file_location("flet_mock_data", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def _parse_date(value: str) -> datetime:
    for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            continue
    return datetime.now(timezone.utc)


def seed_full_content(db: Session) -> dict[str, int]:
    m = _load_mock_data()
    counts = {"problems": 0, "scenarios": 0, "stages": 0, "steps": 0, "documents": 0, "authorities": 0, "sources": 0, "law": 0}

    # ---- Problems (catalogue) -------------------------------------------------
    problems_by_category: dict[str, Problem] = {}
    for p in m.PROBLEMS:
        slug = p["id"]
        existing = db.query(Problem).filter(Problem.slug == slug).first()
        if existing:
            problems_by_category.setdefault(existing.category, existing)
            continue
        problem = Problem(
            title=p.get("title", "Проблема"),
            slug=slug,
            short_description=(p.get("description", "")[:500]),
            description=p.get("description", ""),
            icon="HELP_OUTLINE",
            category=p.get("category_name", ""),
            status=ContentStatus.PUBLISHED,
        )
        db.add(problem)
        db.flush()
        problems_by_category.setdefault(problem.category, problem)
        counts["problems"] += 1

    def _problem_for(category_name: str) -> Problem:
        if category_name in problems_by_category:
            return problems_by_category[category_name]
        # bucket problem for categories without a catalogue entry
        slug = f"bucket-{abs(hash(category_name)) % 100000}"
        problem = db.query(Problem).filter(Problem.slug == slug).first()
        if not problem:
            problem = Problem(
                title=category_name or "Жизненные ситуации",
                slug=slug,
                short_description=f"Жизненные ситуации: {category_name}.",
                description="",
                icon="CATEGORY",
                category=category_name,
                status=ContentStatus.PUBLISHED,
            )
            db.add(problem)
            db.flush()
        problems_by_category[category_name] = problem
        return problem

    # ---- Authorities (reference directory) -----------------------------------
    def _authority_by_title(title: str) -> Authority | None:
        return db.query(Authority).filter(Authority.title == title).first()

    for inst in getattr(m, "INSTITUTIONS", []):
        title = inst.get("short_name") or inst.get("full_name") or "Учреждение"
        if _authority_by_title(title):
            continue
        db.add(Authority(
            title=title,
            description=inst.get("full_name", "") or ", ".join(inst.get("services", [])),
            website_url=inst.get("website", ""),
            phone=inst.get("phone", ""),
            address=inst.get("address", ""),
            working_hours=inst.get("working_hours", ""),
            type=inst.get("institution_type", ""),
            region=inst.get("region", ""),
            city=inst.get("city", ""),
        ))
        counts["authorities"] += 1
    db.flush()

    # ---- Scenarios with stages/steps/docs/authorities/sources ----------------
    for tpl in m.SCENARIO_TEMPLATES:
        slug = tpl["id"]
        if db.query(Scenario).filter(Scenario.slug == slug).first():
            continue
        category = tpl.get("category", "")
        problem = _problem_for(category)
        scenario = Scenario(
            problem_id=problem.id,
            title=tpl.get("title", "Сценарий"),
            slug=slug,
            short_description=(tpl.get("short_description", "")[:500]),
            description=tpl.get("description", ""),
            target_audience="Граждане Республики Беларусь",
            estimated_duration=tpl.get("estimated_duration", ""),
            difficulty_level=_DIFFICULTY.get(tpl.get("difficulty", ""), DifficultyLevel.MEDIUM),
            status=ContentStatus.PUBLISHED,
            priority=50,
        )
        db.add(scenario)
        db.flush()
        counts["scenarios"] += 1

        # authorities for this scenario (deduped globally), assigned round-robin
        scenario_authorities: list[Authority] = []
        for a in tpl.get("authorities", []):
            title = a.get("title", "Учреждение")
            obj = _authority_by_title(title)
            if not obj:
                obj = Authority(title=title, description=a.get("description", ""), type="", region="", city="")
                db.add(obj)
                db.flush()
                counts["authorities"] += 1
            scenario_authorities.append(obj)

        # documents for this scenario (linked to the first step below)
        scenario_documents: list[Document] = []
        for d in tpl.get("documents", []):
            doc = Document(
                title=d.get("title", "Документ"),
                description=d.get("description", ""),
                document_type="other",
                is_required=bool(d.get("required", True)),
                where_to_get="",
                validity_period="",
                status=ContentStatus.PUBLISHED,
            )
            db.add(doc)
            scenario_documents.append(doc)
            counts["documents"] += 1
        db.flush()

        # stages
        stage_by_key: dict[str, ScenarioStage] = {}
        for idx, st in enumerate(tpl.get("stages", []), start=1):
            stage = ScenarioStage(
                scenario_id=scenario.id,
                title=st.get("title", "Этап"),
                description=st.get("description", ""),
                order_index=st.get("order_index", idx),
                is_required=True,
            )
            db.add(stage)
            db.flush()
            stage_by_key[st.get("id", str(idx))] = stage
            counts["stages"] += 1

        # steps (grouped by stage_id)
        first_step: ScenarioStep | None = None
        auth_n = len(scenario_authorities)
        for i, task in enumerate(tpl.get("tasks", [])):
            stage = stage_by_key.get(task.get("stage_id")) or next(iter(stage_by_key.values()), None)
            if stage is None:
                continue
            deadline = task.get("deadline", "")
            step = ScenarioStep(
                stage_id=stage.id,
                title=task.get("title", "Шаг"),
                description=(f"Срок: {deadline}" if deadline else ""),
                order_index=i + 1,
                action_type="info",
                authority_id=scenario_authorities[i % auth_n].id if auth_n else None,
                is_required=True,
            )
            db.add(step)
            db.flush()
            if first_step is None:
                first_step = step
            counts["steps"] += 1

        # attach scenario documents to the first step (M2M) so they surface
        if first_step and scenario_documents:
            first_step.documents.extend(scenario_documents)

        # sources (polymorphic → scenario)
        for s in tpl.get("sources", []):
            db.add(SourceReference(
                sourceable_type="scenario",
                sourceable_id=scenario.id,
                title=s.get("title", "Источник"),
                url=s.get("url", ""),
                source_type="government_portal",
                description="",
            ))
            counts["sources"] += 1
        db.flush()

    # ---- Law updates ----------------------------------------------------------
    for law in getattr(m, "LEGAL_UPDATES", []):
        title = law.get("title", "Обновление")
        if db.query(LawUpdate).filter(LawUpdate.title == title).first():
            continue
        body = law.get("short", "")
        if law.get("what_to_do"):
            body = f"{body}\n\nЧто делать: {law['what_to_do']}"
        db.add(LawUpdate(
            title=title,
            description=body,
            source_url=law.get("source_url", ""),
            update_date=_parse_date(law.get("date", "")),
            status="applied",  # публичный список показывает только applied
        ))
        counts["law"] += 1

    db.commit()
    return counts
