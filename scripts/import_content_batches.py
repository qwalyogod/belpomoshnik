#!/usr/bin/env python3
"""Import validated content_*_2022_2026.json batches into the backend DB."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from sqlalchemy import delete, select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from backend.database import SessionLocal  # noqa: E402
from backend.enums import ActionType, ContentStatus, DifficultyLevel, LawUpdateStatus, SourceType  # noqa: E402
from backend.models import (  # noqa: E402
    Article,
    Document,
    ExtremistEntry,
    LawUpdate,
    Problem,
    Scenario,
    ScenarioDependency,
    ScenarioStage,
    ScenarioStep,
    SourceReference,
)


IMPORT_DIR = PROJECT_ROOT / "data" / "import"

DIFFICULTY = {
    "Простая": DifficultyLevel.EASY,
    "Лёгкая": DifficultyLevel.EASY,
    "Легкая": DifficultyLevel.EASY,
    "Средняя": DifficultyLevel.MEDIUM,
    "Сложная": DifficultyLevel.HARD,
}

CATEGORY_LABELS = {
    "documents": "Документы",
    "family": "Семья",
    "work": "Работа",
    "business": "Бизнес / ИП",
    "housing": "Жильё и ЖКХ",
    "taxes": "Налоги",
    "health": "Здоровье",
    "auto": "Авто",
}

SOURCE_TYPE_BY_SOURCE_ID = {
    "source-pravo": SourceType.LAW,
    "source-portal-gov": SourceType.GOVERNMENT_PORTAL,
    "source-mintrud": SourceType.MINISTRY,
    "source-nalog": SourceType.TAX,
    "source-minjust": SourceType.REGISTRY,
    "source-mvd": SourceType.GOVERNMENT_PORTAL,
    "source-gibdd": SourceType.GOVERNMENT_PORTAL,
    "source-court": SourceType.COURT,
    "source-nbki": SourceType.REGISTRY,
    "source-minzdrav": SourceType.MINISTRY,
    "source-raschet-erip": SourceType.GOVERNMENT_PORTAL,
    "source-egr": SourceType.REGISTRY,
    "source-nces": SourceType.GOVERNMENT_PORTAL,
    "source-115": SourceType.GOVERNMENT_PORTAL,
    "source-beltechosmotr": SourceType.REGISTRY,
    "source-president": SourceType.GOVERNMENT_PORTAL,
    "source-government": SourceType.GOVERNMENT_PORTAL,
}


def dumps(value: Any) -> str:
    return json.dumps(value if value is not None else [], ensure_ascii=False)


def parse_date(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str) or not value:
        return datetime.now(timezone.utc)
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return datetime.now(timezone.utc)


def optional_date(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    return parse_date(value)


def action_type_for(title: str) -> ActionType:
    text = title.lower()
    if any(word in text for word in ("оплат", "госпошлин", "платеж")):
        return ActionType.PAYMENT
    if any(word in text for word in ("подготов", "паспорт", "справк", "документ")):
        return ActionType.DOCUMENT_PREPARE
    if any(word in text for word in ("обрат", "подать", "загс", "гаи", "инспекц", "исполком")):
        return ActionType.VISIT_OFFICE
    if any(word in text for word in ("ожид", "получить", "проверить")):
        return ActionType.WAITING
    return ActionType.INFO


def source_type_from_url(url: str) -> SourceType:
    lower = (url or "").lower()
    if "pravo.by" in lower:
        return SourceType.LAW
    if "nalog.gov.by" in lower:
        return SourceType.TAX
    if "court.gov.by" in lower:
        return SourceType.COURT
    if any(domain in lower for domain in ("mintrud.gov.by", "minzdrav.gov.by", "mvd.gov.by", "minjust.gov.by")):
        return SourceType.MINISTRY
    if any(domain in lower for domain in ("egr.gov.by", "gto.by")):
        return SourceType.REGISTRY
    if "portal.gov.by" in lower or "raschet.by" in lower or "government.by" in lower:
        return SourceType.GOVERNMENT_PORTAL
    return SourceType.OTHER


def get_problem(db: Session, slug: str) -> Problem | None:
    return db.scalar(select(Problem).where(Problem.slug == slug))


def upsert_problem(db: Session, item: dict[str, Any], counts: dict[str, int], *, bucket: bool = False) -> Problem:
    slug = str(item["id"])
    problem = get_problem(db, slug)
    created = problem is None
    if problem is None:
        problem = Problem(slug=slug, title=item.get("title") or "Проблема")
        db.add(problem)
    problem.title = item.get("title") or problem.title
    problem.short_description = (item.get("shortDescription") or "")[:500]
    problem.description = item.get("shortDescription") or ""
    problem.category = item.get("category") or ""
    problem.icon = item.get("category") or "info"
    problem.what_to_do_now = "\n".join(item.get("whatToDoNow") or [])
    problem.steps_json = dumps(item.get("steps") or [])
    problem.documents_json = dumps(item.get("documents") or [])
    problem.deadlines_json = dumps(item.get("deadlines") or [])
    problem.institutions_json = dumps(item.get("institutions") or [])
    problem.mistakes_json = dumps(item.get("mistakes") or [])
    problem.status = ContentStatus.ARCHIVED if bucket else ContentStatus.PUBLISHED
    db.flush()
    counts["problems_created" if created else "problems_updated"] += 1
    import_sources(db, "problem", problem.id, item.get("sources") or [], counts)
    return problem


def get_scenario_bucket(db: Session, category: str, counts: dict[str, int]) -> Problem:
    slug = f"life-events-{category}"
    title = f"Жизненные сценарии: {CATEGORY_LABELS.get(category, category)}"
    item = {
        "id": slug,
        "title": title,
        "category": category,
        "shortDescription": f"Служебная категория для сценариев раздела «{CATEGORY_LABELS.get(category, category)}».",
        "whatToDoNow": [],
        "steps": [],
        "documents": [],
        "deadlines": [],
        "institutions": [],
        "mistakes": [],
    }
    return upsert_problem(db, item, counts, bucket=True)


def clear_scenario_content(db: Session, scenario: Scenario) -> None:
    db.execute(delete(ScenarioDependency).where(ScenarioDependency.scenario_id == scenario.id))
    db.execute(delete(SourceReference).where(
        SourceReference.sourceable_type == "scenario",
        SourceReference.sourceable_id == scenario.id,
    ))
    for stage in list(scenario.stages):
        db.delete(stage)
    db.flush()


def upsert_document(db: Session, title: str, required: bool, counts: dict[str, int]) -> Document:
    doc = db.scalar(select(Document).where(Document.title == title))
    created = doc is None
    if doc is None:
        doc = Document(title=title)
        db.add(doc)
    doc.description = ""
    doc.document_type = "other"
    doc.is_required = bool(required)
    doc.status = ContentStatus.PUBLISHED
    db.flush()
    counts["documents_created" if created else "documents_updated"] += 1
    return doc


def upsert_scenario(db: Session, item: dict[str, Any], counts: dict[str, int]) -> Scenario:
    slug = str(item["id"])
    category = item.get("category") or ""
    problem = get_scenario_bucket(db, category, counts)
    scenario = db.scalar(select(Scenario).where(Scenario.slug == slug))
    created = scenario is None
    if scenario is None:
        scenario = Scenario(problem_id=problem.id, slug=slug, title=item.get("title") or "Сценарий")
        db.add(scenario)
    else:
        clear_scenario_content(db, scenario)
    scenario.problem_id = problem.id
    scenario.title = item.get("title") or scenario.title
    scenario.short_description = (item.get("shortDescription") or "")[:500]
    scenario.description = item.get("longDescription") or ""
    scenario.target_audience = item.get("forWhom") or ""
    scenario.estimated_duration = item.get("estimatedTime") or ""
    scenario.difficulty_level = DIFFICULTY.get(item.get("difficulty"), DifficultyLevel.MEDIUM)
    scenario.status = ContentStatus.PUBLISHED
    scenario.priority = 20
    scenario.content_verified_at = parse_date((item.get("sources") or [{}])[0].get("checked_at") if item.get("sources") else None)
    scenario.verified_by = "content-import"
    scenario.verification_notes = "Импортировано из content_*_2022_2026.json после структурной проверки."
    db.flush()
    counts["scenarios_created" if created else "scenarios_updated"] += 1

    docs = [upsert_document(db, d.get("title", "Документ"), bool(d.get("required", True)), counts) for d in item.get("documents") or [] if isinstance(d, dict)]
    task_to_step: dict[str, ScenarioStep] = {}
    first_step: ScenarioStep | None = None
    for stage_index, stage_item in enumerate(item.get("stages") or [], start=1):
        stage = ScenarioStage(
            scenario_id=scenario.id,
            title=stage_item.get("title") or "Этап",
            description="",
            order_index=stage_index,
            is_required=True,
        )
        db.add(stage)
        db.flush()
        counts["stages_created"] += 1
        for step_index, task in enumerate(stage_item.get("tasks") or [], start=1):
            step = ScenarioStep(
                stage_id=stage.id,
                title=task.get("title") or "Задача",
                description=task.get("durationHint") or "",
                order_index=step_index,
                action_type=action_type_for(task.get("title") or ""),
                is_required=True,
            )
            db.add(step)
            db.flush()
            if first_step is None:
                first_step = step
            if task.get("id"):
                task_to_step[str(task["id"])] = step
            counts["steps_created"] += 1
    if first_step and docs:
        first_step.documents.extend(docs)
    for stage_item in item.get("stages") or []:
        for task in stage_item.get("tasks") or []:
            step = task_to_step.get(str(task.get("id")))
            if not step:
                continue
            for dep_id in task.get("blockedBy") or []:
                dep_step = task_to_step.get(str(dep_id))
                if dep_step:
                    db.add(ScenarioDependency(
                        scenario_id=scenario.id,
                        step_id=step.id,
                        depends_on_step_id=dep_step.id,
                        description=f"Сначала выполните: {dep_step.title}",
                    ))
                    counts["dependencies_created"] += 1
    import_sources(db, "scenario", scenario.id, item.get("sources") or [], counts)
    return scenario


def import_sources(db: Session, sourceable_type: str, sourceable_id: int, sources: list[dict[str, Any]], counts: dict[str, int]) -> None:
    db.execute(delete(SourceReference).where(
        SourceReference.sourceable_type == sourceable_type,
        SourceReference.sourceable_id == sourceable_id,
    ))
    for source in sources:
        if not isinstance(source, dict) or not source.get("url"):
            continue
        db.add(SourceReference(
            sourceable_type=sourceable_type,
            sourceable_id=sourceable_id,
            title=source.get("title") or "Источник",
            url=source.get("url") or "",
            source_type=source_type_from_url(source.get("url") or ""),
            description=source.get("description") or "",
            last_checked_at=optional_date(source.get("checked_at") or source.get("checkedAt")),
        ))
        counts["sources_created"] += 1


def upsert_article(db: Session, item: dict[str, Any], counts: dict[str, int]) -> Article:
    source_url = item.get("sourceUrl") or ""
    stmt = select(Article).where(Article.source_url == source_url) if source_url else select(Article).where(Article.title == item.get("title"))
    article = db.scalar(stmt)
    created = article is None
    if article is None:
        article = Article(kind="news", title=item.get("title") or "Новость")
        db.add(article)
    article.kind = "news"
    article.title = item.get("title") or article.title
    article.summary = item.get("summary") or ""
    article.body_html = item.get("bodyHtml") or ""
    article.cover = item.get("cover") or ""
    article.video = item.get("video") or ""
    article.gallery = dumps(item.get("gallery") or [])
    article.tags = dumps(item.get("tags") or [])
    article.category = item.get("category") or ""
    article.source = item.get("source") or ""
    article.source_url = source_url
    article.status = "published"
    article.author_name = "Редакция Белпомощника"
    article.author_role = "content_editor"
    article.proposed_by = ""
    article.proposer_id = None
    article.publish_date = item.get("date") or ""
    article.views = int(item.get("views_seed") or article.views or 0)
    db.flush()
    counts["articles_created" if created else "articles_updated"] += 1
    return article


def upsert_law_update(db: Session, item: dict[str, Any], counts: dict[str, int]) -> LawUpdate:
    source = item.get("source") or {}
    source_url = source.get("url") or ""
    stmt = select(LawUpdate).where(LawUpdate.title == item.get("title"))
    law = db.scalar(stmt)
    created = law is None
    if law is None:
        law = LawUpdate(title=item.get("title") or "Закон-апдейт", update_date=parse_date(item.get("effectiveDate")))
        db.add(law)
    law.title = item.get("title") or law.title
    law.description = item.get("summary") or item.get("whatChanged") or ""
    law.body_html = item.get("bodyHtml") or ""
    law.source_url = source_url
    law.update_date = parse_date(item.get("effectiveDate"))
    law.status = LawUpdateStatus.APPLIED
    db.flush()
    counts["law_updates_created" if created else "law_updates_updated"] += 1
    return law


def upsert_extremist_entry(db: Session, item: dict[str, Any], counts: dict[str, int]) -> ExtremistEntry:
    stmt = select(ExtremistEntry).where(
        ExtremistEntry.title == item.get("title"),
        ExtremistEntry.source_url == item.get("source_url"),
    )
    entry = db.scalar(stmt)
    created = entry is None
    if entry is None:
        entry = ExtremistEntry(title=item.get("title") or "Запись", source_url=item.get("source_url") or "")
        db.add(entry)
    entry.title = item.get("title") or entry.title
    entry.category = item.get("category") or "registry"
    entry.source_url = item.get("source_url") or ""
    entry.source_name = item.get("source_name") or ""
    entry.included_at = optional_date(item.get("included_at"))
    entry.last_checked_at = optional_date(item.get("last_checked_at"))
    entry.short_description = item.get("short_description") or ""
    entry.cover_url = item.get("cover_url") or ""
    entry.media_urls = dumps(item.get("media_urls") or [])
    entry.attachment_urls = dumps(item.get("attachment_urls") or [])
    entry.filters_json = item.get("filters_json") or "{}"
    entry.status = item.get("status") or "draft"
    db.flush()
    counts["extremist_created" if created else "extremist_updated"] += 1
    return entry


def import_file(db: Session, path: Path, counts: dict[str, int]) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    for item in data.get("problems") or []:
        upsert_problem(db, item, counts)
    for item in data.get("scenarios") or []:
        upsert_scenario(db, item, counts)
    for item in data.get("news_articles") or []:
        upsert_article(db, item, counts)
    for item in data.get("law_updates") or []:
        upsert_law_update(db, item, counts)
    for item in data.get("extremist_entries") or []:
        upsert_extremist_entry(db, item, counts)
    counts["files_imported"] += 1


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Импорт валидированных content-батчей в backend БД.")
    parser.add_argument("files", nargs="*", type=Path, help="JSON-файлы. По умолчанию data/import/content_*_2022_2026.json.")
    parser.add_argument("--dry-run", action="store_true", help="Проверить импорт без commit.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    files = args.files or sorted(IMPORT_DIR.glob("content_*_2022_2026.json"))
    if not files:
        print("Нет файлов для импорта.")
        return 0
    counts: dict[str, int] = defaultdict(int)
    with SessionLocal() as db:
        for path in files:
            import_file(db, path, counts)
        if args.dry_run:
            db.rollback()
        else:
            db.commit()
    print(json.dumps({"dry_run": args.dry_run, "counts": dict(sorted(counts.items()))}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
