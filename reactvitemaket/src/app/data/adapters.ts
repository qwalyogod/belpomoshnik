import type {
  AdminScenarioRow,
  AppNotification,
  CategoryId,
  ContentTag,
  Difficulty,
  DocumentRef,
  Institution,
  LegalUpdate,
  OfficialSource,
  Problem,
  Scenario,
  Stage,
  Task,
  TaskKind,
  UserAddress,
  UserDocument,
  UserDocumentStatus,
  UserDocumentType,
  UserProfile,
  UserNote,
  UserSituation,
  SituationStatus,
  TaxObligation,
  UtilityAccount,
  UtilityPayment,
  UtilityServiceType,
  Article,
  ArticleKind,
  ArticleStatus,
  CustomField,
} from "./types";
import { API_BASE_URL } from "../services/api";

type LooseRecord = Record<string, unknown>;

/** v1.2: бэк возвращает относительный путь аватара (/uploads/avatars/...).
 *  Для <img src> нужен абсолютный URL на бэкенд. data:/http(s) — отдаём как есть. */
function absoluteAvatarUrl(value: unknown): string | undefined {
  const raw = typeof value === "string" ? value.trim() : "";
  if (!raw) return undefined;
  if (/^(data:|https?:\/\/|blob:)/i.test(raw)) return raw;
  return `${API_BASE_URL}${raw.startsWith("/") ? raw : `/${raw}`}`;
}

function text(value: unknown, fallback = "") {
  return typeof value === "string" && value.trim() ? value : fallback;
}

function identifier(value: unknown, fallback = "") {
  if (typeof value === "string" && value.trim()) return value;
  if (typeof value === "number") return String(value);
  return fallback;
}

function bool(value: unknown, fallback = false) {
  return typeof value === "boolean" ? value : fallback;
}

function numberValue(value: unknown, fallback = 0) {
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}

function stringList(value: unknown): string[] {
  if (Array.isArray(value)) {
    return value.map(item => text(item)).filter(Boolean);
  }
  if (typeof value === "string" && value.trim()) {
    return [value.trim()];
  }
  return [];
}

function category(value: unknown): CategoryId {
  const allowed: CategoryId[] = ["documents", "family", "work", "business", "housing", "taxes", "health", "auto"];
  if (allowed.includes(value as CategoryId)) return value as CategoryId;
  const normalized = text(value).toLowerCase();
  if (normalized.includes("сем")) return "family";
  if (normalized.includes("работ")) return "work";
  if (normalized.includes("бизнес") || normalized.includes("ип")) return "business";
  if (normalized.includes("жкх") || normalized.includes("жиль")) return "housing";
  if (normalized.includes("налог")) return "taxes";
  if (normalized.includes("здоров") || normalized.includes("мед")) return "health";
  if (normalized.includes("авто")) return "auto";
  if (normalized.includes("документ") || normalized.includes("паспорт")) return "documents";
  return "documents";
}

function difficulty(value: unknown): Difficulty {
  return value === "medium" || value === "hard" ? value : "easy";
}

function documentType(value: unknown): UserDocumentType {
  const allowed: UserDocumentType[] = ["passport", "driver", "medical", "birth", "housing", "receipt", "other"];
  return allowed.includes(value as UserDocumentType) ? (value as UserDocumentType) : "other";
}

function documentStatus(value: unknown): UserDocumentStatus {
  if (value === "expired" || value === "expiring") return value;
  return "active";
}

function situationStatus(value: unknown, progress: unknown): SituationStatus {
  const normalized = text(value).toLowerCase();
  const percent = numberValue(progress, 0);
  if (normalized.includes("заверш") || normalized === "done" || percent >= 100) return "done";
  if (normalized.includes("не нач") || normalized === "not_started" || percent <= 0) return "not_started";
  return "in_progress";
}

function comparable(value: unknown) {
  return text(value).trim().toLowerCase().replace(/\s+/g, " ");
}

