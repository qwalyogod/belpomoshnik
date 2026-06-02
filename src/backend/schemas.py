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
    status: ContentStatus
    difficulty_level: DifficultyLevel
    estimated_duration: str
    priority: int
    content_verified_at: datetime | None = None
    verified_by: str = ""
    verification_notes: str = ""


class ProblemPublicOut(ORMModel):
    id: int
    title: str
    slug: str
    short_description: str
    description: str
    icon: str
    category: str
    status: ContentStatus


class ProblemWithScenariosOut(ProblemPublicOut):
    scenarios: list[ScenarioPublicSummary] = Field(default_factory=list)


class ScenarioFullOut(ORMModel):
    id: int
    problem_id: int
    title: str
    slug: str
    short_description: str
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

