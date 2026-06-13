// Domain types — single source of truth. Future API responses will match these.

export type Role = "guest" | "citizen" | "content_editor" | "platform_admin" | "editor" | "admin";
// NB: "editor" | "admin" оставлены для обратной совместимости со старыми quickAccounts
// в localStorage. Новые записи (после security-фикса) используют "content_editor" / "platform_admin".
export type Lang = "ru" | "be" | "en";

export interface AppUser {
  id: string;
  name: string;
  email: string;
  role: Role;
  region?: string;
  city?: string;
  district?: string;
  isTestAccount?: boolean;
}

export type CategoryId = "documents" | "family" | "work" | "business" | "housing" | "taxes" | "health" | "auto";

export interface Category {
  id: CategoryId;
  name: string;
}

export interface ContentTag {
  id: string;
  name: string;
  slug: string;
  description: string;
  color: string;
  isActive: boolean;
}

export type Difficulty = "easy" | "medium" | "hard";

export interface OfficialSource {
  id: string;
  title: string;
  url: string;
  description: string;
  checkedAt?: string;       // ISO date, or undefined → "требует проверки"
}

/** P6: расширенный источник для интеграции с NewsPage.
 *  Отдельный от OfficialSource (вложен в сценарии) — здесь с type/lastChecked
 *  для UI-чипов и фильтрации. */
export interface Source {
  id: string;
  title: string;
  type: string;             // law | ministry | government_portal | tax | registry
  url: string;
  description: string;
  lastChecked: string;      // yyyy-mm-dd
}

export interface Institution {
  id: string;
  name: string;
  address: string;
  hours?: string;
  phone?: string;
  region?: string;
  city?: string;
}

export interface DocumentRef {
  id: string;
  name: string;
  required: boolean;
  note?: string;
}

export type TaskKind = "form" | "visit" | "payment" | "wait" | "document";

export interface Task {
  id: string;
  title: string;
  kind: TaskKind;
  durationHint?: string;     // e.g. "до 14 дней"
  dueOffsetDays?: number;    // relative to situation start
  blockedBy?: string[];      // ids of tasks that must be completed first
  documents?: string[];      // DocumentRef ids
  institutionId?: string;
}

export interface Stage {
  id: string;
  title: string;
  description?: string;
  tasks: Task[];
}

export interface Scenario {
  id: string;
  title: string;
  category: CategoryId;
  shortDescription: string;
  longDescription: string;
  forWhom: string;
  estimatedTime: string;      // "от 14 дней"
  difficulty: Difficulty;
  stageCount?: number;
  taskCount?: number;
  stages: Stage[];
  documents: DocumentRef[];
  institutions: Institution[];
  sources: OfficialSource[];
  relatedIds: string[];
}

export type SituationStatus = "not_started" | "in_progress" | "done";

export interface UserSituation {
  id: string;
  scenarioId: string;
  status: SituationStatus;
  startedAt: string;          // ISO
  completedTaskIds: string[];
  backendTaskIds?: Record<string, string>; // scenario task id -> backend task id
  // v1.2: серверный id ситуации. Локальный `id` остаётся стабильным (для роутинга
  // /situations/:id), а backendId используется для backend-операций (delete/sync).
  backendId?: string;
  notes: Record<string, string>; // taskId -> note
}

export type UserDocumentStatus = "active" | "expiring" | "expired";
export type UserDocumentType = "passport" | "driver" | "medical" | "birth" | "housing" | "receipt" | "other";

/** v0.4: пользовательское поле для типа «Другое». */
export interface CustomField {
  name: string;
  value: string;
}

export interface UserDocument {
  id: string;
  type: UserDocumentType;
  title: string;
  number: string;             // raw — UI masks it
  issuedAt?: string;
  issuedBy?: string;
  comment?: string;
  expiresAt?: string;
  status: UserDocumentStatus;
  /** v0.4: только для type='other'. Хранится в БД как JSON-строка. */
  customFields?: CustomField[];
}

export interface UtilityPayment {
  id: string;
  accountId: string;
  period: string;
  readingsDate?: string;
  paymentDate?: string;
  amount: number;
  status: string; // "Ожидает" | "Оплачено" | "Просрочено"
  readingsDeadline?: string;
  paymentDeadline?: string;
  comment?: string;
}

export interface UtilityAccount {
  id: string;
  address: string;
  accountNumber: string;
  provider: string;
  payments: UtilityPayment[];
}

export interface TaxObligation {
  id: string;
  title: string;
  userType: string; // "individual" | "ip"
  deadline?: string;
  amount: number;
  status: string; // "Предстоит" | "Оплачено" | "Просрочено"
  period?: string;
  comment?: string;
  receiptPath?: string;
}

export interface AdminScenarioRow {
  id: string;
  title: string;
  category: CategoryId;
  status: "published" | "review" | "draft";
  taskCount: number;
}

export interface AppNotification {
  id: string;
  kind: "task_due" | "document_expiring" | "legal_update" | "step_done";
  title: string;
  body?: string;
  createdAt: string;
  read: boolean;
  link?: { page: string; id?: string };
}

export interface LegalUpdate {
  id: string;
  category: CategoryId;
  title: string;
  summary: string;
  bodyHtml?: string;
  whoAffected: string;
  whatChanged: string;
  whatToDo: string;
  effectiveDate: string;       // ISO
  source: OfficialSource;
  /** P6: опциональная привязка к Source.id из OFFICIAL_SOURCES.
   *  Если пусто — NewsPage ищет источник по `source.id`. */
  sourceIds?: string[];
  priority: boolean;
  matchesProfile: boolean;
}

