from __future__ import annotations

from typing import Any, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend import schemas
from backend.enums import ContentStatus
from backend.models import (
    Article,
    AuditLog,
    Authority,
    Deadline,
    Document,
    LawUpdate,
    Problem,
    RelatedScenario,
    Scenario,
    ScenarioDependency,
    ScenarioStage,
    ScenarioStep,
    SourceReference,
)


ModelT = TypeVar("ModelT")


def create_entity(db: Session, model_cls: type[ModelT], payload: schemas.BaseModel) -> ModelT:
    obj = model_cls(**payload.model_dump(mode="json"))
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_entity(db: Session, obj: Any, payload: schemas.BaseModel) -> Any:
    for key, value in payload.model_dump(exclude_unset=True, mode="json").items():
        setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


def get_by_id(db: Session, model_cls: type[ModelT], obj_id: int) -> ModelT | None:
    return db.get(model_cls, obj_id)


def list_published_problems(db: Session) -> list[Problem]:
    stmt = (
        select(Problem)
        .where(Problem.status == ContentStatus.PUBLISHED)
        .order_by(Problem.title.asc())
    )
    return list(db.scalars(stmt).all())


def get_published_problem_by_slug(db: Session, slug: str) -> Problem | None:
    stmt = (
        select(Problem)
        .where(Problem.slug == slug, Problem.status == ContentStatus.PUBLISHED)
        .limit(1)
    )
    return db.scalar(stmt)


def list_published_problem_scenarios(db: Session, problem_id: int) -> list[Scenario]:
    stmt = (
        select(Scenario)
        .options(
            selectinload(Scenario.problem),
            selectinload(Scenario.stages).selectinload(ScenarioStage.steps),
        )
        .where(
            Scenario.problem_id == problem_id,
            Scenario.status == ContentStatus.PUBLISHED,
        )
        .order_by(Scenario.priority.desc(), Scenario.title.asc())
    )
    return list(db.scalars(stmt).all())


def list_published_scenarios(db: Session) -> list[Scenario]:
    stmt = (
        select(Scenario)
        .options(
            selectinload(Scenario.problem),
            selectinload(Scenario.stages).selectinload(ScenarioStage.steps),
        )
        .where(Scenario.status == ContentStatus.PUBLISHED)
        .order_by(Scenario.priority.desc(), Scenario.title.asc())
    )
    return list(db.scalars(stmt).all())


def get_published_scenario_by_slug(db: Session, slug: str) -> Scenario | None:
    stmt = (
        select(Scenario)
        .options(
            selectinload(Scenario.stages)
            .selectinload(ScenarioStage.steps)
            .selectinload(ScenarioStep.documents),
            selectinload(Scenario.stages)
            .selectinload(ScenarioStage.steps)
            .selectinload(ScenarioStep.notification_rules),
            selectinload(Scenario.stages)
            .selectinload(ScenarioStage.steps)
            .selectinload(ScenarioStep.authority),
            selectinload(Scenario.stages)
            .selectinload(ScenarioStage.steps)
            .selectinload(ScenarioStep.deadline),
            selectinload(Scenario.problem),
            selectinload(Scenario.dependencies),
            selectinload(Scenario.law_updates),
        )
        .where(Scenario.slug == slug, Scenario.status == ContentStatus.PUBLISHED)
        .limit(1)
    )
    return db.scalar(stmt)


def get_scenario_by_id(db: Session, scenario_id: int) -> Scenario | None:
    stmt = (
        select(Scenario)
        .options(
            selectinload(Scenario.stages)
            .selectinload(ScenarioStage.steps)
            .selectinload(ScenarioStep.documents),
            selectinload(Scenario.stages)
            .selectinload(ScenarioStage.steps)
            .selectinload(ScenarioStep.notification_rules),
            selectinload(Scenario.stages)
            .selectinload(ScenarioStage.steps)
            .selectinload(ScenarioStep.authority),
            selectinload(Scenario.stages)
            .selectinload(ScenarioStage.steps)
            .selectinload(ScenarioStep.deadline),
            selectinload(Scenario.problem),
            selectinload(Scenario.dependencies),
            selectinload(Scenario.law_updates),
        )
        .where(Scenario.id == scenario_id)
        .limit(1)
    )
    return db.scalar(stmt)


def list_published_scenario_steps(db: Session, slug: str) -> list[ScenarioStep]:
    scenario = get_published_scenario_by_slug(db, slug)
    if not scenario:
        return []
    steps: list[ScenarioStep] = []
    for stage in scenario.stages:
        steps.extend(stage.steps)
    return steps


def list_published_documents(db: Session) -> list[Document]:
    stmt = (
        select(Document)
        .where(Document.status == ContentStatus.PUBLISHED)
        .order_by(Document.title.asc())
    )
    return list(db.scalars(stmt).all())


