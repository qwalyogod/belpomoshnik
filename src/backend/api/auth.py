from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    create_access_token,
    create_refresh_token,
    get_token_payload,
    hash_password,
    verify_password,
)
from backend.database import get_db
from backend.models import RefreshToken, User
from backend.rate_limit import login_limiter

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
# Internal helpers
# ---------------------------------------------------------------------------

def _issue_tokens(db: Session, user: User) -> TokenResponse:
    access = create_access_token({"sub": user.email, "role": user.role_id})
    refresh = create_refresh_token({"sub": user.email})
    from datetime import timedelta
    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    db.add(RefreshToken(user_id=user.id, token=refresh, expires_at=expires_at))
    db.commit()
    return TokenResponse(access_token=access, refresh_token=refresh)


# ---------------------------------------------------------------------------
# Dependency: current user (H6 RBAC)
# ---------------------------------------------------------------------------

def get_current_user_email(token: str = Depends(oauth2_scheme)) -> str:
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
    """H6 — RBAC. Иерархия: citizen (0) < content_editor (1) < platform_admin (2)."""
    def _check(email: str = Depends(get_current_user_email), db: Session = Depends(get_db)) -> str:
        user = db.scalars(select(User).where(User.email == email)).first()
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Пользователь не найден или деактивирован.")
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
    """H2 — Регистрация: создаёт пользователя с bcrypt-паролем, возвращает JWT."""
    existing = db.scalars(select(User).where(User.email == payload.email)).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email уже зарегистрирован.")
    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        name=payload.name,
        role_id="citizen",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _issue_tokens(db, user)


@router.post("/login", response_model=TokenResponse)
def login(request: Request, form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """H2 — Авторизация: проверяет bcrypt-пароль, возвращает JWT. Rate-limited: 5 попыток / 5 мин."""
    client_key = f"{request.client.host}:{form.username}" if request.client else form.username
    if login_limiter.is_blocked(client_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Слишком много попыток входа. Повторите через 5 минут.",
            headers={"Retry-After": "300"},
        )
    user = db.scalars(select(User).where(User.email == form.username)).first()
    if not user or not user.is_active or not verify_password(form.password, user.hashed_password):
        login_limiter.record(client_key)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный email или пароль.")
    login_limiter.reset(client_key)
    user.last_login_at = datetime.now(timezone.utc)
    response = _issue_tokens(db, user)
    if user.role_id in {"content_editor", "platform_admin"}:
        from backend.service import log_audit_event

        log_audit_event(
            db,
            actor=user.email,
            actor_user_id=user.id,
            role_id=user.role_id,
            action="Вход в панель управления",
            event_type="login",
            entity_type="session",
            ip_address=request.client.host if request.client else "",
            user_agent=request.headers.get("user-agent", "")[:500],
        )
    return response


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(payload: RefreshRequest, db: Session = Depends(get_db)):
    """H3 — Обновить access-токен по refresh-токену. Старый токен отзывается (rotation)."""
    token_data = get_token_payload(payload.refresh_token)
    if not token_data or token_data.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Невалидный refresh-токен.")
    email = token_data.get("sub")
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Токен не содержит sub.")

    stored = db.scalars(select(RefreshToken).where(RefreshToken.token == payload.refresh_token)).first()
    if not stored or stored.revoked or stored.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh-токен недействителен или истёк.")

    user = db.scalars(select(User).where(User.email == email)).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Пользователь не найден.")

    stored.revoked = True
    db.commit()
    return _issue_tokens(db, user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: RefreshRequest, db: Session = Depends(get_db)):
    """H3 — Выход: отзывает refresh-токен в БД."""
    stored = db.scalars(select(RefreshToken).where(RefreshToken.token == payload.refresh_token)).first()
    if stored and not stored.revoked:
        stored.revoked = True
        db.commit()
    return None


@router.get("/me")
def get_me(email: str = Depends(get_current_user_email), db: Session = Depends(get_db)):
    """H3 — Текущий пользователь."""
    user = db.scalars(select(User).where(User.email == email)).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Пользователь не найден.")
    return {"id": user.id, "email": user.email, "name": user.name, "role": user.role_id}


@router.get("/test-accounts")
def list_test_accounts(db: Session = Depends(get_db)):
    """
    Список тестовых аккаунтов для UI-переключателя ролей.

    ВАЖНО: по умолчанию endpoint ВЫКЛЮЧЕН. Включается явно через
    BELPOMOSHNIK_ENABLE_TEST_SWITCHER=true в .env (или для тестов).
    Возвращает только пользователей с is_test_account=True. Обычные
    регистрации сюда не попадают.
    """
    import os as _os
    if _os.getenv("BELPOMOSHNIK_ENABLE_TEST_SWITCHER", "false").lower() != "true":
        return []
    users = db.scalars(
        select(User).where(User.is_test_account == True).order_by(User.id)  # noqa: E712
    ).all()
    return [
        {"email": u.email, "name": u.name, "role": u.role_id}
        for u in users
    ]