export interface UserProfile {
  name: string;
  email: string;
  region: string;
  city: string;
  district: string;
  address?: string;
  employment: string;
  flags: {
    hasChildren: boolean;
    hasCar: boolean;
    homeowner: boolean;
    tenant: boolean;
  };
  interests: string[];
  learningProgress: number;    // 0..100
  achievements: { id: string; title: string }[];
  // v1.2: URL аватара. Обрезанное в редакторе фото грузится на бэк
  // (POST /api/user/avatar → users.avatar_url) и приходит абсолютным URL на
  // /uploads/avatars/... Может временно держать data:/blob: при локальном
  // предпросмотре. Имя историческое (раньше тут был base64 data URL).
  avatarDataUrl?: string;
  // v1.1 (P4): до 5 адресов пользователя (label + регион/район/город/улица).
  // Один помечается isPrimary. На бэк ходит как addresses_json.
  addresses: UserAddress[];
  // v1.1 (P4): id предпочтительных источников новостей (OFFICIAL_SOURCES).
  // Локальная фишка — хранится ТОЛЬКО в localStorage.
  preferredSourceIds: string[];
}

export interface UserAddress {
  id: string;
  label: string;
  region: string;
  district: string;
  city: string;
  street: string;
  isPrimary: boolean;
}

export const NOTE_CATEGORIES = ["Общее", "Документы", "Семья", "Здоровье"] as const;
export type NoteCategory = (typeof NOTE_CATEGORIES)[number];

export interface UserNote {
  id: string;
  text: string;
  category: NoteCategory;
  /** ISO дата напоминания (yyyy-mm-dd или полный ISO). */
  reminderAt?: string;
  done: boolean;
  createdAt: string;
}

export interface Settings {
  theme: "light" | "dark";
  lang: Lang;
  notifications: {
    deadlines: boolean;
    documents: boolean;
    legal: boolean;
    push: boolean;
  };
  privacy: {
    maskDocuments: boolean;
    quickLogin: boolean;
  };
  accessibility: {
    largeFont: boolean;
    highContrast: boolean;
  };
}

export interface Problem {
  id: string;
  title: string;
  category: CategoryId;
  shortDescription: string;
  whatToDoNow: string;
  steps: { id: string; title: string; checked?: boolean }[];
  documents: string[];
  deadlines: string[];
  institutions: string[];
  mistakes: string[];
}

export type ArticleKind = "news" | "scenario" | "problem";
export type ArticleStatus = "published" | "draft" | "review" | "rejected";

export interface AuthorMeta {
  name: string;                              // content author (editor/admin) display name
  role: "editor" | "admin" | "citizen";
  proposedBy?: string;                       // user who proposed it (UGC)
  proposerId?: string;                       // sender id kept for moderation even if anonymous
  anonymous?: boolean;                       // hide proposer name publicly
}

// Editor/UGC publication created through the content editor. Stored locally
// (per-user) first; backend persistence comes later.
export interface Article {
  id: string;
  kind: ArticleKind;
  title: string;
  summary: string;
  bodyHtml: string;
  cover: string;
  video?: string;
  gallery?: string[];
  tags: string[];
  category: string;
  specialization?: string;
  audience?: string;
  source?: string;
  sourceUrl?: string;
  /** P6: опциональная привязка к Source.id из OFFICIAL_SOURCES. */
  sourceIds?: string[];
  status: ArticleStatus;
  author: AuthorMeta;
  date: string;                              // yyyy-mm-dd publication date
  views: number;
  updatedAt: string;                         // ISO timestamp
  reported?: boolean;                        // editor flagged it for admin review
}

// P7: каркас «Экстремистский контент». Контент НЕ заполняется — только типы
// и константы. Любая запись ОБЯЗАНА иметь source_url (валидируется).
export type ExtremistCategory = "registry" | "news" | "explanation";
export type ExtremistStatus = "draft" | "published";
export type ExtremistContentType =
  | "social"
  | "channels"
  | "media"
  | "persons"
  | "organizations"
  | "music"
  | "other";

export interface ExtremistEntry {
  id: string;
  title: string;
  category: ExtremistCategory;
  sourceUrl: string;                         // обязателен, валидируется на сервере
  sourceName: string;
  includedAt?: string;                       // ISO date
  lastCheckedAt?: string;                    // ISO date
  shortDescription: string;
  coverUrl?: string;
  mediaUrls?: string[];
  attachmentUrls?: string[];
  contentTypes: ExtremistContentType[];      // мульти-выбор (filters_json)
  status: ExtremistStatus;
  createdAt: string;
  updatedAt: string;
}

export const EXTREMIST_CATEGORY_LABEL: Record<ExtremistCategory, string> = {
  registry: "Реестр",
  news: "Новость",
  explanation: "Разъяснение",
};

export const EXTREMIST_STATUS_LABEL: Record<ExtremistStatus, string> = {
  draft: "Черновик",
  published: "Опубликовано",
};

export const EXTREMIST_CONTENT_TYPE_LABEL: Record<ExtremistContentType, string> = {
  social: "Соцсети",
  channels: "Каналы",
  media: "Медиа",
  persons: "Лица",
  organizations: "Организации",
  music: "Музыка",
  other: "Другое",
};