def search_published_news(db: Session, query: str, limit: int = 25) -> list[Article]:
    """Лёгкий keyword-поиск по опубликованным новостям. Для RAG."""
    from backend.models import Article
    stmt = (
        select(Article)
        .where(Article.status == "published", Article.kind == "news")
        .order_by(Article.updated_at.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


def list_authorities(db: Session) -> list[Authority]:
    stmt = select(Authority).order_by(Authority.title.asc())
    return list(db.scalars(stmt).all())


def list_source_references_for_scenario(db: Session, scenario_id: int) -> list[SourceReference]:
    stmt = (
        select(SourceReference)
        .where(
            (
                (SourceReference.sourceable_type == "scenario")
                & (SourceReference.sourceable_id == scenario_id)
            )
            | (
                (SourceReference.sourceable_type == "stage")
                & (SourceReference.sourceable_id.in_(
                    select(ScenarioStage.id).where(ScenarioStage.scenario_id == scenario_id)
                ))
            )
            | (
                (SourceReference.sourceable_type == "step")
                & (
                    SourceReference.sourceable_id.in_(
                        select(ScenarioStep.id).join(ScenarioStage).where(ScenarioStage.scenario_id == scenario_id)
                    )
                )
            )
        )
        .order_by(SourceReference.id.asc())
    )
    return list(db.scalars(stmt).all())


def list_related_scenarios(db: Session, scenario_id: int) -> list[schemas.RelatedScenarioOut]:
    stmt = (
        select(RelatedScenario, Scenario)
        .join(Scenario, Scenario.id == RelatedScenario.related_scenario_id)
        .where(RelatedScenario.scenario_id == scenario_id)
        .order_by(RelatedScenario.id.asc())
    )
    rows = db.execute(stmt).all()
    return [
        schemas.RelatedScenarioOut(
            id=relation.id,
            scenario_id=relation.scenario_id,
            related_scenario_id=relation.related_scenario_id,
            relation_type=relation.relation_type,
            description=relation.description,
            related_scenario_title=related.title,
            related_scenario_slug=related.slug,
        )
        for relation, related in rows
    ]


def scenario_to_full_schema(db: Session, scenario: Scenario) -> schemas.ScenarioFullOut:
    sorted_stages = sorted(scenario.stages, key=lambda s: s.order_index)
    stages_out: list[schemas.ScenarioStageOut] = []
    for stage in sorted_stages:
        sorted_steps = sorted(stage.steps, key=lambda s: s.order_index)
        stage_out = schemas.ScenarioStageOut(
            id=stage.id,
            title=stage.title,
            description=stage.description,
            order_index=stage.order_index,
            is_required=stage.is_required,
            steps=[schemas.ScenarioStepOut.model_validate(step) for step in sorted_steps],
        )
        stages_out.append(stage_out)

    payload = schemas.ScenarioFullOut.model_validate(scenario)
    return payload.model_copy(
        update={
            "stages": stages_out,
            "category": scenario.problem.category if scenario.problem else "",
            "related_scenarios": list_related_scenarios(db, scenario.id),
            "source_references": [
                schemas.SourceReferenceOut.model_validate(item)
                for item in list_source_references_for_scenario(db, scenario.id)
            ],
            "law_updates": [
                schemas.LawUpdateOut.model_validate(item)
                for item in scenario.law_updates
            ],
            "dependencies": [
                schemas.ScenarioDependencyOut.model_validate(item)
                for item in scenario.dependencies
            ],
        }
    )


def list_scenarios(
    db: Session,
    problem_id: int | None = None,
    status: ContentStatus | None = None,
) -> list[Scenario]:
    stmt = select(Scenario)
    if problem_id is not None:
        stmt = stmt.where(Scenario.problem_id == problem_id)
    if status is not None:
        stmt = stmt.where(Scenario.status == status)
    stmt = stmt.order_by(Scenario.updated_at.desc())
    return list(db.scalars(stmt).all())


def list_problems_admin(db: Session) -> list[Problem]:
    stmt = select(Problem).order_by(Problem.updated_at.desc())
    return list(db.scalars(stmt).all())


def list_documents_admin(db: Session) -> list[Document]:
    stmt = select(Document).order_by(Document.updated_at.desc())
    return list(db.scalars(stmt).all())


def list_deadlines_admin(db: Session) -> list[Deadline]:
    stmt = select(Deadline).order_by(Deadline.updated_at.desc())
    return list(db.scalars(stmt).all())


def list_law_updates_admin(db: Session) -> list[LawUpdate]:
    stmt = select(LawUpdate).order_by(LawUpdate.update_date.desc())
    return list(db.scalars(stmt).all())


def list_published_law_updates(db: Session) -> list[LawUpdate]:
    """E7: публичный список опубликованных закон-апдейтов для Flet-клиента."""
    from backend.enums import LawUpdateStatus
    stmt = (
        select(LawUpdate)
        .where(LawUpdate.status == LawUpdateStatus.APPLIED)
        .order_by(LawUpdate.update_date.desc())
    )
    return list(db.scalars(stmt).all())


def log_audit_event(
    db: Session,
    actor: str,
    action: str,
    role_id: str = "content_editor",
    event_type: str = "other",
    status: str = "ok",
    actor_user_id: int | None = None,
    entity_type: str = "",
    entity_id: str | int = "",
    before_json: str = "",
    after_json: str = "",
    ip_address: str = "",
    user_agent: str = "",
) -> AuditLog:
    """H9 — Записать событие в таблицу audit_logs."""
    if event_type == "other":
        lower = action.lower()
        if lower.startswith("создан") or lower.startswith("добавлен"):
            event_type = "create"
        elif lower.startswith("изменён") or lower.startswith("обновлён"):
            event_type = "update"
        elif lower.startswith("удалён"):
            event_type = "delete"
        elif lower.startswith("опубликован"):
            event_type = "publish"
    entry = AuditLog(
        actor_user_id=actor_user_id,
        actor=actor,
        action=action,
        role_id=role_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id != "" else "",
        before_json=before_json,
        after_json=after_json,
        ip_address=ip_address,
        user_agent=user_agent,
        status=status,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def list_audit_logs(db: Session, limit: int = 200) -> list[AuditLog]:
    """H9 — Последние N записей аудита для admin endpoint."""
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    return list(db.scalars(stmt).all())
