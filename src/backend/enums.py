from enum import Enum


class ContentStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class ActionType(str, Enum):
    INFO = "info"
    VISIT_OFFICE = "visit_office"
    ONLINE_REQUEST = "online_request"
    DOCUMENT_PREPARE = "document_prepare"
    PAYMENT = "payment"
    WAITING = "waiting"


class DurationUnit(str, Enum):
    DAYS = "days"
    WEEKS = "weeks"
    MONTHS = "months"


class NotificationType(str, Enum):
    REMINDER = "reminder"
    DEADLINE = "deadline"
    UPDATE = "update"


class RelationType(str, Enum):
    NEXT_STEP = "next_step"
    ALTERNATIVE = "alternative"
    RELATED_PROBLEM = "related_problem"


class SourceType(str, Enum):
    LAW = "law"
    GOVERNMENT_PORTAL = "government_portal"
    MINISTRY = "ministry"
    COURT = "court"
    TAX = "tax"
    REGISTRY = "registry"
    OTHER = "other"


class LawUpdateStatus(str, Enum):
    NEW = "new"
    REVIEWED = "reviewed"
    APPLIED = "applied"

