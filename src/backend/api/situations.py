"""
G5/G7 — Личные ситуации, задачи и уведомления пользователя (реальная БД).

Все endpoint требуют JWT. Доступ только к своим объектам (owner-isolated).
ID генерируются на сервере (uuid4 hex).
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.api.user import get_current_user
from backend.database import get_db
from backend.models import User, UserNotification, UserSituation, UserSituationTask

router = APIRouter(prefix="/api/user", tags=["situations"])

_COMPLETED = {"Завершено", "Завершена"}


def _new_id() -> str:
    return uuid.uuid4().hex


def _recompute(situation: UserSituation) -> None:
    tasks = situation.tasks
    total = len(tasks)
    done = len([t for t in tasks if t.completed])
    progress = round(done / total * 100) if total else 0
    situation.progress = progress
    situation.status = "Не начата" if progress <= 0 else "Завершена" if progress >= 100 else "В процессе"


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class TaskIn(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    due_date: str = ""
    stage_title: str = ""
    order_index: int = 0


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    due_date: str | None = None
    stage_title: str | None = None
    completed: bool | None = None
    order_index: int | None = None


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    situation_id: str
    title: str
    completed: bool
    due_date: str
    stage_title: str
    order_index: int


class SituationIn(BaseModel):
    template_id: str = ""
    title: str = Field(min_length=1, max_length=255)
    category: str = ""
    tasks: list[TaskIn] = Field(default_factory=list)


class SituationUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    status: str | None = None
    category: str | None = None


class SituationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    template_id: str
    title: str
    status: str
    progress: int
    category: str
    tasks: list[TaskOut] = Field(default_factory=list)


class NotificationIn(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = ""
    notification_type: str = "task"
    source: str = ""
    due_date: str | None = None


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    description: str
    notification_type: str
    is_read: bool
    source: str
    due_date: str | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _owned_situation(db: Session, user: User, situation_id: str) -> UserSituation:
    sit = db.scalars(
        select(UserSituation).where(UserSituation.id == situation_id, UserSituation.user_id == user.id)
    ).first()
    if not sit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ситуация не найдена.")
    return sit


def _owned_task(db: Session, user: User, task_id: str) -> UserSituationTask:
    task = db.scalars(
        select(UserSituationTask)
        .join(UserSituation, UserSituationTask.situation_id == UserSituation.id)
        .where(UserSituationTask.id == task_id, UserSituation.user_id == user.id)
    ).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена.")
    return task


# ---------------------------------------------------------------------------
# G5 — Situations
# ---------------------------------------------------------------------------

@router.get("/situations", response_model=list[SituationOut])
def list_situations(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sits = db.scalars(
        select(UserSituation).where(UserSituation.user_id == user.id).order_by(UserSituation.created_at.desc())
    ).all()
    return [SituationOut.model_validate(s) for s in sits]


@router.post("/situations", response_model=SituationOut, status_code=status.HTTP_201_CREATED)
def create_situation(payload: SituationIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sit = UserSituation(
        id=_new_id(),
        user_id=user.id,
        template_id=payload.template_id,
        title=payload.title,
        category=payload.category,
        status="Не начата",
        progress=0,
    )
    db.add(sit)
    for idx, task in enumerate(payload.tasks):
        db.add(UserSituationTask(
            id=_new_id(),
            situation_id=sit.id,
            title=task.title,
            due_date=task.due_date,
            stage_title=task.stage_title,
            order_index=task.order_index or idx,
        ))
    db.flush()
    _recompute(sit)
    db.commit()
    db.refresh(sit)
    return SituationOut.model_validate(sit)


@router.get("/situations/{situation_id}", response_model=SituationOut)
def get_situation(situation_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return SituationOut.model_validate(_owned_situation(db, user, situation_id))


@router.put("/situations/{situation_id}", response_model=SituationOut)
def update_situation(
    situation_id: str,
    payload: SituationUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sit = _owned_situation(db, user, situation_id)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(sit, field, value)
    db.commit()
    db.refresh(sit)
    return SituationOut.model_validate(sit)


@router.delete("/situations/{situation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_situation(situation_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.delete(_owned_situation(db, user, situation_id))
    db.commit()


# ---------------------------------------------------------------------------
# G5 — Tasks
# ---------------------------------------------------------------------------

@router.post("/situations/{situation_id}/tasks", response_model=SituationOut, status_code=status.HTTP_201_CREATED)
def add_task(
    situation_id: str,
    payload: TaskIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sit = _owned_situation(db, user, situation_id)
    db.add(UserSituationTask(
        id=_new_id(),
        situation_id=sit.id,
        title=payload.title,
        due_date=payload.due_date,
        stage_title=payload.stage_title,
        order_index=payload.order_index or len(sit.tasks),
    ))
    db.flush()
    db.refresh(sit)
    _recompute(sit)
    db.commit()
    db.refresh(sit)
    return SituationOut.model_validate(sit)


@router.patch("/tasks/{task_id}", response_model=TaskOut)
def update_task(
    task_id: str,
    payload: TaskUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = _owned_task(db, user, task_id)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(task, field, value)
    db.flush()
    _recompute(task.situation)
    db.commit()
    db.refresh(task)
    return TaskOut.model_validate(task)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = _owned_task(db, user, task_id)
    situation = task.situation
    db.delete(task)
    db.flush()
    db.refresh(situation)
    _recompute(situation)
    db.commit()


# ---------------------------------------------------------------------------
# G7 — Notifications
# ---------------------------------------------------------------------------

@router.get("/notifications", response_model=list[NotificationOut])
def list_notifications(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = db.scalars(
        select(UserNotification).where(UserNotification.user_id == user.id).order_by(UserNotification.created_at.desc())
    ).all()
    return [NotificationOut.model_validate(n) for n in items]


@router.post("/notifications", response_model=NotificationOut, status_code=status.HTTP_201_CREATED)
def create_notification(payload: NotificationIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    n = UserNotification(id=_new_id(), user_id=user.id, **payload.model_dump())
    db.add(n)
    db.commit()
    db.refresh(n)
    return NotificationOut.model_validate(n)


@router.patch("/notifications/{notification_id}/read", response_model=NotificationOut)
def mark_read(notification_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    n = db.scalars(
        select(UserNotification).where(UserNotification.id == notification_id, UserNotification.user_id == user.id)
    ).first()
    if not n:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Уведомление не найдено.")
    n.is_read = True
    db.commit()
    db.refresh(n)
    return NotificationOut.model_validate(n)


@router.post("/notifications/read-all")
def mark_all_read(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = db.scalars(
        select(UserNotification).where(UserNotification.user_id == user.id, UserNotification.is_read == False)  # noqa: E712
    ).all()
    for n in items:
        n.is_read = True
    db.commit()
    return {"updated": len(items)}


@router.delete("/notifications/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification(notification_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    n = db.scalars(
        select(UserNotification).where(UserNotification.id == notification_id, UserNotification.user_id == user.id)
    ).first()
    if not n:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Уведомление не найдено.")
    db.delete(n)
    db.commit()