function computedDocumentStatus(expiry: string, fallback: unknown): UserDocumentStatus {
  if (!expiry) return documentStatus(fallback);
  const expiryDate = new Date(`${expiry}T00:00:00`);
  if (Number.isNaN(expiryDate.getTime())) return documentStatus(fallback);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const diffDays = Math.ceil((expiryDate.getTime() - today.getTime()) / 86400000);
  if (diffDays < 0) return "expired";
  if (diffDays <= 60) return "expiring";
  return "active";
}

function source(input: unknown): OfficialSource {
  const data = (input && typeof input === "object" ? input : {}) as LooseRecord;
  return {
    id: identifier(data.id, text(data.url, "source")),
    title: text(data.title, "Официальный источник"),
    url: text(data.url, "https://portal.gov.by"),
    description: text(data.description, "Источник требует проверки при финальном наполнении."),
    checkedAt: text(data.checkedAt || data.last_checked_at, "") || undefined,
  };
}

export function adaptDocumentRef(input: unknown): DocumentRef {
  const data = (input && typeof input === "object" ? input : {}) as LooseRecord;
  return {
    id: identifier(data.id, text(data.title || data.name, "document")),
    name: text(data.name || data.title, "Документ"),
    required: bool(data.required ?? data.is_required, true),
    note: text(data.note || data.description, "") || undefined,
  };
}

export function adaptContentTag(input: unknown): ContentTag {
  const data = (input && typeof input === "object" ? input : {}) as LooseRecord;
  return {
    id: identifier(data.id, text(data.slug || data.name, "tag")),
    name: text(data.name, "Тег"),
    slug: text(data.slug, identifier(data.id, "tag")),
    description: text(data.description, ""),
    color: text(data.color, ""),
    isActive: bool(data.is_active ?? data.isActive, true),
  };
}

export function adaptInstitution(input: unknown): Institution {
  const data = (input && typeof input === "object" ? input : {}) as LooseRecord;
  return {
    id: identifier(data.id, text(data.title || data.name, "institution")),
    name: text(data.name || data.title, "Учреждение"),
    address: text(data.address),
    hours: text(data.hours || data.working_hours, "") || undefined,
    phone: text(data.phone, "") || undefined,
    email: text(data.email, "") || undefined,
    websiteUrl: text(data.websiteUrl || data.website_url || data.website, "") || undefined,
    type: text(data.type || data.institution_type, "") || undefined,
    region: text(data.region, "") || undefined,
    district: text(data.district, "") || undefined,
    city: text(data.city, "") || undefined,
    settlement: text(data.settlement, "") || undefined,
    services: stringList(data.services),
    tags: stringList(data.tags),
    relatedScenarioCategories: stringList(data.relatedScenarioCategories || data.related_scenario_categories),
    relatedScenarios: stringList(data.relatedScenarios || data.related_scenarios),
    sourceIds: stringList(data.sourceIds || data.source_ids),
    sourceUrls: stringList(data.sourceUrls || data.source_urls),
    lastCheckedAt: text(data.lastCheckedAt || data.last_checked_at, "") || undefined,
    confidence: text(data.confidence, "") || undefined,
    notes: text(data.notes, "") || undefined,
    isActive: bool(data.isActive ?? data.is_active, true),
  };
}

function taskKind(value: unknown): TaskKind {
  const normalized = text(value).toLowerCase();
  if (normalized === "visit" || normalized === "visit_office") return "visit";
  if (normalized === "online_request" || normalized === "form") return "form";
  if (normalized === "document_prepare" || normalized === "document") return "document";
  if (normalized === "payment") return "payment";
  if (normalized === "waiting" || normalized === "wait") return "wait";
  return "form";
}

function collectUnique<T extends { id: string }>(items: T[]) {
  return Array.from(new Map(items.map(item => [item.id, item])).values());
}

