from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend import schemas
from backend.schemas import ReorderPayload, ScenarioVerifyNotesPayload
from backend.api.auth import get_current_user_email, require_role
from backend.database import get_db
from backend.enums import ContentStatus
from sqlalchemy import select

from backend.models import (
    Authority,
    Deadline,
    Document,
    ExtremistEntry,
    LawUpdate,
    NotificationRule,
    Problem,
    RelatedScenario,
    Scenario,
    ScenarioDependency,
    ScenarioStage,
    ScenarioStep,
    SourceReference,
    User,
)
from backend.service import (
    create_entity,
    get_by_id,
    get_scenario_by_id,
    list_audit_logs,
    list_deadlines_admin,
    list_documents_admin,
    list_law_updates_admin,
    list_problems_admin,
    list_scenarios,
    log_audit_event,
    scenario_to_full_schema,
    update_entity,
)


router = APIRouter(
    prefix="/api/admin",
    tags=["admin"],
    dependencies=[Depends(require_role("content_editor"))],
)


def _must_get(db: Session, model, obj_id: int, message: str):
    obj = get_by_id(db, model, obj_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
    return obj


@router.get("/problems", response_model=list[schemas.ProblemPublicOut])
def admin_list_problems(db: Session = Depends(get_db)):
    return [schemas.ProblemPublicOut.model_validate(item) for item in list_problems_admin(db)]


@router.post("/problems", response_model=schemas.ProblemPublicOut, status_code=status.HTTP_201_CREATED)
def admin_create_problem(
    payload: schemas.ProblemCreate,
    db: Session = Depends(get_db),
    actor: str = Depends(get_current_user_email),
):
    obj = create_entity(db, Problem, payload)
    log_audit_event(db, actor=actor, action=f"Создана проблема: «{obj.title}»", event_type="create")
    return schemas.ProblemPublicOut.model_validate(obj)


@router.put("/problems/{problem_id}", response_model=schemas.ProblemPublicOut)
def admin_update_problem(problem_id: int, payload: schemas.ProblemUpdate, db: Session = Depends(get_db)):
    problem = _must_get(db, Problem, problem_id, "Проблема не найдена")
    obj = update_entity(db, problem, payload)
    return schemas.ProblemPublicOut.model_validate(obj)


@router.delete("/problems/{problem_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_problem(
    problem_id: int,
    db: Session = Depends(get_db),
    actor: str = Depends(get_current_user_email),
):
    problem = _must_get(db, Problem, problem_id, "Проблема не найдена")
    log_audit_event(db, actor=actor, action=f"Удалена проблема: «{problem.title}»", event_type="delete")
    db.delete(problem)
    db.commit()


@router.get("/scenarios", response_model=list[schemas.ScenarioPublicSummary])
def admin_list_scenarios(
    problem_id: int | None = Query(default=None),
    status_filter: ContentStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
):
    items = list_scenarios(db, problem_id=problem_id, status=status_filter)
    return [schemas.ScenarioPublicSummary.model_validate(item) for item in items]


@router.post("/scenarios", response_model=schemas.ScenarioPublicSummary, status_code=status.HTTP_201_CREATED)
def admin_create_scenario(
    payload: schemas.ScenarioCreate,
    db: Session = Depends(get_db),
    actor: str = Depends(get_current_user_email),
):
    _must_get(db, Problem, payload.problem_id, "Проблема для сценария не найдена")
    obj = create_entity(db, Scenario, payload)
    log_audit_event(db, actor=actor, action=f"Создан сценарий: «{obj.title}»", event_type="create")
    return schemas.ScenarioPublicSummary.model_validate(obj)


@router.put("/scenarios/{scenario_id}", response_model=schemas.ScenarioPublicSummary)
def admin_update_scenario(scenario_id: int, payload: schemas.ScenarioUpdate, db: Session = Depends(get_db)):
    scenario = _must_get(db, Scenario, scenario_id, "Сценарий не найден")
    if payload.problem_id is not None:
        _must_get(db, Problem, payload.problem_id, "Новая проблема для сценария не найдена")
    obj = update_entity(db, scenario, payload)
    return schemas.ScenarioPublicSummary.model_validate(obj)


@router.post("/scenarios/{scenario_id}/verify", response_model=schemas.ScenarioPublicSummary)
def admin_verify_scenario(
    scenario_id: int,
    db: Session = Depends(get_db),
    actor: str = Depends(get_current_user_email),
):
    """P5 — Отметить сценарий как проверенный по официальным источникам."""
    from datetime import datetime, timezone as _tz

    scenario = _must_get(db, Scenario, scenario_id, "Сценарий не найден")
    scenario.content_verified_at = datetime.now(_tz.utc)
    scenario.verified_by = actor
    db.commit()
    db.refresh(scenario)
    log_audit_event(
        db,
        actor=actor,
        action=f"Сценарий верифицирован: «{scenario.title}»",
        event_type="verify",
    )
    return schemas.ScenarioPublicSummary.model_validate(scenario)


@router.post("/scenarios/{scenario_id}/verify-notes", response_model=schemas.ScenarioPublicSummary)
def admin_set_verification_notes(
    scenario_id: int,
    payload: schemas.ScenarioVerifyNotesPayload,
    db: Session = Depends(get_db),
    actor: str = Depends(get_current_user_email),
):
    """P5 — Сохранить заметки верификации (что проверено, источники)."""
    scenario = _must_get(db, Scenario, scenario_id, "Сценарий не найден")
    scenario.verification_notes = payload.notes
    db.commit()
    db.refresh(scenario)
    log_audit_event(
        db,
        actor=actor,
        action=f"Обновлены заметки верификации: «{scenario.title}»",
        event_type="update",
    )
    return schemas.ScenarioPublicSummary.model_validate(scenario)


@router.delete("/scenarios/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_scenario(
    scenario_id: int,
    db: Session = Depends(get_db),
    actor: str = Depends(get_current_user_email),
):
    scenario = _must_get(db, Scenario, scenario_id, "Сценарий не найден")
    log_audit_event(db, actor=actor, action=f"Удалён сценарий: «{scenario.title}»", event_type="delete")
    db.delete(scenario)
    db.commit()


@router.get("/scenarios/{scenario_id}", response_model=schemas.ScenarioFullOut)
def admin_get_scenario(scenario_id: int, db: Session = Depends(get_db)):
    scenario = get_scenario_by_id(db, scenario_id)
    if not scenario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Сценарий не найден")
    return scenario_to_full_schema(db, scenario)


@router.get("/scenarios/{scenario_id}/stages", response_model=list[schemas.ScenarioStageOut])
def admin_list_scenario_stages(scenario_id: int, db: Session = Depends(get_db)):
    scenario = get_scenario_by_id(db, scenario_id)
    if not scenario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Сценарий не найден")
    return [schemas.ScenarioStageOut.model_validate(item) for item in scenario.stages]


@router.post("/scenarios/{scenario_id}/stages", response_model=schemas.ScenarioStageOut, status_code=status.HTTP_201_CREATED)
def admin_create_stage(scenario_id: int, payload: schemas.ScenarioStageCreate, db: Session = Depends(get_db)):
    _must_get(db, Scenario, scenario_id, "Сценарий не найден")
    if payload.scenario_id != scenario_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="scenario_id в payload не совпадает с URL")
    obj = create_entity(db, ScenarioStage, payload)
    return schemas.ScenarioStageOut.model_validate(obj)


