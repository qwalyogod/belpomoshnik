from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

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


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


scenario_step_documents = Table(
    "scenario_step_documents",
    Base.metadata,
    Column("step_id", ForeignKey("scenario_steps.id", ondelete="CASCADE"), primary_key=True),
    Column("document_id", ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True),
    Column("created_at", DateTime(timezone=True), default=datetime.utcnow, nullable=False),
)


class Problem(Base, TimestampMixin):
    __tablename__ = "problems"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    short_description: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    icon: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    category: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    status: Mapped[ContentStatus] = mapped_column(
        SQLEnum(ContentStatus, name="problem_status"),
        default=ContentStatus.DRAFT,
        nullable=False,
        index=True,
    )

    scenarios: Mapped[list[Scenario]] = relationship(
        back_populates="problem",
        cascade="all, delete-orphan",
        order_by=lambda: (Scenario.priority.desc(), Scenario.id.asc()),
    )


class Scenario(Base, TimestampMixin):
    __tablename__ = "scenarios"
    __table_args__ = (
        Index("ix_scenarios_problem_id_status", "problem_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    short_description: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    target_audience: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    estimated_duration: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    difficulty_level: Mapped[DifficultyLevel] = mapped_column(
        SQLEnum(DifficultyLevel, name="scenario_difficulty"),
        default=DifficultyLevel.MEDIUM,
        nullable=False,
    )
    status: Mapped[ContentStatus] = mapped_column(
        SQLEnum(ContentStatus, name="scenario_status"),
        default=ContentStatus.DRAFT,
        nullable=False,
        index=True,
    )
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    content_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    verified_by: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    verification_notes: Mapped[str] = mapped_column(Text, default="", nullable=False)

    problem: Mapped[Problem] = relationship(back_populates="scenarios")
    stages: Mapped[list[ScenarioStage]] = relationship(
        back_populates="scenario",
        cascade="all, delete-orphan",
        order_by=lambda: (ScenarioStage.order_index.asc(), ScenarioStage.id.asc()),
    )
    dependencies: Mapped[list[ScenarioDependency]] = relationship(
        back_populates="scenario",
        cascade="all, delete-orphan",
    )
    related_from: Mapped[list[RelatedScenario]] = relationship(
        back_populates="scenario",
        cascade="all, delete-orphan",
        foreign_keys="RelatedScenario.scenario_id",
    )
    related_to: Mapped[list[RelatedScenario]] = relationship(
        back_populates="related_scenario",
        foreign_keys="RelatedScenario.related_scenario_id",
    )
    law_updates: Mapped[list[LawUpdate]] = relationship(back_populates="affected_scenario")


class ScenarioStage(Base, TimestampMixin):
    __tablename__ = "scenario_stages"
    __table_args__ = (
        Index("ix_scenario_stages_scenario_order", "scenario_id", "order_index"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    scenario_id: Mapped[int] = mapped_column(ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    scenario: Mapped[Scenario] = relationship(back_populates="stages")
    steps: Mapped[list[ScenarioStep]] = relationship(
        back_populates="stage",
        cascade="all, delete-orphan",
        order_by=lambda: (ScenarioStep.order_index.asc(), ScenarioStep.id.asc()),
    )


class Authority(Base, TimestampMixin):
    __tablename__ = "authorities"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    website_url: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    phone: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    address: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    working_hours: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    type: Mapped[str] = mapped_column(String(120), default="", nullable=False)

    steps: Mapped[list[ScenarioStep]] = relationship(back_populates="authority")


class Deadline(Base, TimestampMixin):
    __tablename__ = "deadlines"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    duration_value: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duration_unit: Mapped[DurationUnit] = mapped_column(
        SQLEnum(DurationUnit, name="deadline_duration_unit"),
        default=DurationUnit.DAYS,
        nullable=False,
    )
    is_business_days: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    steps: Mapped[list[ScenarioStep]] = relationship(back_populates="deadline")


class Document(Base, TimestampMixin):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    document_type: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    where_to_get: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    validity_period: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    status: Mapped[ContentStatus] = mapped_column(
        SQLEnum(ContentStatus, name="document_status"),
        default=ContentStatus.DRAFT,
        nullable=False,
        index=True,
    )

    steps: Mapped[list[ScenarioStep]] = relationship(
        secondary=scenario_step_documents,
        back_populates="documents",
    )


class ScenarioStep(Base, TimestampMixin):
    __tablename__ = "scenario_steps"
    __table_args__ = (
        Index("ix_scenario_steps_stage_order", "stage_id", "order_index"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    stage_id: Mapped[int] = mapped_column(ForeignKey("scenario_stages.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    action_type: Mapped[ActionType] = mapped_column(
        SQLEnum(ActionType, name="scenario_step_action_type"),
        default=ActionType.INFO,
        nullable=False,
    )
    authority_id: Mapped[int | None] = mapped_column(ForeignKey("authorities.id", ondelete="SET NULL"), nullable=True)
    deadline_id: Mapped[int | None] = mapped_column(ForeignKey("deadlines.id", ondelete="SET NULL"), nullable=True)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    stage: Mapped[ScenarioStage] = relationship(back_populates="steps")
    authority: Mapped[Authority | None] = relationship(back_populates="steps")
    deadline: Mapped[Deadline | None] = relationship(back_populates="steps")
    documents: Mapped[list[Document]] = relationship(
        secondary=scenario_step_documents,
        back_populates="steps",
    )
    notification_rules: Mapped[list[NotificationRule]] = relationship(
        back_populates="step",
        cascade="all, delete-orphan",
    )
    dependencies_as_step: Mapped[list[ScenarioDependency]] = relationship(
        back_populates="step",
        cascade="all, delete-orphan",
        foreign_keys="ScenarioDependency.step_id",
    )
    dependencies_as_prerequisite: Mapped[list[ScenarioDependency]] = relationship(
        back_populates="depends_on_step",
        foreign_keys="ScenarioDependency.depends_on_step_id",
    )
    law_updates: Mapped[list[LawUpdate]] = relationship(back_populates="affected_step")


class NotificationRule(Base, TimestampMixin):
    __tablename__ = "notification_rules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    step_id: Mapped[int] = mapped_column(ForeignKey("scenario_steps.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, default="", nullable=False)
    notify_before_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    notification_type: Mapped[NotificationType] = mapped_column(
        SQLEnum(NotificationType, name="notification_rule_type"),
        default=NotificationType.REMINDER,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    step: Mapped[ScenarioStep] = relationship(back_populates="notification_rules")


class ScenarioDependency(Base, TimestampMixin):
    __tablename__ = "scenario_dependencies"
    __table_args__ = (
        UniqueConstraint("step_id", "depends_on_step_id", name="uq_scenario_dependency_pair"),
        Index("ix_scenario_dependencies_scenario", "scenario_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    scenario_id: Mapped[int] = mapped_column(ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False)
    step_id: Mapped[int] = mapped_column(ForeignKey("scenario_steps.id", ondelete="CASCADE"), nullable=False)
    depends_on_step_id: Mapped[int] = mapped_column(ForeignKey("scenario_steps.id", ondelete="CASCADE"), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)

    scenario: Mapped[Scenario] = relationship(back_populates="dependencies")
    step: Mapped[ScenarioStep] = relationship(
        back_populates="dependencies_as_step",
        foreign_keys=[step_id],
    )
    depends_on_step: Mapped[ScenarioStep] = relationship(
        back_populates="dependencies_as_prerequisite",
        foreign_keys=[depends_on_step_id],
    )


class RelatedScenario(Base, TimestampMixin):
    __tablename__ = "related_scenarios"
    __table_args__ = (
        UniqueConstraint("scenario_id", "related_scenario_id", "relation_type", name="uq_related_scenario"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    scenario_id: Mapped[int] = mapped_column(ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False)
    related_scenario_id: Mapped[int] = mapped_column(ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False)
    relation_type: Mapped[RelationType] = mapped_column(
        SQLEnum(RelationType, name="related_scenario_type"),
        default=RelationType.RELATED_PROBLEM,
        nullable=False,
    )
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)

    scenario: Mapped[Scenario] = relationship(
        back_populates="related_from",
        foreign_keys=[scenario_id],
    )
    related_scenario: Mapped[Scenario] = relationship(
        back_populates="related_to",
        foreign_keys=[related_scenario_id],
    )


class SourceReference(Base, TimestampMixin):
    __tablename__ = "source_references"
    __table_args__ = (
        Index("ix_source_references_sourceable", "sourceable_type", "sourceable_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sourceable_type: Mapped[str] = mapped_column(String(60), nullable=False)
    sourceable_id: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    source_type: Mapped[SourceType] = mapped_column(
        SQLEnum(SourceType, name="source_reference_type"),
        default=SourceType.OTHER,
        nullable=False,
    )
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class LawUpdate(Base, TimestampMixin):
    __tablename__ = "law_updates"
    __table_args__ = (
        Index("ix_law_updates_status", "status"),
        Index("ix_law_updates_scenario_step", "affected_scenario_id", "affected_step_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    source_url: Mapped[str] = mapped_column(String(1000), default="", nullable=False)
    affected_scenario_id: Mapped[int | None] = mapped_column(
        ForeignKey("scenarios.id", ondelete="SET NULL"),
        nullable=True,
    )
    affected_step_id: Mapped[int | None] = mapped_column(
        ForeignKey("scenario_steps.id", ondelete="SET NULL"),
        nullable=True,
    )
    update_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[LawUpdateStatus] = mapped_column(
        SQLEnum(LawUpdateStatus, name="law_update_status"),
        default=LawUpdateStatus.NEW,
        nullable=False,
    )

    affected_scenario: Mapped[Scenario | None] = relationship(back_populates="law_updates")
    affected_step: Mapped[ScenarioStep | None] = relationship(back_populates="law_updates")


class Role(Base):
    """H5 — Роль пользователя: citizen / content_editor / platform_admin."""
    __tablename__ = "roles"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    users: Mapped[list[User]] = relationship(back_populates="role")


class User(Base, TimestampMixin):
    """H2, H3, H4, H5 — Пользователь приложения."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    role_id: Mapped[str] = mapped_column(
        ForeignKey("roles.id", ondelete="SET DEFAULT"),
        default="citizen",
        nullable=False,
        index=True,
    )
    city: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    region: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    district: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    address: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    employment_status: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    has_children: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    owns_property: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_car: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_renter: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    interest_tags: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    settings: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    role: Mapped[Role] = relationship(back_populates="users")
    documents: Mapped[list[UserDocument]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    refresh_tokens: Mapped[list[RefreshToken]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class RefreshToken(Base):
    """H3 — JWT refresh-токен (хранится в БД, revoked = отозван)."""
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    user: Mapped[User] = relationship(back_populates="refresh_tokens")


class UserDocument(Base, TimestampMixin):
    """H7, G6 — Личный документ пользователя (паспорт, СНИЛС и т.д.)."""
    __tablename__ = "user_documents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    doc_type: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    number: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    issued_by: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    issued_date: Mapped[str] = mapped_column(String(20), default="", nullable=False)
    expiry_date: Mapped[str] = mapped_column(String(20), default="", nullable=False)
    is_sensitive: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    comment: Mapped[str] = mapped_column(Text, default="", nullable=False)

    user: Mapped[User] = relationship(back_populates="documents")


class UserSituation(Base, TimestampMixin):
    """G5 — Личная ситуация пользователя (план из шаблона сценария)."""
    __tablename__ = "user_situations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    template_id: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(64), default="В процессе", nullable=False)
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    category: Mapped[str] = mapped_column(String(120), default="", nullable=False)

    tasks: Mapped[list[UserSituationTask]] = relationship(
        back_populates="situation",
        cascade="all, delete-orphan",
        order_by=lambda: (UserSituationTask.order_index.asc(), UserSituationTask.id.asc()),
    )


class UserSituationTask(Base):
    """G5 — Задача внутри личной ситуации."""
    __tablename__ = "user_situation_tasks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    situation_id: Mapped[str] = mapped_column(
        ForeignKey("user_situations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    due_date: Mapped[str] = mapped_column(String(20), default="", nullable=False)
    stage_title: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    situation: Mapped[UserSituation] = relationship(back_populates="tasks")


class UserNotification(Base):
    """G7 — Уведомление пользователя."""
    __tablename__ = "user_notifications"
    __table_args__ = (
        Index("ix_user_notifications_user_read", "user_id", "is_read"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    notification_type: Mapped[str] = mapped_column(String(64), default="task", nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    source: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    due_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class EmailNotification(Base):
    """I2 — Модель email-уведомления (журнал доставки + очередь отправки)."""
    __tablename__ = "email_notifications"
    __table_args__ = (
        Index("ix_email_notifications_user_status", "user_id", "status"),
        Index("ix_email_notifications_scheduled", "status", "scheduled_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    recipient_email: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    notification_type: Mapped[str] = mapped_column(String(64), nullable=False, default="doc_expiry")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", index=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class AuditLog(Base, TimestampMixin):
    """
    F7 — Журнал действий редактора/админа.
    MVP: хранит действия локально через admin_audit_logs_state.
    Production: эта модель хранит записи в БД.
    Структура отражает будущую backend-модель; миграции готовить после G.
    """
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    role_id: Mapped[str] = mapped_column(String(64), nullable=False, default="content_editor")
    event_type: Mapped[str] = mapped_column(String(32), nullable=False, default="other")
    action: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="demo")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