export function adaptScenario(input: LooseRecord): Scenario {
  const dependencies = Array.isArray(input.dependencies) ? input.dependencies as LooseRecord[] : [];
  const blockedBy = (stepId: string) =>
    dependencies
      .filter(dep => identifier(dep.step_id) === stepId)
      .map(dep => identifier(dep.depends_on_step_id))
      .filter(Boolean);

  const stages: Stage[] = Array.isArray(input.stages)
    ? (input.stages as LooseRecord[]).map(stage => ({
        id: identifier(stage.id, text(stage.title, "stage")),
        title: text(stage.title, "Этап"),
        description: text(stage.description, "") || undefined,
        tasks: Array.isArray(stage.steps)
          ? (stage.steps as LooseRecord[]).map((step): Task => {
              const stepId = identifier(step.id, text(step.title, "task"));
              const authority = (step.authority && typeof step.authority === "object" ? step.authority : undefined) as LooseRecord | undefined;
              const deadline = (step.deadline && typeof step.deadline === "object" ? step.deadline : undefined) as LooseRecord | undefined;
              return {
                id: stepId,
                title: text(step.title, "Задача"),
                kind: taskKind(step.kind || step.action_type),
                durationHint: text(step.durationHint || deadline?.title || deadline?.description, "") || undefined,
                blockedBy: blockedBy(stepId),
                documents: Array.isArray(step.documents)
                  ? (step.documents as LooseRecord[]).map(doc => identifier(doc.id)).filter(Boolean)
                  : undefined,
                institutionId: authority ? identifier(authority.id) : undefined,
              };
            })
          : [],
      }))
    : [];

  const stepDocuments = stages.flatMap(stage =>
    stage.tasks.flatMap(task => {
      const rawStage = Array.isArray(input.stages)
        ? (input.stages as LooseRecord[]).find(item => identifier(item.id, text(item.title)) === stage.id)
        : undefined;
      const rawStep = Array.isArray(rawStage?.steps)
        ? (rawStage.steps as LooseRecord[]).find(item => identifier(item.id, text(item.title)) === task.id)
        : undefined;
      return Array.isArray(rawStep?.documents) ? (rawStep.documents as unknown[]).map(adaptDocumentRef) : [];
    })
  );

  const stepInstitutions = stages.flatMap(stage =>
    stage.tasks.flatMap(task => {
      const rawStage = Array.isArray(input.stages)
        ? (input.stages as LooseRecord[]).find(item => identifier(item.id, text(item.title)) === stage.id)
        : undefined;
      const rawStep = Array.isArray(rawStage?.steps)
        ? (rawStage.steps as LooseRecord[]).find(item => identifier(item.id, text(item.title)) === task.id)
        : undefined;
      return rawStep?.authority ? [adaptInstitution(rawStep.authority)] : [];
    })
  );
  const computedTaskCount = stages.reduce((total, stage) => total + stage.tasks.length, 0);

  return {
    id: text(input.slug, identifier(input.id, "scenario")),
    title: text(input.title, "Сценарий"),
    category: category(input.category),
    shortDescription: text(input.shortDescription || input.short_description),
    longDescription: text(input.longDescription || input.description),
    forWhom: text(input.forWhom || input.target_audience, "Граждане Республики Беларусь."),
    estimatedTime: text(input.estimatedTime || input.estimated_duration, "требует уточнения"),
    difficulty: difficulty(input.difficulty || input.difficulty_level),
    stageCount: numberValue(input.stageCount ?? input.stage_count, stages.length),
    taskCount: numberValue(input.taskCount ?? input.task_count, computedTaskCount),
    stages,
    documents: collectUnique([
      ...(Array.isArray(input.documents) ? input.documents.map(adaptDocumentRef) : []),
      ...stepDocuments,
    ]),
    institutions: Array.isArray(input.institutions || input.authorities)
      ? collectUnique(((input.institutions || input.authorities) as unknown[]).map(adaptInstitution))
      : collectUnique(stepInstitutions),
    sources: Array.isArray(input.sources || input.source_references)
      ? ((input.sources || input.source_references) as unknown[]).map(source)
      : [],
    relatedIds: Array.isArray(input.relatedIds || input.related_scenarios)
      ? ((input.relatedIds || input.related_scenarios) as LooseRecord[]).map(item =>
          typeof item === "string" ? item : text(item.related_scenario_slug, identifier(item.related_scenario_id))
        ).filter(Boolean)
      : [],
  };
}

