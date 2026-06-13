"""K-этап — публикации (редакторские + UGC) и модерация.

Local-first на фронте, здесь серверный источник правды. RBAC:
- любой вошедший пользователь может создать предложение (UGC);
- content_editor+ управляет и модерирует;
- platform_admin блокирует отправителей.
"""

from __future__ import annotations

import json
import os
import re
import uuid
from datetime import date, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend import schemas
from backend.api.auth import get_current_user_email, require_role
from backend.config import get_upload_dir
from backend.database import get_db
from backend.models import Article, ArticleViewDaily, BlockedSubmitter, ContentTag, User


# ─────────────────────────────────────────────────────────────────────────────
# Санитизация body_html (минимум, без внешних зависимостей)
# Полноценный sanitize требует bleach/DOMPurify — TODO для production.
# Здесь убираем только самые опасные теги/атрибуты.
# ─────────────────────────────────────────────────────────────────────────────
_DANGEROUS_TAGS = re.compile(
    r"<\s*(?:script|iframe|object|embed|svg|math|style|link|meta|base|form|frame|frameset)\b",
    re.IGNORECASE,
)
_DANGEROUS_ON_ATTRS = re.compile(r"""\s+on[a-z]+\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+)""", re.IGNORECASE)
_JS_HREF = re.compile(r"""\s+(?:href|src|xlink:href)\s*=\s*(?:"\s*javascript:[^"]*"|'\s*javascript:[^']*'|javascript:[^\s>]+)""", re.IGNORECASE)


def sanitize_html(value: str | None) -> str | None:
    """Вырезает опасные теги и атрибуты из пользовательского HTML.

    Не пытаемся быть полноценным sanitizer'ом — только блокируем самые
    распространённые XSS-векторы. Для production → bleach (см. PROJECT_STATUS).
    """
    if not value:
        return value
    s = _DANGEROUS_TAGS.sub("<span data-belp-stripped", value)
    s = _DANGEROUS_ON_ATTRS.sub(" data-belp-attr-stripped=", s)
    s = _JS_HREF.sub(' data-belp-href-stripped="#"', s)
    return s

router = APIRouter(prefix="/api/articles", tags=["articles"])

UPLOAD_DIR = Path(get_upload_dir())
_MAX_UPLOAD = 15 * 1024 * 1024  # 15 MB
_ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".mp4", ".webm", ".ogg", ".pdf"}

_STAFF_ROLES = {"content_editor", "platform_admin"}
_VALID_STATUS = {"draft", "review", "published", "rejected"}
_VALID_KIND = {"news", "scenario", "problem"}


def _user(db: Session, email: str) -> User:
    user = db.scalars(select(User).where(User.email == email)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден.")
    return user


def _is_blocked(db: Session, user_id: int) -> bool:
    return db.get(BlockedSubmitter, user_id) is not None


def _json_list(raw: str) -> list[str]:
    try:
        value = json.loads(raw or "[]")
        return [str(x) for x in value] if isinstance(value, list) else []
    except (ValueError, TypeError):
        return []


def _normalize_article_tags(db: Session, tags: list[str]) -> list[str]:
    requested = []
    seen = set()
    for item in tags:
        tag = str(item).strip()
        key = tag.lower()
        if tag and key not in seen:
            requested.append(tag)
            seen.add(key)
    if not requested:
        return []

    allowed = {
        row.name.lower(): row.name
        for row in db.scalars(select(ContentTag).where(ContentTag.is_active.is_(True))).all()
    }
    unknown = [tag for tag in requested if tag.lower() not in allowed]
    if unknown:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Недоступные теги: {', '.join(unknown)}",
        )
    return [allowed[tag.lower()] for tag in requested]


def _to_out(a: Article) -> schemas.ArticleOut:
    return schemas.ArticleOut(
        id=a.id,
        kind=a.kind,
        title=a.title,
        summary=a.summary,
        body_html=a.body_html,
        cover=a.cover,
        video=a.video,
        gallery=_json_list(a.gallery),
        tags=_json_list(a.tags),
        category=a.category,
        specialization=a.specialization,
        audience=a.audience,
        source=a.source,
        source_url=a.source_url,
        status=a.status,
        author=schemas.ArticleAuthorOut(
            name=a.author_name,
            role=a.author_role,
            proposed_by=a.proposed_by,
            proposer_id=a.proposer_id,
            anonymous=a.anonymous,
        ),
        reported=a.reported,
        date=a.publish_date,
        views=a.views,
        updated_at=a.updated_at,
    )


