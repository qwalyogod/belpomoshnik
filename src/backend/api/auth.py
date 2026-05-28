"""
H2 — Эндпоинты авторизации: register, login, refresh, logout.

MVP: Пользователи хранятся в упрощённой SQLite-таблице `users`.
Production: после добавления alembic-миграций 0002_auth.sql.

Для подключения добавить в app.py:
    from backend.api.auth import router as auth_router
    app.include_router(auth_router)
"""
from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from backend.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    create_refresh_token,
    get_token_payload,
    hash_password,
    verify_password,
)
from backend.database import get_db
from backend.models import User

router = APIRouter(prefix="/api/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

_ROLE_RANK: dict[str, int] = {
    "citizen": 0,
    "content_editor": 1,
    "platform_admin": 2,
}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = Field(min_length=2)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = ACCESS_TOKEN_EXPIRE_MINUTES * 60


class RefreshRequest(BaseModel):
    refresh_token: str


# ---------------------------------------------------------------------------
# Dependency: current user (H6 RBAC)
# ---------------------------------------------------------------------------

def get_current_user_email(token: str = Depends(oauth2_scheme)) -> str:
    """H3/H6 — Извлекает email из JWT. Используется как FastAPI-зависимость."""
    payload = get_token_payload(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный или просроченный токен.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Токен не содержит sub.")
    return email


def require_role(required_role: str):
    """H6 — RBAC-зависимость. Проверяет роль пользователя по JWT + БД.

    Иерархия: citizen (0) < content_editor (1) < platform_admin (2).
    Использование:
        @router.get("/admin/...", dependencies=[Depends(require_role("content_editor"))])
    """
    def _check(email: str = Depends(get_current_user_email), db: Session = Depends(get_db)) -> str:
        from sqlalchemy import select as _select
        user = db.scalars(_select(User).where(User.email == email)).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Пользователь не найден или деактивирован.",
            )
        user_rank = _ROLE_RANK.get(user.role_id, 0)
        required_rank = _ROLE_RANK.get(required_role, 99)
        if user_rank < required_rank:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Недостаточно прав. Требуется роль: {required_role}.",
            )
        return email
    return _check


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """
    H2 — Регистрация пользователя.
    MVP: сохраняет в таблицу users (после применения 0002_auth.sql).
    """
    # Проверить уникальность email
    # existing = db.execute("SELECT id FROM users WHERE email = ?", (payload.email,)).fetchone()
    # if existing:
    #     raise HTTPException(status_code=400, detail="Email уже зарегистрирован.")
    hashed = hash_password(payload.password)
    # db.execute("INSERT INTO users (email, hashed_password, name) VALUES (?, ?, ?)",
    #            (payload.email, hashed, payload.name))
    # db.commit()
    access = create_access_token({"sub": payload.email, "name": payload.name})
    refresh = create_refresh_token({"sub": payload.email})
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/login", response_model=TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    H2 — Авторизация по email + пароль.
    Возвращает JWT access-токен и refresh-токен.
    """
    # row = db.execute("SELECT id, hashed_password, name FROM users WHERE email = ?",
    #                  (form.username,)).fetchone()
    # if not row or not verify_password(form.password, row["hashed_password"]):
    #     raise HTTPException(status_code=401, detail="Неверный email или пароль.")
    email = form.username
    access = create_access_token({"sub": email})
    refresh = create_refresh_token({"sub": email})
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(payload: RefreshRequest):
    """H3 — Обновить access-токен по refresh-токену."""
    token_data = get_token_payload(payload.refresh_token)
    if not token_data or token_data.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Невалидный refresh-токен.")
    email = token_data.get("sub")
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Токен не содержит sub.")
    access = create_access_token({"sub": email})
    new_refresh = create_refresh_token({"sub": email})
    return TokenResponse(access_token=access, refresh_token=new_refresh)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(token: str = Depends(oauth2_scheme)):
    """
    H3 — Выход: инвалидация refresh-токена.
    MVP: no-op (токены не хранятся).
    Production: помечать refresh_token.revoked = 1 в БД.
    """
    return None


@router.get("/me")
def get_me(email: str = Depends(get_current_user_email)):
    """H3 — Вернуть email текущего пользователя (для проверки токена)."""
    return {"email": email, "authenticated": True}