export function adaptProblem(input: LooseRecord): Problem {
  return {
    id: text(input.slug, identifier(input.id, "problem")),
    title: text(input.title, "Проблема"),
    category: category(input.category || input.title || input.description),
    shortDescription: text(input.shortDescription || input.short_description),
    whatToDoNow: text(input.whatToDoNow || input.what_to_do_now),
    steps: Array.isArray(input.steps) ? (input.steps as Problem["steps"]) : [],
    documents: Array.isArray(input.documents) ? (input.documents as string[]) : [],
    deadlines: Array.isArray(input.deadlines) ? (input.deadlines as string[]) : [],
    institutions: Array.isArray(input.institutions) ? (input.institutions as string[]) : [],
    mistakes: Array.isArray(input.mistakes) ? (input.mistakes as string[]) : [],
  };
}

export function adaptUserDocument(input: LooseRecord): UserDocument {
  const expiresAt = text(input.expiresAt || input.expires_at || input.expiry_date, "") || undefined;
  // v0.4: парсим custom_fields_json (если бэк прислал) или принимаем массивом
  let customFields: CustomField[] | undefined;
  const rawCustom = input.customFields ?? input.custom_fields_json;
  if (Array.isArray(rawCustom)) {
    customFields = rawCustom.filter(
      (item): item is CustomField =>
        item && typeof item === "object" && typeof item.name === "string" && typeof item.value === "string",
    );
  } else if (typeof rawCustom === "string" && rawCustom.trim()) {
    try {
      const parsed = JSON.parse(rawCustom);
      if (Array.isArray(parsed)) {
        customFields = parsed.filter(
          (item): item is CustomField =>
            item && typeof item === "object" && typeof item.name === "string" && typeof item.value === "string",
        );
      }
    } catch {
      customFields = undefined;
    }
  }
  // Промпт 1: scan metadata. Поддерживаем оба формата (snake_case от FastAPI и
  // camelCase для будущих изменений).
  let scan: UserDocument["scan"];
  const rawScan = (input.scan ?? null) as LooseRecord | null;
  if (rawScan && typeof rawScan === "object" && (rawScan.has_scan || rawScan.hasScan)) {
    scan = {
      hasScan: true,
      mimeType: text(rawScan.mime_type || rawScan.mimeType, "") || undefined,
      size: typeof rawScan.size === "number" ? rawScan.size : undefined,
      originalFilename: text(rawScan.original_filename || rawScan.originalFilename, "") || undefined,
      uploadedAt: text(rawScan.uploaded_at || rawScan.uploadedAt, "") || undefined,
      downloadUrl: text(rawScan.download_url || rawScan.downloadUrl, "") || undefined,
    };
  }
  return {
    id: identifier(input.id, "document"),
    type: documentType(input.type || input.doc_type || input.document_type),
    title: text(input.title || input.name, "Документ"),
    number: text(input.number || input.document_number, ""),
    issuedAt: text(input.issuedAt || input.issued_at || input.issued_date, "") || undefined,
    issuedBy: text(input.issuedBy || input.issued_by, "") || undefined,
    comment: text(input.comment, "") || undefined,
    expiresAt,
    status: computedDocumentStatus(expiresAt ?? "", input.status),
    customFields: customFields && customFields.length > 0 ? customFields : undefined,
    encryptedAtRest: Boolean(input.encrypted_at_rest ?? input.encryptedAtRest ?? true),
    scan,
  };
}

/** v1.1 (P4): адаптер пользовательской заметки. */
export function adaptUserNote(input: LooseRecord): UserNote {
  return {
    id: identifier(input.id, "note"),
    text: text(input.text, ""),
    category: text(input.category, "Общее") as UserNote["category"],
    reminderAt: text(input.reminderAt || input.reminder_at, "") || undefined,
    done: Boolean(input.done),
    createdAt: text(input.createdAt || input.created_at, "") || new Date().toISOString(),
  };
}

/** v1.1 (P4): payload заметки для PUT/POST. reminder_at приводим к yyyy-mm-dd. */
export function userNotePayload(note: Partial<UserNote>): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  if (note.text !== undefined) out.text = note.text;
  if (note.category !== undefined) out.category = note.category;
  if (note.done !== undefined) out.done = note.done;
  if (note.reminderAt !== undefined) {
    out.reminder_at = note.reminderAt ? note.reminderAt.slice(0, 10) : "";
  }
  return out;
}