def _must_get(db: Session, article_id: int) -> Article:
    article = db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Публикация не найдена.")
    return article


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

@router.get("", response_model=list[schemas.ArticleOut])
def list_published(kind: str | None = None, db: Session = Depends(get_db)):
    """Публичная лента: только опубликованные материалы (для читателей)."""
    stmt = select(Article).where(Article.status == "published")
    if kind in _VALID_KIND:
        stmt = stmt.where(Article.kind == kind)
    stmt = stmt.order_by(Article.updated_at.desc())
    return [_to_out(a) for a in db.scalars(stmt).all()]


@router.get("/all", response_model=list[schemas.ArticleOut])
def list_all(_: str = Depends(require_role("content_editor")), db: Session = Depends(get_db)):
    """Все публикации (Публикации + Модерация) — только для редакции."""
    stmt = select(Article).order_by(Article.updated_at.desc())
    return [_to_out(a) for a in db.scalars(stmt).all()]


@router.get("/mine", response_model=list[schemas.ArticleOut])
def list_mine(email: str = Depends(get_current_user_email), db: Session = Depends(get_db)):
    """Свои предложения текущего пользователя («Мои предложения»)."""
    me = _user(db, email)
    stmt = select(Article).where(Article.proposer_id == me.id).order_by(Article.updated_at.desc())
    return [_to_out(a) for a in db.scalars(stmt).all()]


@router.get("/blocked", response_model=list[int])
def list_blocked(_: str = Depends(require_role("content_editor")), db: Session = Depends(get_db)):
    return [row.user_id for row in db.scalars(select(BlockedSubmitter)).all()]


@router.post("/upload")
def upload_media(file: UploadFile = File(...), _: str = Depends(get_current_user_email)):
    """Загрузка обложки / видео / фото на сервер (вместо локального object URL)."""
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in _ALLOWED_EXT:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Недопустимый тип файла.")
    data = file.file.read()
    if len(data) > _MAX_UPLOAD:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Файл больше 15 МБ.")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}{ext}"
    (UPLOAD_DIR / name).write_bytes(data)
    return {"url": f"/uploads/{name}"}


@router.get("/views/daily")
def daily_views(days: int = 7, db: Session = Depends(get_db)):
    """Просмотры по дням за последние N дней (для графика дашборда)."""
    days = max(1, min(days, 90))
    rows = {r.day: r.count for r in db.scalars(select(ArticleViewDaily)).all()}
    today = date.today()
    return [
        {"date": (today - timedelta(days=i)).isoformat(), "count": rows.get((today - timedelta(days=i)).isoformat(), 0)}
        for i in range(days - 1, -1, -1)
    ]


@router.post("/{article_id}/view")
def register_view(article_id: int, db: Session = Depends(get_db)):
    """Публичный счётчик просмотров: +1 при открытии материала читателем."""
    article = _must_get(db, article_id)
    article.views = (article.views or 0) + 1
    today = date.today().isoformat()
    row = db.get(ArticleViewDaily, today)
    if row:
        row.count += 1
    else:
        db.add(ArticleViewDaily(day=today, count=1))
    db.commit()
    return {"id": article.id, "views": article.views}


# ---------------------------------------------------------------------------
# Write
# ---------------------------------------------------------------------------

