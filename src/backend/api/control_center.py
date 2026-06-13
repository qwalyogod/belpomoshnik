from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import (
    Article,
    Authority,
    ControlCenterAuditLog,
    ControlCenterSession,
    ExtremistEntry,
    LawUpdate,
    Problem,
    Scenario,
    SystemSetting,
    User,
    UserNotification,
)
from backend.notifications.delivery import deliver_notification
from backend.notifications.native_push import is_native_push_ready
from backend.notifications.service import create_in_app_notification


router = APIRouter(prefix="/api/control-center", tags=["control-center"])
public_router = APIRouter(prefix="/api/public", tags=["system"])


DEFAULT_STATE: dict[str, Any] = {
    "maintenance": {
        "enabled": False,
        "level": "notice",
        "title": "Платформа работает в штатном режиме",
        "message": "",
        "until": "",
        "allowAdminAccess": True,
    },
    "readonly": {"enabled": False, "message": ""},
    "banner": {
        "enabled": False,
        "type": "info",
        "text": "",
        "linkLabel": "",
        "linkUrl": "",
        "dismissible": True,
        "audience": "all",
        "version": 1,
    },
    "featureFlags": {
        "documents": True,
        "situations": True,
        "assistant": True,
        "news": True,
        "finance": True,
        "profile": True,
        "editorPanel": True,
        "adminPanel": True,
        "notifications": True,
    },
    "branding": {
        "appName": "Белпомощник",
        "shortName": "Белпомощник",
        "logoText": "Б",
        "logoUrl": "",
        "accentColor": "#2563EB",
        "homeTitle": "Какая у вас ситуация?",
        "homeSubtitle": "Помогаем собрать документы, шаги и сроки в одном месте.",
    },
    "navigationLayout": {
        "desktop": ["home", "catalog", "situations", "documents", "finance", "news", "profile"],
        "tablet": ["home", "catalog", "situations", "documents", "news", "profile"],
        "mobile": ["home", "catalog", "assistant", "news", "profile"],
    },
}

SETTING_KEYS = {
    "maintenance": "maintenance_mode",
    "readonly": "readonly_mode",
    "banner": "system_banner",
    "featureFlags": "feature_flags",
    "branding": "branding",
    "navigationLayout": "navigation_layout",
}

_UNLOCK_ATTEMPTS: dict[str, dict[str, Any]] = {}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _request_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()[:64]
    return (request.client.host if request.client else "")[:64]


def _user_agent(request: Request) -> str:
    return request.headers.get("user-agent", "")[:500]


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _safe_json(raw: str, fallback: Any) -> Any:
    try:
        value = json.loads(raw or "")
        return value if value is not None else fallback
    except (TypeError, ValueError):
        return fallback


def _deep_merge(default: Any, value: Any) -> Any:
    if isinstance(default, dict) and isinstance(value, dict):
        merged = dict(default)
        for key, item in value.items():
            merged[key] = _deep_merge(default.get(key), item) if key in default else item
        return merged
    return value if value is not None else default


def _enabled() -> bool:
    return os.getenv("CONTROL_CENTER_ENABLED", "true").strip().lower() not in {"0", "false", "no", "off"}


def _ttl_minutes() -> int:
    try:
        return max(5, min(24 * 60, int(os.getenv("CONTROL_CENTER_TOKEN_TTL_MINUTES", "30"))))
    except ValueError:
        return 30


def _max_attempts() -> int:
    try:
        return max(1, min(50, int(os.getenv("CONTROL_CENTER_MAX_ATTEMPTS", "5"))))
    except ValueError:
        return 5


def _lock_minutes() -> int:
    try:
        return max(1, min(24 * 60, int(os.getenv("CONTROL_CENTER_LOCK_MINUTES", "15"))))
    except ValueError:
        return 15


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _hash_token(token: str) -> str:
    return _sha256(token)


def _password_valid(password: str) -> bool:
    configured_hash = os.getenv("CONTROL_CENTER_PASSWORD_HASH", "").strip()
    if configured_hash:
        expected = configured_hash.removeprefix("sha256:").strip()
        return hmac.compare_digest(_sha256(password), expected)
    expected_password = os.getenv("CONTROL_CENTER_PASSWORD", "x20b01")
    return hmac.compare_digest(password, expected_password)