function findScenarioTask(scenario: Scenario | undefined, backendTask: LooseRecord) {
  if (!scenario) return undefined;
  const taskTitle = comparable(backendTask.title);
  const stageTitle = comparable(backendTask.stage_title || backendTask.stageTitle);
  if (!taskTitle) return undefined;

  if (stageTitle) {
    const stage = scenario.stages.find(item => comparable(item.title) === stageTitle);
    const task = stage?.tasks.find(item => comparable(item.title) === taskTitle);
    if (task) return task;
  }

  return scenario.stages.flatMap(stage => stage.tasks).find(item => comparable(item.title) === taskTitle);
}

export function adaptUserSituation(input: LooseRecord, scenarios: Scenario[]): UserSituation {
  const scenarioId = identifier(input.scenarioId || input.template_id || input.templateId, "");
  const scenario = scenarios.find(item => item.id === scenarioId);
  const tasks = Array.isArray(input.tasks) ? input.tasks as LooseRecord[] : [];
  const backendTaskIds: Record<string, string> = {};
  const completedTaskIds: string[] = [];

  tasks.forEach(task => {
    const scenarioTask = findScenarioTask(scenario, task);
    if (!scenarioTask) return;
    const backendId = identifier(task.id, "");
    if (backendId) backendTaskIds[scenarioTask.id] = backendId;
    if (bool(task.completed, false)) completedTaskIds.push(scenarioTask.id);
  });

  const fallbackStartedAt = new Date().toISOString().slice(0, 10);

  return {
    id: identifier(input.id, "situation"),
    scenarioId,
    status: situationStatus(input.status, input.progress),
    startedAt: text(input.startedAt || input.started_at || input.created_at, fallbackStartedAt),
    completedTaskIds,
    backendTaskIds,
    notes: input.notes && typeof input.notes === "object" ? input.notes as Record<string, string> : {},
  };
}

export function adaptTax(input: LooseRecord): TaxObligation {
  return {
    id: identifier(input.id, "tax"),
    title: text(input.title, "Налог"),
    userType: text(input.user_type || input.userType, "individual"),
    deadline: text(input.deadline, "") || undefined,
    amount: numberValue(input.amount, 0),
    status: text(input.status, "Предстоит"),
    period: text(input.period, "") || undefined,
    comment: text(input.comment, "") || undefined,
    receiptPath: text(input.receipt_path || input.receiptPath, "") || undefined,
    // Промпт 2: расширенные поля.
    taxType: (text(input.tax_type || input.taxType, "other") as TaxObligation["taxType"]) || undefined,
    source: (text(input.source, "") as TaxObligation["source"]) || undefined,
    recipient: text(input.recipient, "") || undefined,
    unp: text(input.unp, "") || undefined,
    noticeNumber: text(input.notice_number || input.noticeNumber, "") || undefined,
    paymentCode: text(input.payment_code || input.paymentCode, "") || undefined,
    paidAt: text(input.paid_at || input.paidAt, "") || undefined,
    externalUrl: text(input.external_url || input.externalUrl, "") || undefined,
    helpText: text(input.help_text || input.helpText, "") || undefined,
  };
}

export function taxPayload(tax: Partial<TaxObligation>): Record<string, unknown> {
  return {
    title: tax.title ?? "",
    user_type: tax.userType ?? "individual",
    deadline: tax.deadline ?? "",
    amount: tax.amount ?? 0,
    receipt_path: tax.receiptPath ?? "",
    status: tax.status ?? "Предстоит",
    period: tax.period ?? "",
    comment: tax.comment ?? "",
    tax_type: tax.taxType ?? "other",
    source: tax.source ?? "manual",
    recipient: tax.recipient ?? "",
    unp: tax.unp ?? "",
    notice_number: tax.noticeNumber ?? "",
    payment_code: tax.paymentCode ?? "",
    paid_at: tax.paidAt ?? "",
    external_url: tax.externalUrl ?? "",
    help_text: tax.helpText ?? "",
  };
}