@router.post("", response_model=schemas.ArticleOut, status_code=status.HTTP_201_CREATED)
def create_article(payload: schemas.ArticleCreate, email: str = Depends(get_current_user_email), db: Session = Depends(get_db)):
    me = _user(db, email)
    is_staff = me.role_id in _STAFF_ROLES
    proposal = payload.as_proposal or not is_staff

    if proposal and _is_blocked(db, me.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Отправка предложений ограничена администрацией.")

    kind = payload.kind if payload.kind in _VALID_KIND else "news"
    requested = payload.status if payload.status in _VALID_STATUS else "draft"
    # Граждане не могут публиковать напрямую — только черновик или на модерацию.
    if proposal:
        status_value = "draft" if requested == "draft" else "review"
    else:
        status_value = requested

    normalized_tags = _normalize_article_tags(db, payload.tags)

    article = Article(
        kind=kind,
        title=payload.title.strip(),
        summary=payload.summary,
        body_html=sanitize_html(payload.body_html),
        cover=payload.cover,
        video=payload.video,
        gallery=json.dumps(payload.gallery, ensure_ascii=False),
        tags=json.dumps(normalized_tags, ensure_ascii=False),
        category=payload.category,
        specialization=payload.specialization,
        audience=payload.audience,
        source=payload.source,
        source_url=payload.source_url,
        status=status_value,
        publish_date=payload.date or date.today().isoformat(),
        anonymous=bool(payload.anonymous) if proposal else False,
    )
    if proposal:
        article.author_role = "citizen"
        article.author_name = ""
        article.proposed_by = me.name or "Пользователь"
        article.proposer_id = me.id
    else:
        article.author_role = me.role_id
        article.author_name = me.name or "Редакция"

    db.add(article)
    db.commit()
    db.refresh(article)
    return _to_out(article)


@router.put("/{article_id}", response_model=schemas.ArticleOut)
def update_article(article_id: int, payload: schemas.ArticleUpdate, email: str = Depends(get_current_user_email), db: Session = Depends(get_db)):
    me = _user(db, email)
    article = _must_get(db, article_id)
    is_staff = me.role_id in _STAFF_ROLES

    if not is_staff:
        # Гражданин правит только свой черновик/заявку.
        if article.proposer_id != me.id or article.status not in {"draft", "review"}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Можно редактировать только свои черновики и заявки.")

    data = payload.model_dump(exclude_unset=True)
    if "date" in data:
        article.publish_date = data.pop("date") or article.publish_date
    if "gallery" in data and data["gallery"] is not None:
        article.gallery = json.dumps(data.pop("gallery"), ensure_ascii=False)
    if "tags" in data and data["tags"] is not None:
        article.tags = json.dumps(_normalize_article_tags(db, data.pop("tags")), ensure_ascii=False)
    if "status" in data:
        new_status = data.pop("status")
        if new_status in _VALID_STATUS:
            if not is_staff and new_status not in {"draft", "review"}:
                new_status = "review"
            article.status = new_status
    if "kind" in data:
        kind = data.pop("kind")
        if kind in _VALID_KIND:
            article.kind = kind
    for key, value in data.items():
        if value is None or not hasattr(article, key):
            continue
        if key == "body_html":
            setattr(article, key, sanitize_html(value))
        else:
            setattr(article, key, value)

    # Редактор доработал предложение пользователя → «при поддержке {редактор}».
    if is_staff and article.proposed_by:
        article.author_name = me.name or "Редакция"

    db.commit()
    db.refresh(article)
    return _to_out(article)


@router.post("/{article_id}/moderate", response_model=schemas.ArticleOut)
def moderate_article(article_id: int, payload: schemas.ArticleModerate, email: str = Depends(require_role("content_editor")), db: Session = Depends(get_db)):
    me = _user(db, email)
    article = _must_get(db, article_id)
    action = payload.action
    if action == "publish":
        article.status = "published"
        article.reported = False
        if article.proposed_by:
            article.author_name = me.name or "Редакция"
    elif action == "reject":
        article.status = "rejected"
    elif action == "report":
        article.reported = True
    elif action == "unreport":
        article.reported = False
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Неизвестное действие модерации.")
    db.commit()
    db.refresh(article)
    return _to_out(article)


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_article(article_id: int, _: str = Depends(require_role("content_editor")), db: Session = Depends(get_db)):
    article = _must_get(db, article_id)
    db.delete(article)
    db.commit()


@router.post("/blocked/{user_id}", response_model=list[int])
def toggle_block(user_id: int, email: str = Depends(require_role("platform_admin")), db: Session = Depends(get_db)):
    """Заблокировать / разблокировать пользователю право предлагать контент."""
    existing = db.get(BlockedSubmitter, user_id)
    if existing:
        db.delete(existing)
    else:
        db.add(BlockedSubmitter(user_id=user_id, blocked_by=email))
    db.commit()
    return [row.user_id for row in db.scalars(select(BlockedSubmitter)).all()]