def _check_enabled() -> None:
    if not _enabled():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Control Center is disabled")


def _attempt_state(ip: str) -> dict[str, Any]:
    item = _UNLOCK_ATTEMPTS.setdefault(ip, {"attempts": [], "locked_until": None})
    locked_until = item.get("locked_until")
    if isinstance(locked_until, datetime) and locked_until <= _utcnow():
        item["locked_until"] = None
        item["attempts"] = []
    return item


def _assert_not_locked(ip: str) -> None:
    item = _attempt_state(ip)
    locked_until = item.get("locked_until")
    if isinstance(locked_until, datetime) and locked_until > _utcnow():
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Слишком много попыток. Повторите позже.",
        )


def _record_failed_attempt(ip: str) -> None:
    item = _attempt_state(ip)
    now = _utcnow()
    cutoff = now - timedelta(minutes=_lock_minutes())
    item["attempts"] = [dt for dt in item.get("attempts", []) if isinstance(dt, datetime) and dt >= cutoff]
    item["attempts"].append(now)
    if len(item["attempts"]) >= _max_attempts():
        item["locked_until"] = now + timedelta(minutes=_lock_minutes())


def _reset_attempts(ip: str) -> None:
    _UNLOCK_ATTEMPTS.pop(ip, None)


def _audit(
    db: Session,
    *,
    request: Request,
    action: str,
    session_id: int | None = None,
    entity_type: str = "",
    entity_id: str = "",
    before: Any = None,
    after: Any = None,
    audit_status: str = "ok",
) -> None:
    db.add(
        ControlCenterAuditLog(
            session_id=session_id,
            action=action[:120],
            entity_type=entity_type[:80],
            entity_id=entity_id[:120],
            before_json=_json_dumps(before) if before is not None else "",
            after_json=_json_dumps(after) if after is not None else "",
            ip_address=_request_ip(request),
            user_agent=_user_agent(request),
            status=audit_status[:32],
        )
    )


def _setting_value(db: Session, logical_key: str) -> Any:
    storage_key = SETTING_KEYS[logical_key]
    default = DEFAULT_STATE[logical_key]
    row = db.scalars(select(SystemSetting).where(SystemSetting.key == storage_key)).first()
    if row is None:
        return default
    return _deep_merge(default, _safe_json(row.value_json, default))


def _set_setting(db: Session, logical_key: str, value: Any) -> tuple[Any, Any]:
    storage_key = SETTING_KEYS[logical_key]
    before = _setting_value(db, logical_key)
    next_value = _deep_merge(DEFAULT_STATE[logical_key], value)
    row = db.scalars(select(SystemSetting).where(SystemSetting.key == storage_key)).first()
    if row is None:
        row = SystemSetting(key=storage_key, value_json=_json_dumps(next_value))
        db.add(row)
    else:
        row.value_json = _json_dumps(next_value)
        row.updated_by = "control-center"
    db.flush()
    return before, next_value


def _system_state(db: Session) -> dict[str, Any]:
    return {logical: _setting_value(db, logical) for logical in SETTING_KEYS}


def _count(db: Session, model: Any, *conditions: Any) -> int:
    stmt = select(func.count()).select_from(model)
    for condition in conditions:
        stmt = stmt.where(condition)
    return int(db.scalar(stmt) or 0)


def _require_token(
    request: Request,
    db: Session = Depends(get_db),
    x_control_center_token: str = Header(default="", alias="X-Control-Center-Token"),
) -> ControlCenterSession:
    _check_enabled()
    token = x_control_center_token.strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Control token required")
    token_hash = _hash_token(token)
    session = db.scalars(select(ControlCenterSession).where(ControlCenterSession.token_hash == token_hash)).first()
    if session is None or session.revoked_at is not None or session.expires_at <= _utcnow():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Control token expired or revoked")
    session.last_used_at = _utcnow()
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


class UnlockRequest(BaseModel):
    password: str = Field(min_length=1, max_length=200)


class UnlockResponse(BaseModel):
    control_token: str
    expires_at: datetime
    ttl_minutes: int


