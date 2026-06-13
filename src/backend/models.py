from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum as SQLEnum,
    Float,
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


def _utcnow() -> datetime:
    """Timezone-aware UTC now (replaces deprecated datetime.utcnow())."""
    return datetime.now(timezone.utc)


def _json_list(raw: str) -> list:
    try:
        value = json.loads(raw or "[]")
        return value if isinstance(value, list) else []
    except (ValueError, TypeError):
        return []


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        onupdate=_utcnow,
        nullable=False,
    )


scenario_step_documents = Table(
    "scenario_step_documents",
    Base.metadata,
    Column("step_id", ForeignKey("scenario_steps.id", ondelete="CASCADE"), primary_key=True),
    Column("document_id", ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True),
    Column("created_at", DateTime(timezone=True), default=_utcnow, nullable=False),
)


class Problem(Base, TimestampMixin):
    __tablename__ = "problems"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    short_description: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    icon: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    category: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    # Rich «what to do» content (ported from the Flet PROBLEM_DETAIL set).
    what_to_do_now: Mapped[str] = mapped_column(Text, default="", nullable=False)
    steps_json: Mapped[str] = mapped_column(String(500), default="[]", nullable=False)
    documents_json: Mapped[str] = mapped_column(String(500), default="[]", nullable=False)
    deadlines_json: Mapped[str] = mapped_column(String(500), default="[]", nullable=False)
    institutions_json: Mapped[str] = mapped_column(String(500), default="[]", nullable=False)
    mistakes_json: Mapped[str] = mapped_column(String(500), default="[]", nullable=False)
    status: Mapped[ContentStatus] = mapped_column(
        SQLEnum(ContentStatus, name="problem_status"),
        default=ContentStatus.DRAFT,
        nullable=False,
        index=True,
    )

    @property
    def steps(self) -> list:
        return _json_list(self.steps_json)

    @property
    def documents(self) -> list:
        return _json_list(self.documents_json)

    @property
    def deadlines(self) -> list:
        return _json_list(self.deadlines_json)

    @property
    def institutions(self) -> list:
        return _json_list(self.institutions_json)

    @property
    def mistakes(self) -> list:
        return _json_list(self.mistakes_json)

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

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
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

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
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

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    external_id: Mapped[str] = mapped_column(String(255), default="", nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    website_url: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    phone: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    email: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    address: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    working_hours: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    type: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    region: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    district: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    city: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    settlement: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    services_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    tags_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    related_scenario_categories_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    related_scenarios_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    source_ids_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    source_urls_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    last_checked_at: Mapped[str] = mapped_column(String(40), default="", nullable=False)
    confidence: Mapped[str] = mapped_column(String(40), default="", nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    @property
    def services(self) -> list:
        return _json_list(self.services_json)

    @property
    def tags(self) -> list:
        return _json_list(self.tags_json)

    @property
    def related_scenario_categories(self) -> list:
        return _json_list(self.related_scenario_categories_json)

    @property
    def related_scenarios(self) -> list:
        return _json_list(self.related_scenarios_json)

    @property
    def source_ids(self) -> list:
        return _json_list(self.source_ids_json)

    @property
    def source_urls(self) -> list:
        return _json_list(self.source_urls_json)

    steps: Mapped[list[ScenarioStep]] = relationship(back_populates="authority")


class Deadline(Base, TimestampMixin):
    __tablename__ = "deadlines"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
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

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
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

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
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

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
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

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
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

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
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

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
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

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    body_html: Mapped[str] = mapped_column(Text, default="", nullable=False)
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
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    users: Mapped[list[User]] = relationship(back_populates="role")


class User(Base, TimestampMixin):
    """H2, H3, H4, H5 — Пользователь приложения."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    role_id: Mapped[str] = mapped_column(
        ForeignKey("roles.id", ondelete="RESTRICT"),
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
    interest_tags: Mapped[str] = mapped_column(String(500), default="[]", nullable=False)
    # v1.1 (P4): JSON-массив адресов пользователя (до 5 шт.). Валидация
    # и нормализация — в api/user.py, здесь только ограничение длины.
    addresses_json: Mapped[str] = mapped_column(String(2000), default="[]", nullable=False)
    # v1.2: путь к обрезанному аватару (/uploads/avatars/<uid>/<token>.<ext>)
    # или "" если не задан. Файл лежит в data/uploads/avatars, загрузка — api/user.py.
    avatar_url: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    settings: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_test_account: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    role: Mapped[Role] = relationship(back_populates="users")
    documents: Mapped[list[UserDocument]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    refresh_tokens: Mapped[list[RefreshToken]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    # v1.1 (P4): пользовательские заметки (текст, категория, срок).
    notes: Mapped[list[UserNote]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        order_by=lambda: UserNote.created_at.desc(),
    )


class RefreshToken(Base):
    """H3 — JWT refresh-токен (хранится в БД, revoked = отозван)."""
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    user: Mapped[User] = relationship(back_populates="refresh_tokens")


class UserNote(Base, TimestampMixin):
    """v1.1 (P4) — пользовательская заметка с категорией и сроком напоминания.

    Заметки отделены от задач ситуаций: это свободные текстовые напоминания
    пользователя, которые показываются на главной рядом с активными ситуациями
    и могут быть помечены как выполненные.
    """
    __tablename__ = "user_notes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    text: Mapped[str] = mapped_column(String(1000), nullable=False)
    category: Mapped[str] = mapped_column(String(80), default="Общее", nullable=False)
    # ISO дата напоминания (yyyy-mm-dd). Может быть пустой строкой.
    reminder_at: Mapped[str] = mapped_column(String(40), default="", nullable=False)
    done: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    user: Mapped[User] = relationship(back_populates="notes")


class UserDocument(Base, TimestampMixin):
    """H7, G6 — Личный документ пользователя (паспорт, СНИЛС и т.д.)."""
    __tablename__ = "user_documents"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    doc_type: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    number: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    issued_by: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    issued_date: Mapped[str] = mapped_column(String(20), default="", nullable=False)
    expiry_date: Mapped[str] = mapped_column(String(20), default="", nullable=False)
    is_sensitive: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    comment: Mapped[str] = mapped_column(Text, default="", nullable=False)
    scan_path: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    # v0.4: пользовательские поля для doc_type='other'. Храним как JSON-строку,
    # чтобы не плодить колонки. Для остальных типов остаётся пустым.
    custom_fields_json: Mapped[str] = mapped_column(String(2000), default="", nullable=False)
    # Промпт 1 (encryption at-rest). Plain-колонки выше оставлены для backward
    # compatibility — read-путь умеет fallback. Все новые записи идут только
    # в encrypted-колонки; plain остаются пустыми.
    number_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    issued_by_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    comment_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    custom_fields_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Скан хранится зашифрованно вне публичной /uploads-папки.
    scan_encrypted_path: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    scan_original_filename: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    scan_mime_type: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    scan_size: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    scan_uploaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

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
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    situation: Mapped[UserSituation] = relationship(back_populates="tasks")


class UserNotification(Base):
    """G7 — Уведомление пользователя."""
    __tablename__ = "user_notifications"
    __table_args__ = (
        Index("ix_user_notifications_user_read", "user_id", "is_read"),
        # Промпт 6: dedupe — не создавать одну и ту же запись повторно.
        Index("ix_user_notifications_dedupe", "user_id", "dedupe_key"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    notification_type: Mapped[str] = mapped_column(String(64), default="task", nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    source: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    due_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    # Промпт 6: route для глубокой ссылки в приложении.
    route: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    # Промпт 6: дедупликация. Пустая строка = не подлежит дедупу.
    dedupe_key: Mapped[str] = mapped_column(String(255), default="", nullable=False)


class UserPushToken(Base, TimestampMixin):
    """Промпт 6: device-токен пользователя для native push (FCM/APNs).

    Полный токен на frontend не возвращается — только masked + last_seen_at.
    """
    __tablename__ = "user_push_tokens"
    __table_args__ = (
        UniqueConstraint("user_id", "token_hash", name="uq_user_push_tokens_hash"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    platform: Mapped[str] = mapped_column(String(16), default="android", nullable=False)
    token_hash: Mapped[str] = mapped_column(String(120), nullable=False)
    token_encrypted: Mapped[str] = mapped_column(Text, default="", nullable=False)
    device_label: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class UtilityAccount(Base, TimestampMixin):
    """G8 — Лицевой счёт ЖКХ пользователя."""
    __tablename__ = "utility_accounts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    address: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    account_number: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    provider: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    # Промпт 2: расширенные поля. Все добавлены опциональными с дефолтами,
    # чтобы старые ответы API оставались валидными.
    label: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    service_types: Mapped[str] = mapped_column(String(500), default="[]", nullable=False)  # JSON-массив
    payer_name: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    manual_mode: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_sync_note: Mapped[str] = mapped_column(String(500), default="", nullable=False)

    payments: Mapped[list[UtilityPayment]] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
        order_by=lambda: UtilityPayment.id.asc(),
    )
    requests: Mapped[list["UtilityRequest"]] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
        order_by=lambda: UtilityRequest.created_at.desc(),
    )


class UtilityPayment(Base):
    """G8 — Платёж/период ЖКХ по лицевому счёту."""
    __tablename__ = "utility_payments"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    account_id: Mapped[str] = mapped_column(
        ForeignKey("utility_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    period: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    readings_date: Mapped[str] = mapped_column(String(20), default="", nullable=False)
    payment_date: Mapped[str] = mapped_column(String(20), default="", nullable=False)
    amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    status: Mapped[str] = mapped_column(String(64), default="Ожидает", nullable=False)
    readings_deadline: Mapped[str] = mapped_column(String(20), default="", nullable=False)
    payment_deadline: Mapped[str] = mapped_column(String(20), default="", nullable=False)
    comment: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    # Промпт 2: breakdown как JSON-строка (вода/свет/газ с показаниями и тарифом).
    breakdown_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    # manual / erip / receipt — откуда запись (manual = пользователь ввёл).
    source: Mapped[str] = mapped_column(String(32), default="manual", nullable=False)
    # Путь к загруженной квитанции (зашифровано через тот же сервис, что и сканы документов).
    receipt_path: Mapped[str] = mapped_column(String(500), default="", nullable=False)

    account: Mapped[UtilityAccount] = relationship(back_populates="payments")


class TaxObligation(Base, TimestampMixin):
    """G9 — Налоговое обязательство пользователя."""
    __tablename__ = "tax_obligations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user_type: Mapped[str] = mapped_column(String(32), default="individual", nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    deadline: Mapped[str] = mapped_column(String(20), default="", nullable=False)
    amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    receipt_path: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    status: Mapped[str] = mapped_column(String(64), default="Предстоит", nullable=False)
    period: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    comment: Mapped[str] = mapped_column(Text, default="", nullable=False)
    # Промпт 2: расширенные поля.
    tax_type: Mapped[str] = mapped_column(String(40), default="other", nullable=False)
    source: Mapped[str] = mapped_column(String(32), default="manual", nullable=False)
    recipient: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    unp: Mapped[str] = mapped_column(String(40), default="", nullable=False)
    notice_number: Mapped[str] = mapped_column(String(80), default="", nullable=False)
    payment_code: Mapped[str] = mapped_column(String(80), default="", nullable=False)
    paid_at: Mapped[str] = mapped_column(String(20), default="", nullable=False)
    external_url: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    help_text: Mapped[str] = mapped_column(String(500), default="", nullable=False)


class AIChatSession(Base, TimestampMixin):
    """Промпт 3: сессия AI-чата пользователя. Гражданская или редакторская."""
    __tablename__ = "ai_chat_sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    mode: Mapped[str] = mapped_column(String(16), default="citizen", nullable=False)
    archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_message_preview: Mapped[str] = mapped_column(String(255), default="", nullable=False)

    messages: Mapped[list["AIChatMessage"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by=lambda: AIChatMessage.created_at.asc(),
    )


class AIChatMessage(Base):
    """Промпт 3: сообщение в AI-чате (user / assistant / system)."""
    __tablename__ = "ai_chat_messages"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("ai_chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(16), default="user", nullable=False)
    content: Mapped[str] = mapped_column(Text, default="", nullable=False)
    links_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    actions_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    sources_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    source: Mapped[str] = mapped_column(String(16), default="llm", nullable=False)
    model: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    provider: Mapped[str] = mapped_column(String(40), default="", nullable=False)
    error_code: Mapped[str] = mapped_column(String(40), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    session: Mapped[AIChatSession] = relationship(back_populates="messages")


class UtilityRequest(Base, TimestampMixin):
    """Промпт 2: пользовательская заявка ЖКХ (115). Локальный органайзер,
    реальной отправки в 115.бел нет — пользователь руками отмечает статусы."""
    __tablename__ = "utility_requests"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id: Mapped[str | None] = mapped_column(
        ForeignKey("utility_accounts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    address: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(40), default="other", nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="draft", nullable=False, index=True)
    external_number: Mapped[str] = mapped_column(String(80), default="", nullable=False)
    external_url: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    target_service: Mapped[str] = mapped_column(String(80), default="", nullable=False)

    account: Mapped[UtilityAccount | None] = relationship(back_populates="requests")


class EmailNotification(Base):
    """I2 — Модель email-уведомления (журнал доставки + очередь отправки)."""
    __tablename__ = "email_notifications"
    __table_args__ = (
        Index("ix_email_notifications_user_status", "user_id", "status"),
        Index("ix_email_notifications_scheduled", "status", "scheduled_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
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
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)


class AuditLog(Base, TimestampMixin):
    """
    F7 — Журнал действий редактора/админа.
    MVP: хранит действия локально через admin_audit_logs_state.
    Production: эта модель хранит записи в БД.
    Структура отражает будущую backend-модель; миграции готовить после G.
    """
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    actor: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    role_id: Mapped[str] = mapped_column(String(64), nullable=False, default="content_editor")
    event_type: Mapped[str] = mapped_column(String(32), nullable=False, default="other")
    action: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="demo")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)


class Article(Base, TimestampMixin):
    """Editorial / UGC publication (news, situation, problem) — K-этап.

    Local-first на фронте; здесь — серверный источник правды. Авторство хранит
    и автора-редактора (author_name), и предложившего пользователя (proposer).
    """

    __tablename__ = "articles"
    __table_args__ = (
        Index("ix_articles_status", "status"),
        Index("ix_articles_kind_status", "kind", "status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    kind: Mapped[str] = mapped_column(String(16), default="news", nullable=False)  # news|scenario|problem
    title: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    body_html: Mapped[str] = mapped_column(Text, default="", nullable=False)
    cover: Mapped[str] = mapped_column(String(1000), default="", nullable=False)
    video: Mapped[str] = mapped_column(String(1000), default="", nullable=False)
    gallery: Mapped[str] = mapped_column(String(2000), default="[]", nullable=False)  # JSON list of urls
    tags: Mapped[str] = mapped_column(String(500), default="[]", nullable=False)     # JSON list of strings
    category: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    specialization: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    audience: Mapped[str] = mapped_column(String(64), default="all", nullable=False)
    source: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    source_url: Mapped[str] = mapped_column(String(1000), default="", nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="draft", nullable=False)  # draft|review|published|rejected
    # authorship
    author_name: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    author_role: Mapped[str] = mapped_column(String(32), default="editor", nullable=False)
    proposed_by: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    proposer_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    anonymous: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reported: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    publish_date: Mapped[str] = mapped_column(String(32), default="", nullable=False)  # yyyy-mm-dd
    views: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class ContentTag(Base, TimestampMixin):
    """Редакторский справочник тегов для публикаций.

    Статьи хранят выбранные теги как JSON-список строк для совместимости с
    уже созданным контентом, а этот справочник задаёт разрешённый набор тегов,
    который редактор видит и поддерживает в админке.
    """

    __tablename__ = "content_tags"
    __table_args__ = (
        UniqueConstraint("name", name="uq_content_tags_name"),
        UniqueConstraint("slug", name="uq_content_tags_slug"),
        Index("ix_content_tags_active", "is_active"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    color: Mapped[str] = mapped_column(String(32), default="", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class BlockedSubmitter(Base):
    """Пользователь, которому администрация запретила предлагать контент."""

    __tablename__ = "blocked_submitters"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    blocked_by: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)


class ArticleViewDaily(Base):
    """Посуточный счётчик просмотров материалов (для графика дашборда)."""

    __tablename__ = "article_view_daily"

    day: Mapped[str] = mapped_column(String(10), primary_key=True)  # yyyy-mm-dd
    count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class ExtremistEntry(Base, TimestampMixin):
    """P7 — Каркас раздела «Экстремистский контент».

    Это юридически чувствительная таблица. Любая запись ОБЯЗАНА иметь
    проверенный официальный source_url. Контент хранится в статусе
    ``draft`` по умолчанию; перевод в published выполняется после ручной
    проверки официального источника.
    """

    __tablename__ = "extremist_entries"
    __table_args__ = (
        Index("ix_extremist_entries_status", "status"),
        Index("ix_extremist_entries_category", "category"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    # kind: registry | news | explanation
    category: Mapped[str] = mapped_column(String(32), nullable=False, default="registry")
    # Обязательный URL официального источника
    source_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    source_name: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    included_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_checked_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    short_description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    cover_url: Mapped[str] = mapped_column(String(1000), default="", nullable=False)
    # JSON-массивы URL. Файлы загружаются через общий /api/articles/upload,
    # ссылки можно вставлять вручную из официального источника.
    media_urls: Mapped[str] = mapped_column(String(500), default="[]", nullable=False)
    attachment_urls: Mapped[str] = mapped_column(String(500), default="[]", nullable=False)
    # JSON-словарь: {"content_types": ["social", "channels", "media", ...]}.
    # Храним как строку, чтобы не зависеть от диалекта JSON-типа.
    filters_json: Mapped[str] = mapped_column(String(500), default="{}", nullable=False)
    # draft | published. По умолчанию draft: контент не верифицирован.
    status: Mapped[str] = mapped_column(String(16), default="draft", nullable=False)
