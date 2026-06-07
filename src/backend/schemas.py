from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from backend.enums import (
    ActionType,
    ContentStatus,
    DifficultyLevel,
    DurationUnit,
    LawUpdateStatus,
    NotificationType,
    RelationType,
    SourceType,
)

# v1.1 (P4): пользовательские заметки. Категории — фиксированный набор,
# синхронизирован с NOTE_CATEGORIES на фронте (types.ts).
USER_NOTE_CATEGORIES: tuple[str, ...] = ("Общее", "Документы", "Семья", "Здоровье")


class ProblemBase(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    slug: str = Field(min_length=2, max_length=255)
    short_description: str = Field(default="", max_length=500)
    description: str = ""
    icon: str = ""
    category: str = ""
    status: ContentStatus = ContentStatus.DRAFT


class ProblemCreate(ProblemBase):
    pass


class ProblemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=255)
    slug: str | None = Field(default=None, min_length=2, max_length=255)
    short_description: str | None = Field(default=None, max_length=500)
    description: str | None = None
    icon: str | None = None
    category: str | None = None
    status: ContentStatus | None = None


class ScenarioBase(BaseModel):
    problem_id: int
    title: str = Field(min_length=2, max_length=255)
    slug: str = Field(min_length=2, max_length=255)
    short_description: str = Field(default="", max_length=500)
    description: str = ""
    target_audience: str = ""
    estimated_duration: str = ""
    difficulty_level: DifficultyLevel = DifficultyLevel.MEDIUM
    status: ContentStatus = ContentStatus.DRAFT
    priority: int = 0


class ScenarioCreate(ScenarioBase):
    pass


class ScenarioUpdate(BaseModel):
    problem_id: int | None = None
    title: str | None = Field(default=None, min_length=2, max_length=255)
    slug: str | None = Field(default=None, min_length=2, max_length=255)
    short_description: str | None = Field(default=None, max_length=500)
    description: str | None = None
    target_audience: str | None = None
    estimated_duration: str | None = None
    difficulty_level: DifficultyLevel | None = None
    status: ContentStatus | None = None
    priority: int | None = None
    content_verified_at: datetime | None = None
    verified_by: str | None = None
    verification_notes: str | None = None


class ScenarioStageBase(BaseModel):
    scenario_id: int
    title: str = Field(min_length=2, max_length=255)
    description: str = ""
    order_index: int = 0
    is_required: bool = True


class ScenarioStageCreate(ScenarioStageBase):
    pass


class ScenarioStageUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = None
    order_index: int | None = None
    is_required: bool | None = None


class ScenarioStepBase(BaseModel):
    stage_id: int
    title: str = Field(min_length=2, max_length=255)
    description: str = ""
    order_index: int = 0
    action_type: ActionType = ActionType.INFO
    authority_id: int | None = None
    deadline_id: int | None = None
    is_required: bool = True


class ScenarioStepCreate(ScenarioStepBase):
    pass


class ScenarioStepUpdate(BaseModel):
    stage_id: int | None = None
    title: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = None
    order_index: int | None = None
    action_type: ActionType | None = None
    authority_id: int | None = None
    deadline_id: int | None = None
    is_required: bool | None = None