class ControlStatus(BaseModel):
    backend_online: bool
    database_connected: bool
    total_users: int
    active_users: int
    blocked_users: int
    notifications_today: int
    publications_count: int
    problems_count: int
    scenarios_count: int
    authorities_count: int
    regions_count: int
    maintenance_mode: bool
    readonly_mode: bool
    banner_enabled: bool
    ai_status: str
    push_status: str
    scheduler_status: str
    frontend_version: str
    backend_version: str


class SystemStateResponse(BaseModel):
    maintenance: dict[str, Any]
    readonly: dict[str, Any]
    banner: dict[str, Any]
    featureFlags: dict[str, Any]
    branding: dict[str, Any]
    navigationLayout: dict[str, Any]


class MaintenanceUpdate(BaseModel):
    enabled: bool = False
    level: str = "notice"
    title: str = "Техническое обслуживание"
    message: str = ""
    until: str = ""
    allowAdminAccess: bool = True


class BannerUpdate(BaseModel):
    enabled: bool = False
    type: str = "info"
    text: str = ""
    linkLabel: str = ""
    linkUrl: str = ""
    dismissible: bool = True
    audience: str = "all"
    version: int = 1


class FeatureFlagsUpdate(BaseModel):
    flags: dict[str, bool]


class BrandingUpdate(BaseModel):
    appName: str = "Белпомощник"
    shortName: str = "Белпомощник"
    logoText: str = "Б"
    logoUrl: str = ""
    accentColor: str = "#2563EB"
    homeTitle: str = "Какая у вас ситуация?"
    homeSubtitle: str = "Помогаем собрать документы, шаги и сроки в одном месте."


class NavigationLayoutUpdate(BaseModel):
    desktop: list[str] = Field(default_factory=list)
    tablet: list[str] = Field(default_factory=list)
    mobile: list[str] = Field(default_factory=list)


class BroadcastNotificationRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = ""
    notification_type: str = "system"
    route: str = "/notifications"
    audience: str = "test_users"
    region: str = ""
    confirm_all_users: bool = False


class ReadonlyUpdate(BaseModel):
    enabled: bool = False
    message: str = ""


def _target_users(db: Session, payload: BroadcastNotificationRequest) -> list[User]:
    stmt = select(User).where(User.is_active == True)  # noqa: E712
    audience = payload.audience
    if audience == "all":
        if not payload.confirm_all_users:
            raise HTTPException(status_code=400, detail="Для отправки всем пользователям требуется confirm_all_users=true")
    elif audience == "test_users":
        stmt = stmt.where(User.is_test_account == True)  # noqa: E712
    elif audience == "citizens":
        stmt = stmt.where(User.role_id == "citizen")
    elif audience == "editors":
        stmt = stmt.where(User.role_id == "content_editor")
    elif audience == "admins":
        stmt = stmt.where(User.role_id == "platform_admin")
    elif audience == "region":
        region = payload.region.strip()
        if not region:
            raise HTTPException(status_code=400, detail="Для аудитории региона укажите region")
        stmt = stmt.where(User.region == region)
    else:
        raise HTTPException(status_code=400, detail="Неизвестная аудитория")
    return list(db.scalars(stmt.order_by(User.id.asc())).all())


@public_router.get("/system-state", response_model=SystemStateResponse)
def public_system_state(db: Session = Depends(get_db)):
    return _system_state(db)


@router.post("/unlock", response_model=UnlockResponse)
def unlock_control_center(payload: UnlockRequest, request: Request, db: Session = Depends(get_db)):
    _check_enabled()
    ip = _request_ip(request)
    _assert_not_locked(ip)
    if not _password_valid(payload.password):
        _record_failed_attempt(ip)
        _audit(db, request=request, action="unlock_failed", audit_status="denied")
        db.commit()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Неверный пароль")

    _reset_attempts(ip)
    ttl = _ttl_minutes()
    raw_token = secrets.token_urlsafe(32)
    expires_at = _utcnow() + timedelta(minutes=ttl)
    session = ControlCenterSession(
        token_hash=_hash_token(raw_token),
        expires_at=expires_at,
        ip_address=ip,
        user_agent=_user_agent(request),
    )
    db.add(session)
    db.flush()
    _audit(db, request=request, action="unlock", session_id=session.id, entity_type="control_session", entity_id=str(session.id))
    db.commit()
    return UnlockResponse(control_token=raw_token, expires_at=expires_at, ttl_minutes=ttl)