export function adaptUtilityPayment(input: LooseRecord, accountId = ""): UtilityPayment {
  // Промпт 2: breakdown приходит как JSON-строка (или массив для будущей версии API).
  let breakdown: UtilityPayment["breakdown"];
  const rawBreakdown = input.breakdown ?? input.breakdown_json;
  if (Array.isArray(rawBreakdown)) {
    breakdown = rawBreakdown as UtilityPayment["breakdown"];
  } else if (typeof rawBreakdown === "string" && rawBreakdown.trim()) {
    try {
      const parsed = JSON.parse(rawBreakdown);
      if (Array.isArray(parsed)) breakdown = parsed as UtilityPayment["breakdown"];
    } catch {
      breakdown = undefined;
    }
  }
  return {
    id: identifier(input.id, "upay"),
    accountId: identifier(input.account_id || input.accountId, accountId),
    period: text(input.period, ""),
    readingsDate: text(input.readings_date || input.readingsDate, "") || undefined,
    paymentDate: text(input.payment_date || input.paymentDate, "") || undefined,
    amount: numberValue(input.amount, 0),
    status: text(input.status, "Ожидает"),
    readingsDeadline: text(input.readings_deadline || input.readingsDeadline, "") || undefined,
    paymentDeadline: text(input.payment_deadline || input.paymentDeadline, "") || undefined,
    comment: text(input.comment, "") || undefined,
    breakdown,
    source: (text(input.source, "") as UtilityPayment["source"]) || undefined,
    receiptPath: text(input.receipt_path || input.receiptPath, "") || undefined,
  };
}

export function utilityPaymentPayload(payment: Partial<UtilityPayment>): Record<string, unknown> {
  return {
    period: payment.period ?? "",
    readings_date: payment.readingsDate ?? "",
    payment_date: payment.paymentDate ?? "",
    amount: payment.amount ?? 0,
    status: payment.status ?? "Ожидает",
    readings_deadline: payment.readingsDeadline ?? "",
    payment_deadline: payment.paymentDeadline ?? "",
    comment: payment.comment ?? "",
    breakdown_json: payment.breakdown ? JSON.stringify(payment.breakdown) : "[]",
    source: payment.source ?? "manual",
    receipt_path: payment.receiptPath ?? "",
  };
}

export function adaptUtilityAccount(input: LooseRecord): UtilityAccount {
  const id = identifier(input.id, "util");
  return {
    id,
    address: text(input.address, ""),
    accountNumber: text(input.account_number || input.accountNumber, ""),
    provider: text(input.provider, ""),
    payments: Array.isArray(input.payments)
      ? (input.payments as LooseRecord[]).map(p => adaptUtilityPayment(p, id))
      : [],
    // Промпт 2: расширенные поля.
    label: text(input.label, "") || undefined,
    serviceTypes: Array.isArray(input.service_types || input.serviceTypes)
      ? ((input.service_types || input.serviceTypes) as string[]).filter((s): s is UtilityServiceType =>
          ["electricity", "cold_water", "hot_water", "gas", "heating", "maintenance", "capital_repair", "waste", "other"].includes(s),
        )
      : undefined,
    payerName: text(input.payer_name || input.payerName, "") || undefined,
    manualMode: input.manual_mode === undefined && input.manualMode === undefined ? undefined : Boolean(input.manual_mode ?? input.manualMode),
    lastSyncNote: text(input.last_sync_note || input.lastSyncNote, "") || undefined,
  };
}

export function utilityAccountPayload(account: Partial<UtilityAccount>): Record<string, unknown> {
  return {
    address: account.address ?? "",
    account_number: account.accountNumber ?? "",
    provider: account.provider ?? "",
    label: account.label ?? "",
    service_types: account.serviceTypes ?? [],
    payer_name: account.payerName ?? "",
    manual_mode: account.manualMode ?? true,
    last_sync_note: account.lastSyncNote ?? "",
  };
}