class DocumentBase(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    description: str = ""
    document_type: str = ""
    is_required: bool = True
    where_to_get: str = ""
    validity_period: str = ""
    status: ContentStatus = ContentStatus.DRAFT


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = None
    document_type: str | None = None
    is_required: bool | None = None
    where_to_get: str | None = None
    validity_period: str | None = None
    status: ContentStatus | None = None


class AuthorityBase(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    description: str = ""
    website_url: str = ""
    phone: str = ""
    address: str = ""
    working_hours: str = ""
    type: str = ""
    region: str = ""
    city: str = ""


class AuthorityCreate(AuthorityBase):
    pass


class AuthorityUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = None
    website_url: str | None = None
    phone: str | None = None
    address: str | None = None
    working_hours: str | None = None
    type: str | None = None
    region: str | None = None
    city: str | None = None


class DeadlineBase(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    description: str = ""
    duration_value: int = 0
    duration_unit: DurationUnit = DurationUnit.DAYS
    is_business_days: bool = False


class DeadlineCreate(DeadlineBase):
    pass


class DeadlineUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = None
    duration_value: int | None = None
    duration_unit: DurationUnit | None = None
    is_business_days: bool | None = None


class NotificationRuleBase(BaseModel):
    step_id: int
    title: str = Field(min_length=2, max_length=255)
    message: str = ""
    notify_before_days: int = 0
    notification_type: NotificationType = NotificationType.REMINDER
    is_active: bool = True


class NotificationRuleCreate(NotificationRuleBase):
    pass


class NotificationRuleUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=255)
    message: str | None = None
    notify_before_days: int | None = None
    notification_type: NotificationType | None = None
    is_active: bool | None = None


class ScenarioDependencyCreate(BaseModel):
    scenario_id: int
    step_id: int
    depends_on_step_id: int
    description: str = ""


class RelatedScenarioCreate(BaseModel):
    scenario_id: int
    related_scenario_id: int
    relation_type: RelationType = RelationType.RELATED_PROBLEM
    description: str = ""


class SourceReferenceCreate(BaseModel):
    sourceable_type: str = Field(min_length=2, max_length=60)
    sourceable_id: int
    title: str = Field(min_length=2, max_length=255)
    url: HttpUrl
    source_type: SourceType = SourceType.OTHER
    description: str = ""
    last_checked_at: datetime | None = None


class LawUpdateBase(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    description: str = ""
    source_url: HttpUrl
    affected_scenario_id: int | None = None
    affected_step_id: int | None = None
    update_date: datetime
    status: LawUpdateStatus = LawUpdateStatus.NEW


class LawUpdateCreate(LawUpdateBase):
    pass


class LawUpdateUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = None
    source_url: HttpUrl | None = None
    affected_scenario_id: int | None = None
    affected_step_id: int | None = None
    update_date: datetime | None = None
    status: LawUpdateStatus | None = None


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class DocumentOut(ORMModel):
    id: int
    title: str
    description: str
    document_type: str
    is_required: bool
    where_to_get: str
    validity_period: str
    status: ContentStatus


class AuthorityOut(ORMModel):
    id: int
    title: str
    description: str
    website_url: str
    phone: str
    address: str
    working_hours: str
    type: str
    region: str = ""
    city: str = ""


class DeadlineOut(ORMModel):
    id: int
    title: str
    description: str
    duration_value: int
    duration_unit: DurationUnit
    is_business_days: bool


class NotificationRuleOut(ORMModel):
    id: int
    title: str
    message: str
    notify_before_days: int
    notification_type: NotificationType
    is_active: bool


class ScenarioStepOut(ORMModel):
    id: int
    title: str
    description: str
    order_index: int
    action_type: ActionType
    is_required: bool
    authority: AuthorityOut | None = None
    deadline: DeadlineOut | None = None
    documents: list[DocumentOut] = Field(default_factory=list)
    notification_rules: list[NotificationRuleOut] = Field(default_factory=list)


class ScenarioStageOut(ORMModel):
    id: int
    title: str
    description: str
    order_index: int
    is_required: bool
    steps: list[ScenarioStepOut] = Field(default_factory=list)


class ScenarioDependencyOut(ORMModel):
    id: int
    step_id: int
    depends_on_step_id: int
    description: str


class RelatedScenarioOut(BaseModel):
    id: int
    scenario_id: int
    related_scenario_id: int
    relation_type: RelationType
    description: str
    related_scenario_title: str
    related_scenario_slug: str


class SourceReferenceOut(ORMModel):
    id: int
    sourceable_type: str
    sourceable_id: int
    title: str
    url: str
    source_type: SourceType
    description: str
    last_checked_at: datetime | None = None


class LawUpdateOut(ORMModel):
    id: int
    title: str
    description: str
    source_url: str
    affected_scenario_id: int | None = None
    affected_step_id: int | None = None
    update_date: datetime
    status: LawUpdateStatus


class ScenarioPublicSummary(ORMModel):
    id: int
    title: str
    slug: str
    short_description: str
    category: str = ""
    status: ContentStatus
    difficulty_level: DifficultyLevel
    estimated_duration: str
    priority: int
    stage_count: int = 0
    task_count: int = 0
    content_verified_at: datetime | None = None
    verified_by: str = ""
    verification_notes: str = ""


class ProblemStepOut(BaseModel):
    id: str = ""
    title: str = ""


class ProblemPublicOut(ORMModel):
    id: int
    title: str
    slug: str
    short_description: str
    description: str
    icon: str
    category: str
    status: ContentStatus
    what_to_do_now: str = ""
    steps: list[ProblemStepOut] = Field(default_factory=list)
    documents: list[str] = Field(default_factory=list)
    deadlines: list[str] = Field(default_factory=list)
    institutions: list[str] = Field(default_factory=list)
    mistakes: list[str] = Field(default_factory=list)


class ProblemWithScenariosOut(ProblemPublicOut):
    scenarios: list[ScenarioPublicSummary] = Field(default_factory=list)


class ScenarioFullOut(ORMModel):
    id: int
    problem_id: int
    title: str
    slug: str
    short_description: str
    category: str = ""
    description: str
    target_audience: str
    estimated_duration: str
    difficulty_level: DifficultyLevel
    status: ContentStatus
    priority: int
    content_verified_at: datetime | None = None
    verified_by: str = ""
    verification_notes: str = ""
    stages: list[ScenarioStageOut] = Field(default_factory=list)
    dependencies: list[ScenarioDependencyOut] = Field(default_factory=list)
    related_scenarios: list[RelatedScenarioOut] = Field(default_factory=list)
    source_references: list[SourceReferenceOut] = Field(default_factory=list)
    law_updates: list[LawUpdateOut] = Field(default_factory=list)


class AuditLogOut(ORMModel):
    """F7 — схема журнала действий редактора для будущего backend endpoint."""
    id: int
    actor: str
    role_id: str
    event_type: str
    action: str
    status: str
    created_at: datetime


class UserAdminOut(BaseModel):
    """H5 — пользователь для раздела «Пользователи и роли»."""
    id: int
    email: str
    name: str
    role_id: str
    is_active: bool
    city: str = ""
    region: str = ""
    created_at: datetime | None = None


class UserRoleUpdate(BaseModel):
    """P11 — изменение роли пользователя (citizen/content_editor/platform_admin)."""
    role: str = Field(pattern="^(citizen|content_editor|platform_admin)$")


class UserActiveUpdate(BaseModel):
    """P11 — бан/разбан (is_active)."""
    is_active: bool


class EmailNotificationOut(ORMModel):
    """I2/I5 — Схема записи в журнале email-уведомлений."""
    id: int
    user_id: int | None
    recipient_email: str
    subject: str
    notification_type: str
    status: str
    error_message: str
    scheduled_at: datetime | None
    sent_at: datetime | None
    created_at: datetime


class AdminListResponse(BaseModel):
    items: list[dict[str, Any]]


class ReorderPayload(BaseModel):
    ids: list[int] = Field(min_length=1)


class ScenarioVerifyNotesPayload(BaseModel):
    notes: str = ""


# ---------------------------------------------------------------------------
# K-этап: публикации (редакторские + UGC) и модерация
# ---------------------------------------------------------------------------

class ArticleAuthorOut(BaseModel):
    name: str = ""
    role: str = "editor"
    proposed_by: str = ""
    proposer_id: int | None = None
    anonymous: bool = False


class ArticleOut(BaseModel):
    id: int
    kind: str
    title: str
    summary: str
    body_html: str
    cover: str
    video: str
    gallery: list[str]
    tags: list[str]
    category: str
    specialization: str
    audience: str
    source: str
    source_url: str
    status: str
    author: ArticleAuthorOut
    reported: bool
    date: str
    views: int
    updated_at: datetime


class ArticleCreate(BaseModel):
    kind: str = Field(default="news")
    title: str = Field(default="", max_length=255)
    summary: str = Field(default="", max_length=2000)
    body_html: str = ""
    cover: str = Field(default="", max_length=1000)
    video: str = Field(default="", max_length=1000)
    gallery: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    category: str = Field(default="", max_length=255)
    specialization: str = Field(default="", max_length=255)
    audience: str = Field(default="all", max_length=64)
    source: str = Field(default="", max_length=255)
    source_url: str = Field(default="", max_length=1000)
    status: str = Field(default="draft")
    date: str = Field(default="", max_length=32)
    anonymous: bool = False
    as_proposal: bool = False  # пользовательское предложение (UGC)


class ArticleUpdate(BaseModel):
    kind: str | None = None
    title: str | None = Field(default=None, max_length=255)
    summary: str | None = Field(default=None, max_length=2000)
    body_html: str | None = None
    cover: str | None = Field(default=None, max_length=1000)
    video: str | None = Field(default=None, max_length=1000)
    gallery: list[str] | None = None
    tags: list[str] | None = None
    category: str | None = Field(default=None, max_length=255)
    specialization: str | None = Field(default=None, max_length=255)
    audience: str | None = Field(default=None, max_length=64)
    source: str | None = Field(default=None, max_length=255)
    source_url: str | None = Field(default=None, max_length=1000)
    status: str | None = None
    date: str | None = Field(default=None, max_length=32)
    reported: bool | None = None


class ArticleModerate(BaseModel):
    action: str  # publish | reject | report | unreport


# ---------------------------------------------------------------------------
# P7 — Каркас раздела «Экстремистский контент» (только структура, без данных)
# ---------------------------------------------------------------------------

EXTREMIST_CATEGORIES = ("registry", "news", "explanation")
EXTREMIST_STATUSES = ("draft", "published")
EXTREMIST_CONTENT_TYPES = (
    "social",
    "channels",
    "media",
    "persons",
    "organizations",
    "music",
    "other",
)


class ExtremistEntryBase(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    category: str = Field(default="registry", max_length=32)
    # Pydantic HttpUrl — жёсткая валидация формата. Поле обязательно.
    source_url: HttpUrl
    source_name: str = Field(default="", max_length=255)
    included_at: datetime | None = None
    last_checked_at: datetime | None = None
    short_description: str = Field(default="", max_length=4000)
    filters_json: str = Field(default="{}", max_length=4000)
    status: str = Field(default="draft", max_length=16)


class ExtremistEntryCreate(ExtremistEntryBase):
    pass


class ExtremistEntryUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=255)
    category: str | None = Field(default=None, max_length=32)
    source_url: HttpUrl | None = None
    source_name: str | None = Field(default=None, max_length=255)
    included_at: datetime | None = None
    last_checked_at: datetime | None = None
    short_description: str | None = Field(default=None, max_length=4000)
    filters_json: str | None = Field(default=None, max_length=4000)
    status: str | None = Field(default=None, max_length=16)


class ExtremistEntryOut(ORMModel):
    id: int
    title: str
    category: str
    source_url: str
    source_name: str
    included_at: datetime | None = None
    last_checked_at: datetime | None = None
    short_description: str
    filters_json: str
    status: str
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# v1.1 (P4) — Пользовательские заметки
# ---------------------------------------------------------------------------

class UserNoteBase(BaseModel):
    text: str = Field(min_length=1, max_length=1000)
    category: str = Field(default="Общее", max_length=80)
    # ISO дата напоминания (yyyy-mm-dd). Пустая строка = без срока.
    reminder_at: str = Field(default="", max_length=40)
    done: bool = False


class UserNoteCreate(UserNoteBase):
    pass


class UserNoteUpdate(BaseModel):
    text: str | None = Field(default=None, min_length=1, max_length=1000)
    category: str | None = Field(default=None, max_length=80)
    reminder_at: str | None = Field(default=None, max_length=40)
    done: bool | None = None


class UserNoteOut(ORMModel):
    id: int
    text: str
    category: str
    reminder_at: str
    done: bool
    created_at: datetime
    updated_at: datetime