@router.post("/lock")
def lock_control_center(
    request: Request,
    session: ControlCenterSession = Depends(_require_token),
    db: Session = Depends(get_db),
):
    session.revoked_at = _utcnow()
    db.add(session)
    _audit(db, request=request, action="lock", session_id=session.id, entity_type="control_session", entity_id=str(session.id))
    db.commit()
    return {"ok": True}


@router.get("/status", response_model=ControlStatus)
def control_status(session: ControlCenterSession = Depends(_require_token), db: Session = Depends(get_db)):
    state = _system_state(db)
    today = _utcnow().date()
    today_start = datetime(today.year, today.month, today.day, tzinfo=timezone.utc)
    publications_count = (
        _count(db, Article, Article.status == "published")
        + _count(db, LawUpdate, LawUpdate.status == "published")
        + _count(db, ExtremistEntry, ExtremistEntry.status == "published")
    )
    regions_count = int(
        db.scalar(select(func.count(func.distinct(Authority.region))).where(Authority.region != "")) or 0
    )
    return ControlStatus(
        backend_online=True,
        database_connected=True,
        total_users=_count(db, User),
        active_users=_count(db, User, User.is_active == True),  # noqa: E712
        blocked_users=_count(db, User, User.is_active == False),  # noqa: E712
        notifications_today=_count(db, UserNotification, UserNotification.created_at >= today_start),
        publications_count=publications_count,
        problems_count=_count(db, Problem),
        scenarios_count=_count(db, Scenario),
        authorities_count=_count(db, Authority),
        regions_count=regions_count,
        maintenance_mode=bool(state["maintenance"].get("enabled")),
        readonly_mode=bool(state["readonly"].get("enabled")),
        banner_enabled=bool(state["banner"].get("enabled")),
        ai_status="configured" if os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY") else "local-rules",
        push_status="configured" if is_native_push_ready() else "credentials_not_configured",
        scheduler_status="running",
        frontend_version=os.getenv("BELPOMOSHNIK_FRONTEND_VERSION", "0.1.0"),
        backend_version=os.getenv("BELPOMOSHNIK_BACKEND_VERSION", "0.1.0"),
    )


@router.put("/maintenance", response_model=SystemStateResponse)
def update_maintenance(
    payload: MaintenanceUpdate,
    request: Request,
    session: ControlCenterSession = Depends(_require_token),
    db: Session = Depends(get_db),
):
    before, after = _set_setting(db, "maintenance", payload.model_dump())
    _audit(db, request=request, action="update_maintenance", session_id=session.id, entity_type="system_setting", entity_id="maintenance_mode", before=before, after=after)
    db.commit()
    return _system_state(db)


@router.put("/readonly", response_model=SystemStateResponse)
def update_readonly(
    payload: ReadonlyUpdate,
    request: Request,
    session: ControlCenterSession = Depends(_require_token),
    db: Session = Depends(get_db),
):
    before, after = _set_setting(db, "readonly", payload.model_dump())
    _audit(db, request=request, action="update_readonly", session_id=session.id, entity_type="system_setting", entity_id="readonly_mode", before=before, after=after)
    db.commit()
    return _system_state(db)


@router.put("/banner", response_model=SystemStateResponse)
def update_banner(
    payload: BannerUpdate,
    request: Request,
    session: ControlCenterSession = Depends(_require_token),
    db: Session = Depends(get_db),
):
    before, after = _set_setting(db, "banner", payload.model_dump())
    _audit(db, request=request, action="update_banner", session_id=session.id, entity_type="system_setting", entity_id="system_banner", before=before, after=after)
    db.commit()
    return _system_state(db)


@router.put("/feature-flags", response_model=SystemStateResponse)
def update_feature_flags(
    payload: FeatureFlagsUpdate,
    request: Request,
    session: ControlCenterSession = Depends(_require_token),
    db: Session = Depends(get_db),
):
    before, after = _set_setting(db, "featureFlags", payload.flags)
    _audit(db, request=request, action="update_feature_flags", session_id=session.id, entity_type="system_setting", entity_id="feature_flags", before=before, after=after)
    db.commit()
    return _system_state(db)