@router.put("/stages/{stage_id}", response_model=schemas.ScenarioStageOut)
def admin_update_stage(stage_id: int, payload: schemas.ScenarioStageUpdate, db: Session = Depends(get_db)):
    stage = _must_get(db, ScenarioStage, stage_id, "Этап не найден")
    obj = update_entity(db, stage, payload)
    return schemas.ScenarioStageOut.model_validate(obj)


@router.delete("/stages/{stage_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_stage(stage_id: int, db: Session = Depends(get_db)):
    stage = _must_get(db, ScenarioStage, stage_id, "Этап не найден")
    db.delete(stage)
    db.commit()


@router.patch("/scenarios/{scenario_id}/stages/reorder", status_code=status.HTTP_204_NO_CONTENT)
def admin_reorder_stages(scenario_id: int, payload: schemas.ReorderPayload, db: Session = Depends(get_db)):
    """Переставить этапы сценария. payload.ids — новый порядок id этапов."""
    _must_get(db, Scenario, scenario_id, "Сценарий не найден")
    for idx, stage_id in enumerate(payload.ids):
        stage = db.get(ScenarioStage, stage_id)
        if stage and stage.scenario_id == scenario_id:
            stage.order_index = idx
    db.commit()


@router.patch("/stages/{stage_id}/steps/reorder", status_code=status.HTTP_204_NO_CONTENT)
def admin_reorder_steps(stage_id: int, payload: schemas.ReorderPayload, db: Session = Depends(get_db)):
    """Переставить шаги этапа. payload.ids — новый порядок id шагов."""
    _must_get(db, ScenarioStage, stage_id, "Этап не найден")
    for idx, step_id in enumerate(payload.ids):
        step = db.get(ScenarioStep, step_id)
        if step and step.stage_id == stage_id:
            step.order_index = idx
    db.commit()


@router.get("/stages/{stage_id}/steps", response_model=list[schemas.ScenarioStepOut])
def admin_list_stage_steps(stage_id: int, db: Session = Depends(get_db)):
    stage = _must_get(db, ScenarioStage, stage_id, "Этап не найден")
    return [schemas.ScenarioStepOut.model_validate(item) for item in stage.steps]


@router.post("/stages/{stage_id}/steps", response_model=schemas.ScenarioStepOut, status_code=status.HTTP_201_CREATED)
def admin_create_step(stage_id: int, payload: schemas.ScenarioStepCreate, db: Session = Depends(get_db)):
    _must_get(db, ScenarioStage, stage_id, "Этап не найден")
    if payload.stage_id != stage_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="stage_id в payload не совпадает с URL")
    if payload.authority_id is not None:
        _must_get(db, Authority, payload.authority_id, "Организация не найдена")
    if payload.deadline_id is not None:
        _must_get(db, Deadline, payload.deadline_id, "Срок не найден")
    obj = create_entity(db, ScenarioStep, payload)
    return schemas.ScenarioStepOut.model_validate(obj)


