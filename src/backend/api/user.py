"""
G3/H7 — User profile + personal document endpoints.

MVP: заглушки с auth-зависимостями (JWT уже работает после Этапа H).
Production: раскомментировать DB-запросы и убрать stub-ответы.

Подключить в app.py:
    from backend.api.user import router as user_router
    app.include_router(user_router)
"""
import os

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any
from sqlalchemy.orm import Session

from backend.api.auth import get_current_user_email
from backend.database import get_db

USER_DOCS_DIR: str = os.getenv("BELPOMOSHNIK_DOCS_DIR", "data/user_docs")
"""H7 — Папка с загружаемыми файлами документов пользователей.
В production: вынести за webroot или использовать S3/MinIO.
Доступ только через аутентифицированный endpoint (не через статику nginx).
"""

router = APIRouter(prefix="/api/user", tags=["user"])


class UserProfileOut(BaseModel):
    """G3 — Профиль пользователя."""
    id: int
    email: str
    name: str
    city: str = ""
    region: str = ""
    district: str = ""
    address: str = ""
    employment_status: str = ""
    has_children: bool = False
    owns_property: bool = False
    has_car: bool = False
    is_renter: bool = False
    interest_tags: list[str] = Field(default_factory=list)
    created_at: datetime


class UserProfileUpdate(BaseModel):
    name: str | None = None
    city: str | None = None
    region: str | None = None
    district: str | None = None
    address: str | None = None
    employment_status: str | None = None
    has_children: bool | None = None
    owns_property: bool | None = None
    has_car: bool | None = None
    is_renter: bool | None = None
    interest_tags: list[str] | None = None


class UserSettingsUpdate(BaseModel):
    dark_theme: bool | None = None
    email_notifications: bool | None = None
    doc_reminder_days: int | None = None
    learning_mode: bool | None = None


# ---------------------------------------------------------------------------
# Заглушки — раскомментировать и подключить к БД после Этапа H (JWT/auth)
# ---------------------------------------------------------------------------

# @router.get("/profile", response_model=UserProfileOut)
# def get_profile(current_user=Depends(get_current_user)):
#     """G3 — Получить профиль текущего пользователя."""
#     return UserProfileOut.model_validate(current_user)


# @router.put("/profile", response_model=UserProfileOut)
# def update_profile(payload: UserProfileUpdate, current_user=Depends(get_current_user), db=Depends(get_db)):
#     """G3 — Обновить профиль пользователя."""
#     for field, value in payload.model_dump(exclude_none=True).items():
#         setattr(current_user, field, value)
#     db.commit()
#     db.refresh(current_user)
#     return UserProfileOut.model_validate(current_user)


# @router.patch("/settings")
# def update_settings(payload: UserSettingsUpdate, current_user=Depends(get_current_user), db=Depends(get_db)):
#     """G3 — Обновить настройки пользователя."""
#     settings = current_user.settings or {}
#     settings.update(payload.model_dump(exclude_none=True))
#     current_user.settings = settings
#     db.commit()
#     return {"ok": True}


# ---------------------------------------------------------------------------
# G5 — Ситуации и задачи (stub)
# ---------------------------------------------------------------------------

# @router.get("/situations")
# def list_situations(current_user=Depends(get_current_user), db=Depends(get_db)):
#     """G5 — Список личных ситуаций пользователя."""
#     ...


# @router.post("/situations", status_code=201)
# def create_situation(template_id: str, current_user=Depends(get_current_user), db=Depends(get_db)):
#     """G5 — Создать ситуацию из шаблона сценария."""
#     ...


# @router.patch("/tasks/{task_id}/complete")
# def complete_task(task_id: str, current_user=Depends(get_current_user), db=Depends(get_db)):
#     """G5 — Отметить задачу выполненной."""
#     ...


# ---------------------------------------------------------------------------
# G6 / H7 — Личные документы
# ---------------------------------------------------------------------------

# @router.get("/documents")
# def list_user_documents(email: str = Depends(get_current_user_email), db: Session = Depends(get_db)):
#     """G6 — Список личных документов пользователя."""
#     ...


# @router.post("/documents", status_code=201)
# def create_user_document(payload: dict, email: str = Depends(get_current_user_email), db: Session = Depends(get_db)):
#     """G6 — Добавить личный документ."""
#     ...


@router.get("/documents/{doc_id}/file")
def get_document_file(
    doc_id: int,
    email: str = Depends(get_current_user_email),
    db: Session = Depends(get_db),
):
    """
    H7 — Скачать файл личного документа.

    Доступ только владельцу: сначала проверяем user_id, потом отдаём файл.
    MVP: endpoint активен, но возвращает 404 (файлов нет до G6 production).
    Production: заменить stub на поиск в user_documents + FileResponse.
    """
    # Production:
    # from sqlalchemy import select as _sel
    # from backend.models import User, UserDocument
    # user = db.scalars(_sel(User).where(User.email == email)).first()
    # if not user:
    #     raise HTTPException(status_code=403, detail="Пользователь не найден.")
    # doc = db.scalars(_sel(UserDocument).where(UserDocument.id == doc_id, UserDocument.user_id == user.id)).first()
    # if not doc:
    #     raise HTTPException(status_code=404, detail="Документ не найден.")
    # path = os.path.join(USER_DOCS_DIR, str(user.id), f"{doc_id}")
    # if not os.path.exists(path):
    #     raise HTTPException(status_code=404, detail="Файл не найден.")
    # return FileResponse(path, media_type="application/octet-stream")
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Файлы документов недоступны в MVP.")


# ---------------------------------------------------------------------------
# G7 — Уведомления (stub)
# ---------------------------------------------------------------------------

# @router.get("/notifications")
# def list_notifications(current_user=Depends(get_current_user), db=Depends(get_db)):
#     """G7 — Список уведомлений пользователя."""
#     ...


# @router.patch("/notifications/{notification_id}/read")
# def mark_notification_read(notification_id: str, current_user=Depends(get_current_user), db=Depends(get_db)):
#     """G7 — Отметить уведомление прочитанным."""
#     ...
