// Domain types — single source of truth. Future API responses will match these.

export type Role = "guest" | "citizen" | "editor" | "admin";
export type Lang = "ru" | "be" | "en";

export interface AppUser {
  id: string;
  name: string;
  email: string;
  role: Role;
  region?: string;
  city?: string;
  district?: string;
  password?: string;
  isTestAccount?: boolean;
}

export type CategoryId = "documents" | "family" | "work" | "business" | "housing" | "taxes" | "health" | "auto";

export interface Category {
  id: CategoryId;
  name: string;
}

export type Difficulty = "easy" | "medium" | "hard";

export interface OfficialSource {
  id: string;
  title: string;
  url: string;
  description: string;
  checkedAt?: string;       // ISO date, or undefined → "требует проверки"
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
  notes: Record<string, string>; // taskId -> note
}

export type UserDocumentStatus = "active" | "expiring" | "expired";
export type UserDocumentType = "passport" | "driver" | "medical" | "birth" | "housing" | "receipt" | "other";

export interface UserDocument {
  id: string;
  type: UserDocumentType;
  title: string;
  number: string;             // raw — UI masks it
  issuedAt?: string;
  expiresAt?: string;
  status: UserDocumentStatus;
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
  whoAffected: string;
  whatChanged: string;
  whatToDo: string;
  effectiveDate: string;       // ISO
  source: OfficialSource;
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
  status: ArticleStatus;
  author: AuthorMeta;
  date: string;                              // yyyy-mm-dd publication date
  views: number;
  updatedAt: string;                         // ISO timestamp
  reported?: boolean;                        // editor flagged it for admin review
}