@router.delete("/steps/{step_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_step(step_id: int, db: Session = Depends(get_db)):
    step = _must_get(db, ScenarioStep, step_id, "Шаг не найден")
    db.delete(step)
    db.commit()


@router.put("/steps/{step_id}", response_model=schemas.ScenarioStepOut)
def admin_update_step(step_id: int, payload: schemas.ScenarioStepUpdate, db: Session = Depends(get_db)):
    step = _must_get(db, ScenarioStep, step_id, "Шаг не найден")
    if payload.stage_id is not None:
        _must_get(db, ScenarioStage, payload.stage_id, "Этап не найден")
    if payload.authority_id is not None:
        _must_get(db, Authority, payload.authority_id, "Организация не найдена")
    if payload.deadline_id is not None:
        _must_get(db, Deadline, payload.deadline_id, "Срок не найден")
    obj = update_entity(db, step, payload)
    return schemas.ScenarioStepOut.model_validate(obj)


@router.get("/documents", response_model=list[schemas.DocumentOut])
def admin_list_documents(db: Session = Depends(get_db)):
    return [schemas.DocumentOut.model_validate(item) for item in list_documents_admin(db)]


@router.post("/documents", response_model=schemas.DocumentOut, status_code=status.HTTP_201_CREATED)
def admin_create_document(payload: schemas.DocumentCreate, db: Session = Depends(get_db)):
    obj = create_entity(db, Document, payload)
    return schemas.DocumentOut.model_validate(obj)


@router.put("/documents/{document_id}", response_model=schemas.DocumentOut)
def admin_update_document(document_id: int, payload: schemas.DocumentUpdate, db: Session = Depends(get_db)):
    document = _must_get(db, Document, document_id, "Документ не найден")
    obj = update_entity(db, document, payload)
    return schemas.DocumentOut.model_validate(obj)


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_document(document_id: int, db: Session = Depends(get_db)):
    document = _must_get(db, Document, document_id, "Документ не найден")
    db.delete(document)
    db.commit()


@router.post("/steps/{step_id}/documents/{document_id}", response_model=schemas.ScenarioStepOut)
def admin_attach_document(step_id: int, document_id: int, db: Session = Depends(get_db)):
    step = _must_get(db, ScenarioStep, step_id, "Шаг не найден")
    document = _must_get(db, Document, document_id, "Документ не найден")
    if document not in step.documents:
        step.documents.append(document)
        db.commit()
        db.refresh(step)
    return schemas.ScenarioStepOut.model_validate(step)


@router.delete("/steps/{step_id}/documents/{document_id}", response_model=schemas.ScenarioStepOut)
def admin_detach_document(step_id: int, document_id: int, db: Session = Depends(get_db)):
    step = _must_get(db, ScenarioStep, step_id, "Шаг не найден")
    document = _must_get(db, Document, document_id, "Документ не найден")
    if document in step.documents:
        step.documents.remove(document)
        db.commit()
        db.refresh(step)
    return schemas.ScenarioStepOut.model_validate(step)


@router.get("/authorities", response_model=list[schemas.AuthorityOut])
def admin_list_authorities(db: Session = Depends(get_db)):
    items = db.query(Authority).order_by(Authority.updated_at.desc()).all()
    return [schemas.AuthorityOut.model_validate(item) for item in items]


@router.post("/authorities", response_model=schemas.AuthorityOut, status_code=status.HTTP_201_CREATED)
def admin_create_authority(payload: schemas.AuthorityCreate, db: Session = Depends(get_db)):
    obj = create_entity(db, Authority, payload)
    return schemas.AuthorityOut.model_validate(obj)


@router.put("/authorities/{authority_id}", response_model=schemas.AuthorityOut)
def admin_update_authority(authority_id: int, payload: schemas.AuthorityUpdate, db: Session = Depends(get_db)):
    authority = _must_get(db, Authority, authority_id, "Организация не найдена")
    obj = update_entity(db, authority, payload)
    return schemas.AuthorityOut.model_validate(obj)


@router.delete("/authorities/{authority_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_authority(authority_id: int, db: Session = Depends(get_db)):
    authority = _must_get(db, Authority, authority_id, "Организация не найдена")
    db.delete(authority)
    db.commit()


@router.get("/deadlines", response_model=list[schemas.DeadlineOut])
def admin_list_deadlines(db: Session = Depends(get_db)):
    return [schemas.DeadlineOut.model_validate(item) for item in list_deadlines_admin(db)]


@router.post("/deadlines", response_model=schemas.DeadlineOut, status_code=status.HTTP_201_CREATED)
def admin_create_deadline(payload: schemas.DeadlineCreate, db: Session = Depends(get_db)):
    obj = create_entity(db, Deadline, payload)
    return schemas.DeadlineOut.model_validate(obj)


@router.put("/deadlines/{deadline_id}", response_model=schemas.DeadlineOut)
def admin_update_deadline(deadline_id: int, payload: schemas.DeadlineUpdate, db: Session = Depends(get_db)):
    deadline = _must_get(db, Deadline, deadline_id, "Срок не найден")
    obj = update_entity(db, deadline, payload)
    return schemas.DeadlineOut.model_validate(obj)


@router.post("/notification-rules", response_model=schemas.NotificationRuleOut, status_code=status.HTTP_201_CREATED)
def admin_create_notification_rule(payload: schemas.NotificationRuleCreate, db: Session = Depends(get_db)):
    _must_get(db, ScenarioStep, payload.step_id, "Шаг не найден")
    obj = create_entity(db, NotificationRule, payload)
    return schemas.NotificationRuleOut.model_validate(obj)


@router.put("/notification-rules/{rule_id}", response_model=schemas.NotificationRuleOut)
def admin_update_notification_rule(rule_id: int, payload: schemas.NotificationRuleUpdate, db: Session = Depends(get_db)):
    rule = _must_get(db, NotificationRule, rule_id, "Правило уведомления не найдено")
    obj = update_entity(db, rule, payload)
    return schemas.NotificationRuleOut.model_validate(obj)


@router.post("/dependencies", response_model=schemas.ScenarioDependencyOut, status_code=status.HTTP_201_CREATED)
def admin_create_dependency(payload: schemas.ScenarioDependencyCreate, db: Session = Depends(get_db)):
    _must_get(db, Scenario, payload.scenario_id, "Сценарий не найден")
    _must_get(db, ScenarioStep, payload.step_id, "Шаг не найден")
    _must_get(db, ScenarioStep, payload.depends_on_step_id, "Зависимый шаг не найден")
    obj = create_entity(db, ScenarioDependency, payload)
    return schemas.ScenarioDependencyOut.model_validate(obj)


@router.delete("/dependencies/{dependency_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_dependency(dependency_id: int, db: Session = Depends(get_db)):
    dep = _must_get(db, ScenarioDependency, dependency_id, "Зависимость не найдена")
    db.delete(dep)
    db.commit()


@router.delete("/related-scenarios/{related_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_related_scenario(related_id: int, db: Session = Depends(get_db)):
    obj = _must_get(db, RelatedScenario, related_id, "Связь не найдена")
    db.delete(obj)
    db.commit()


@router.post("/related-scenarios", response_model=schemas.RelatedScenarioOut, status_code=status.HTTP_201_CREATED)
def admin_create_related_scenario(payload: schemas.RelatedScenarioCreate, db: Session = Depends(get_db)):
    _must_get(db, Scenario, payload.scenario_id, "Сценарий не найден")
    related = _must_get(db, Scenario, payload.related_scenario_id, "Связанный сценарий не найден")
    obj = create_entity(db, RelatedScenario, payload)
    return schemas.RelatedScenarioOut(
        id=obj.id,
        scenario_id=obj.scenario_id,
        related_scenario_id=obj.related_scenario_id,
        relation_type=obj.relation_type,
        description=obj.description,
        related_scenario_title=related.title,
        related_scenario_slug=related.slug,
    )


@router.post("/source-references", response_model=schemas.SourceReferenceOut, status_code=status.HTTP_201_CREATED)
def admin_create_source_reference(payload: schemas.SourceReferenceCreate, db: Session = Depends(get_db)):
    obj = create_entity(db, SourceReference, payload)
    return schemas.SourceReferenceOut.model_validate(obj)


@router.delete("/source-references/{source_ref_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_source_reference(source_ref_id: int, db: Session = Depends(get_db)):
    ref = _must_get(db, SourceReference, source_ref_id, "Источник не найден")
    db.delete(ref)
    db.commit()


@router.get("/law-updates", response_model=list[schemas.LawUpdateOut])
def admin_list_law_updates(db: Session = Depends(get_db)):
    return [schemas.LawUpdateOut.model_validate(item) for item in list_law_updates_admin(db)]


@router.post("/law-updates", response_model=schemas.LawUpdateOut, status_code=status.HTTP_201_CREATED)
def admin_create_law_update(
    payload: schemas.LawUpdateCreate,
    db: Session = Depends(get_db),
    actor: str = Depends(get_current_user_email),
):
    if payload.affected_scenario_id is not None:
        _must_get(db, Scenario, payload.affected_scenario_id, "Сценарий не найден")
    if payload.affected_step_id is not None:
        _must_get(db, ScenarioStep, payload.affected_step_id, "Шаг не найден")
    obj = create_entity(db, LawUpdate, payload)
    log_audit_event(db, actor=actor, action=f"Создан закон-апдейт: «{obj.title}»", event_type="create")
    return schemas.LawUpdateOut.model_validate(obj)


@router.put("/law-updates/{law_update_id}", response_model=schemas.LawUpdateOut)
def admin_update_law_update(
    law_update_id: int,
    payload: schemas.LawUpdateUpdate,
    db: Session = Depends(get_db),
    actor: str = Depends(get_current_user_email),
):
    law_update = _must_get(db, LawUpdate, law_update_id, "Обновление законодательства не найдено")
    if payload.affected_scenario_id is not None:
        _must_get(db, Scenario, payload.affected_scenario_id, "Сценарий не найден")
    if payload.affected_step_id is not None:
        _must_get(db, ScenarioStep, payload.affected_step_id, "Шаг не найден")
    obj = update_entity(db, law_update, payload)
    log_audit_event(db, actor=actor, action=f"Изменён закон-апдейт: «{obj.title}»", event_type="update")
    return schemas.LawUpdateOut.model_validate(obj)


# ---------------------------------------------------------------------------
# H9 — Audit trail endpoint
# ---------------------------------------------------------------------------

@router.get("/audit-logs", response_model=list[schemas.AuditLogOut])
def admin_list_audit_logs(
    limit: int = Query(default=200, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """H9 — Список последних записей аудита (действия редакторов/админов)."""
    return [schemas.AuditLogOut.model_validate(item) for item in list_audit_logs(db, limit=limit)]


# ---------------------------------------------------------------------------
# I5 — Email delivery log endpoint
# ---------------------------------------------------------------------------

@router.get("/email-log", response_model=list[schemas.EmailNotificationOut])
def admin_email_log(
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """I5 — Журнал доставки email-уведомлений."""
    from backend.email_service import list_email_log
    return [schemas.EmailNotificationOut.model_validate(item) for item in list_email_log(db, limit=limit)]


@router.post("/email-queue/flush", status_code=status.HTTP_200_OK)
def admin_flush_email_queue(db: Session = Depends(get_db)):
    """I4 — Запустить отправку всех pending email из очереди (ручной триггер)."""
    from backend.email_service import send_pending_emails
    result = send_pending_emails(db)
    return result


@router.get("/audit-logs", response_model=list[schemas.AuditLogOut])
def admin_audit_logs(_: str = Depends(require_role("content_editor")), db: Session = Depends(get_db)):
    """H9 — Журнал действий (последние записи аудита)."""
    return [schemas.AuditLogOut.model_validate(x) for x in list_audit_logs(db)]


@router.get("/users", response_model=list[schemas.UserAdminOut])
def admin_users(_: str = Depends(require_role("platform_admin")), db: Session = Depends(get_db)):
    """H5 — Пользователи и роли."""
    users = db.scalars(select(User).order_by(User.id.asc())).all()
    return [
        schemas.UserAdminOut(
            id=u.id, email=u.email, name=u.name, role_id=u.role_id,
            is_active=u.is_active, city=u.city, region=u.region,
        )
        for u in users
    ]


# ---------------------------------------------------------------------------
# P7 — Каркас раздела «Экстремистский контент» (только структура, без данных)
# ---------------------------------------------------------------------------

def _validate_extremist_payload(
    category: str | None = None,
    status: str | None = None,
) -> None:
    if category is not None and category not in schemas.EXTREMIST_CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Недопустимая категория. Ожидается одна из: {', '.join(schemas.EXTREMIST_CATEGORIES)}.",
        )
    if status is not None and status not in schemas.EXTREMIST_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Недопустимый статус. Ожидается один из: {', '.join(schemas.EXTREMIST_STATUSES)}.",
        )


@router.get("/extremist-entries", response_model=list[schemas.ExtremistEntryOut])
def admin_list_extremist_entries(
    status_filter: str | None = Query(default=None, alias="status"),
    category_filter: str | None = Query(default=None, alias="category"),
    db: Session = Depends(get_db),
):
    """P7 — Список записей раздела. Доступен content_editor и platform_admin."""
    _validate_extremist_payload(category=category_filter, status=status_filter)
    stmt = select(ExtremistEntry).order_by(ExtremistEntry.updated_at.desc())
    if status_filter:
        stmt = stmt.where(ExtremistEntry.status == status_filter)
    if category_filter:
        stmt = stmt.where(ExtremistEntry.category == category_filter)
    items = db.scalars(stmt).all()
    return [schemas.ExtremistEntryOut.model_validate(item) for item in items]


@router.post(
    "/extremist-entries",
    response_model=schemas.ExtremistEntryOut,
    status_code=status.HTTP_201_CREATED,
)
def admin_create_extremist_entry(
    payload: schemas.ExtremistEntryCreate,
    db: Session = Depends(get_db),
    actor: str = Depends(get_current_user_email),
):
    """P7 — Создать запись. source_url обязателен (валидируется Pydantic HttpUrl)."""
    _validate_extremist_payload(category=payload.category, status=payload.status)
    obj = create_entity(db, ExtremistEntry, payload)
    log_audit_event(
        db,
        actor=actor,
        action=f"Создана запись экстремистского реестра: «{obj.title}»",
        event_type="create",
    )
    return schemas.ExtremistEntryOut.model_validate(obj)


@router.patch("/extremist-entries/{entry_id}", response_model=schemas.ExtremistEntryOut)
def admin_update_extremist_entry(
    entry_id: int,
    payload: schemas.ExtremistEntryUpdate,
    db: Session = Depends(get_db),
    actor: str = Depends(get_current_user_email),
):
    """P7 — Частичное обновление записи (можно править title, source_url, статус)."""
    entry = _must_get(db, ExtremistEntry, entry_id, "Запись не найдена")
    _validate_extremist_payload(category=payload.category, status=payload.status)
    obj = update_entity(db, entry, payload)
    log_audit_event(
        db,
        actor=actor,
        action=f"Изменена запись экстремистского реестра: «{obj.title}»",
        event_type="update",
    )
    return schemas.ExtremistEntryOut.model_validate(obj)


@router.delete("/extremist-entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_extremist_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    actor: str = Depends(get_current_user_email),
):
    """P7 — Удалить запись."""
    entry = _must_get(db, ExtremistEntry, entry_id, "Запись не найдена")
    title = entry.title
    db.delete(entry)
    db.commit()
    log_audit_event(
        db,
        actor=actor,
        action=f"Удалена запись экстремистского реестра: «{title}»",
        event_type="delete",
    )