@router.put("/branding", response_model=SystemStateResponse)
def update_branding(
    payload: BrandingUpdate,
    request: Request,
    session: ControlCenterSession = Depends(_require_token),
    db: Session = Depends(get_db),
):
    before, after = _set_setting(db, "branding", payload.model_dump())
    _audit(db, request=request, action="update_branding", session_id=session.id, entity_type="system_setting", entity_id="branding", before=before, after=after)
    db.commit()
    return _system_state(db)


@router.put("/navigation-layout", response_model=SystemStateResponse)
def update_navigation_layout(
    payload: NavigationLayoutUpdate,
    request: Request,
    session: ControlCenterSession = Depends(_require_token),
    db: Session = Depends(get_db),
):
    before, after = _set_setting(db, "navigationLayout", payload.model_dump())
    _audit(db, request=request, action="update_navigation_layout", session_id=session.id, entity_type="system_setting", entity_id="navigation_layout", before=before, after=after)
    db.commit()
    return _system_state(db)


@router.post("/broadcast-notification")
def broadcast_notification(
    payload: BroadcastNotificationRequest,
    request: Request,
    session: ControlCenterSession = Depends(_require_token),
    db: Session = Depends(get_db),
):
    users = _target_users(db, payload)
    created = 0
    delivered = 0
    for user in users:
        notification, is_created = create_in_app_notification(
            db,
            user_id=user.id,
            title=payload.title,
            description=payload.description,
            notification_type=payload.notification_type,
            source="Control Center",
            route=payload.route or "/notifications",
            dedupe_key="",
        )
        if is_created:
            created += 1
        result = deliver_notification(db, notification)
        if result.get("system_delivered"):
            delivered += 1
    _audit(
        db,
        request=request,
        action="broadcast_notification",
        session_id=session.id,
        entity_type="user_notification",
        after={"audience": payload.audience, "region": payload.region, "targeted": len(users), "created": created},
    )
    db.commit()
    return {"targeted": len(users), "created": created, "delivered": delivered}


@router.post("/service-actions/{action}")
def run_service_action(
    action: str,
    request: Request,
    session: ControlCenterSession = Depends(_require_token),
    db: Session = Depends(get_db),
):
    result: dict[str, Any]
    if action == "create-test-notifications":
        users = list(db.scalars(select(User).where(User.is_test_account == True, User.is_active == True)).all())  # noqa: E712
        created = 0
        for user in users:
            _, is_created = create_in_app_notification(
                db,
                user_id=user.id,
                title="Проверочное уведомление",
                description="Системная проверка центра управления платформой.",
                notification_type="system",
                source="Control Center",
                route="/notifications",
                dedupe_key=f"control-center-test-{user.id}",
            )
            if is_created:
                created += 1
        result = {"ok": True, "created": created, "targeted": len(users)}
    elif action == "reset-transient-system-state":
        before = _system_state(db)
        _set_setting(db, "maintenance", DEFAULT_STATE["maintenance"])
        _set_setting(db, "readonly", DEFAULT_STATE["readonly"])
        _set_setting(db, "banner", DEFAULT_STATE["banner"])
        result = {"ok": True, "reset": ["maintenance", "readonly", "banner"], "before": before}
    elif action == "prepare-presentation-state":
        _, banner = _set_setting(
            db,
            "banner",
            {
                **DEFAULT_STATE["banner"],
                "enabled": True,
                "type": "info",
                "text": "Белпомощник работает в штатном режиме. Основные разделы готовы к показу.",
                "version": int(_utcnow().timestamp()),
            },
        )
        result = {"ok": True, "banner": banner}
    else:
        raise HTTPException(status_code=404, detail="Неизвестное системное действие")

    _audit(db, request=request, action=f"service_action:{action}", session_id=session.id, after=result)
    db.commit()
    return result


@router.get("/audit-log")
def control_audit_log(
    session: ControlCenterSession = Depends(_require_token),
    db: Session = Depends(get_db),
    limit: int = 80,
):
    rows = db.scalars(
        select(ControlCenterAuditLog)
        .order_by(ControlCenterAuditLog.created_at.desc())
        .limit(max(1, min(limit, 200)))
    ).all()
    return [
        {
            "id": row.id,
            "session_id": row.session_id,
            "action": row.action,
            "entity_type": row.entity_type,
            "entity_id": row.entity_id,
            "status": row.status,
            "ip_address": row.ip_address,
            "created_at": row.created_at,
        }
        for row in rows
    ]