// Промпт 2: заявки 115.
export function adaptUtilityRequest(input: LooseRecord): import("./types").UtilityRequest {
  return {
    id: identifier(input.id, "ureq"),
    accountId: text(input.account_id || input.accountId, "") || undefined,
    address: text(input.address, "") || undefined,
    title: text(input.title, "Заявка"),
    category: (text(input.category, "other") as import("./types").UtilityRequestCategory),
    description: text(input.description, "") || undefined,
    status: (text(input.status, "draft") as import("./types").UtilityRequestStatus),
    createdAt: text(input.created_at || input.createdAt, "") || undefined,
    updatedAt: text(input.updated_at || input.updatedAt, "") || undefined,
    externalNumber: text(input.external_number || input.externalNumber, "") || undefined,
    externalUrl: text(input.external_url || input.externalUrl, "") || undefined,
  };
}

export function utilityRequestPayload(req: Partial<import("./types").UtilityRequest>): Record<string, unknown> {
  return {
    account_id: req.accountId || null,
    address: req.address ?? "",
    title: req.title ?? "",
    category: req.category ?? "other",
    description: req.description ?? "",
    status: req.status ?? "draft",
    external_number: req.externalNumber ?? "",
    external_url: req.externalUrl ?? "",
    target_service: "",
  };
}

export function adaptAdminScenarioRow(input: LooseRecord): AdminScenarioRow {
  const rawStatus = text(input.status).toLowerCase();
  const status: AdminScenarioRow["status"] =
    rawStatus === "published"
      ? "published"
      : input.content_verified_at
        ? "review"
        : "draft";
  return {
    id: identifier(input.id, text(input.slug, "scenario")),
    title: text(input.title, "Сценарий"),
    category: category(input.category),
    status,
    taskCount: numberValue(input.task_count ?? input.taskCount, 0),
  };
}

export function adaptUserProfile(input: LooseRecord, fallback: UserProfile): UserProfile {
  // v1.1 (P4): бэк возвращает addresses как JSON-строку или массив.
  // Парсим в обоих случаях и валидируем по схеме UserAddress.
  const rawAddresses = input.addresses ?? input.addresses_json;
  let parsedAddresses: unknown = rawAddresses;
  if (typeof parsedAddresses === "string" && parsedAddresses.trim()) {
    try {
      parsedAddresses = JSON.parse(parsedAddresses);
    } catch {
      parsedAddresses = [];
    }
  }
  const addresses: UserAddress[] = Array.isArray(parsedAddresses)
    ? (parsedAddresses as LooseRecord[])
        .filter((item): item is LooseRecord => !!item && typeof item === "object")
        .map((item) => ({
          id: text(item.id, ""),
          label: text(item.label, ""),
          region: text(item.region, ""),
          district: text(item.district, ""),
          city: text(item.city, ""),
          street: text(item.street, ""),
          isPrimary: bool(item.isPrimary, false),
        }))
        .filter((item) => item.id)
    : fallback.addresses ?? [];
  return {
    ...fallback,
    name: text(input.name, fallback.name),
    email: text(input.email, fallback.email),
    region: text(input.region, fallback.region),
    city: text(input.city, fallback.city),
    district: text(input.district, fallback.district),
    address: text(input.address, fallback.address ?? "") || undefined,
    employment: text(input.employment_status || input.employment, fallback.employment),
    flags: {
      hasChildren: bool(input.has_children, fallback.flags.hasChildren),
      hasCar: bool(input.has_car, fallback.flags.hasCar),
      homeowner: bool(input.owns_property, fallback.flags.homeowner),
      tenant: bool(input.is_renter, fallback.flags.tenant),
    },
    interests: Array.isArray(input.interest_tags)
      ? (input.interest_tags as unknown[]).map(item => String(item)).filter(Boolean)
      : fallback.interests,
    // v1.2: аватар теперь хранится на бэке (users.avatar_url) и приходит как
    // относительный путь — превращаем в абсолютный URL. Если ключ присутствует,
    // доверяем бэку (пустая строка = аватар удалён → undefined). Если ключа нет
    // (офлайн/частичный ответ) — оставляем локальное значение.
    avatarDataUrl: "avatar_url" in input ? absoluteAvatarUrl(input.avatar_url) : fallback.avatarDataUrl,
    addresses,
    preferredSourceIds: Array.isArray(fallback.preferredSourceIds) ? fallback.preferredSourceIds : [],
  };
}

export function userProfilePayload(profile: UserProfile): Record<string, unknown> {
  return {
    name: profile.name,
    city: profile.city,
    region: profile.region,
    district: profile.district,
    address: profile.address ?? "",
    employment_status: profile.employment,
    has_children: profile.flags.hasChildren,
    owns_property: profile.flags.homeowner,
    has_car: profile.flags.hasCar,
    is_renter: profile.flags.tenant,
    interest_tags: profile.interests,
    // v1.1 (P4): адреса отправляем как массив — бэк нормализует и
    // сериализует в addresses_json.
    addresses: profile.addresses ?? [],
  };
}

function notificationKind(value: unknown): AppNotification["kind"] {
  const normalized = text(value).toLowerCase();
  if (normalized.includes("document") || normalized.includes("документ")) return "document_expiring";
  if (normalized.includes("legal") || normalized.includes("law") || normalized.includes("закон")) return "legal_update";
  if (normalized.includes("step") || normalized.includes("done")) return "step_done";
  return "task_due";
}

export function adaptNotification(input: LooseRecord): AppNotification {
  const route = text(input.route);
  const routeParts = route.replace(/^\//, "").split("/").filter(Boolean);
  return {
    id: identifier(input.id, "notification"),
    kind: notificationKind(input.notification_type || input.kind),
    title: text(input.title, "Уведомление"),
    body: text(input.description || input.body, "") || undefined,
    createdAt: text(input.due_date || input.createdAt || input.created_at, ""),
    read: bool(input.is_read ?? input.read, false),
    link: routeParts.length > 0 ? { page: routeParts[0], id: routeParts[1] } : undefined,
  };
}

export function adaptLegalUpdate(input: LooseRecord): LegalUpdate {
  return {
    id: identifier(input.id, "legal-update"),
    category: category(input.category || input.title || input.description),
    title: text(input.title, "Изменение законодательства"),
    summary: text(input.summary || input.description),
    bodyHtml: text(input.bodyHtml || input.body_html),
    whoAffected: text(input.whoAffected || input.who_affected, "Граждане Республики Беларусь."),
    whatChanged: text(input.whatChanged || input.what_changed || input.description),
    whatToDo: text(input.whatToDo || input.what_to_do, "Сверить информацию с официальным источником."),
    effectiveDate: text(input.effectiveDate || input.effective_date || input.update_date),
    source: source(input.source || { url: input.source_url }),
    priority: bool(input.priority),
    matchesProfile: bool(input.matchesProfile || input.matches_profile),
  };
}

function stringArray(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((x): x is string => typeof x === "string") : [];
}

export function adaptArticle(raw: LooseRecord): Article {
  const author = (raw.author ?? {}) as LooseRecord;
  return {
    id: identifier(raw.id),
    kind: (text(raw.kind, "news") as ArticleKind),
    title: text(raw.title),
    summary: text(raw.summary),
    bodyHtml: text(raw.body_html),
    cover: text(raw.cover),
    video: text(raw.video),
    gallery: stringArray(raw.gallery),
    tags: stringArray(raw.tags),
    category: text(raw.category),
    specialization: text(raw.specialization),
    audience: text(raw.audience, "all"),
    source: text(raw.source),
    sourceUrl: text(raw.source_url),
    status: (text(raw.status, "draft") as ArticleStatus),
    author: {
      name: text(author.name),
      role: (text(author.role, "editor") as Article["author"]["role"]),
      proposedBy: text(author.proposed_by) || undefined,
      proposerId: author.proposer_id != null ? identifier(author.proposer_id) : undefined,
      anonymous: bool(author.anonymous),
    },
    date: text(raw.date),
    views: numberValue(raw.views),
    updatedAt: text(raw.updated_at) || new Date().toISOString(),
    reported: bool(raw.reported),
  };
}
