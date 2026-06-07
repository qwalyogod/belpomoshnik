import { createContext, useContext, useMemo, useRef, useState, ReactNode, useCallback, useEffect } from "react";
import {
  Role, Lang, Scenario, UserSituation, UserDocument, AppNotification, LegalUpdate,
  UserProfile, Settings, UserDocumentType, Problem, DocumentRef, Institution, AppUser,
  AdminScenarioRow, UtilityAccount, UtilityPayment, TaxObligation, Article, Category,
  UserAddress, UserNote, NoteCategory,
} from "./types";
import {
  CATEGORIES, SCENARIOS, INITIAL_SITUATIONS, INITIAL_DOCUMENTS, INITIAL_NOTIFICATIONS,
  LEGAL_UPDATES, INITIAL_PROFILE, INITIAL_SETTINGS, INITIAL_FAVORITES, PROBLEMS,
  INITIAL_UTILITY_ACCOUNTS, INITIAL_TAXES
} from "./mock";
import { adaptAdminScenarioRow, adaptArticle, adaptDocumentRef, adaptInstitution, adaptLegalUpdate, adaptNotification, adaptProblem, adaptScenario, adaptTax, adaptUserDocument, adaptUserNote, adaptUserProfile, adaptUserSituation, adaptUtilityAccount, adaptUtilityPayment, taxPayload, userNotePayload, userProfilePayload, utilityAccountPayload, utilityPaymentPayload } from "./adapters";
import { apiClient, API_BASE_URL, type AuthTokens } from "../services/api";
import { buildReminders } from "../services/reminders";
import { GEO_KEY, GEO_SEED, type GeoRegion } from "./geo";

function uid(prefix: string) {
  return `${prefix}-${Math.random().toString(36).slice(2, 9)}`;
}

export interface AdminUserRow { id: string; email: string; name: string; role: string; isActive: boolean; city: string; region: string }
export interface AuditLogRow { id: string; actor: string; roleId: string; eventType: string; action: string; status: string; createdAt: string }

type Store = {
  role: Role;
  setRole: (r: Role) => void;
  currentUser: AppUser;
  quickAccounts: AppUser[];
  isAuthenticated: boolean;
  signInAs: (userId: string) => void;
  signInWithEmail: (email: string, password: string) => boolean;
  registerUser: (payload: Pick<AppUser, "name" | "email" | "password" | "region" | "city">) => AppUser;
  signOut: () => void;
  resetSession: () => void;

  categories: typeof CATEGORIES;
  scenarios: Scenario[];
  problems: Problem[];
  legal: LegalUpdate[];
  publicDocuments: DocumentRef[];
  authorities: Institution[];
  publicContentStatus: "loading" | "api" | "fallback";
  publicContentError?: string;
  loadScenarioDetail: (id: string) => Promise<void>;

  admin: {
    scenarios: AdminScenarioRow[];
    status: "loading" | "api" | "fallback";
    users: AdminUserRow[];
    auditLogs: AuditLogRow[];
  };

  situations: UserSituation[];
  createSituation: (scenarioId: string) => string; // returns new id
  toggleTask: (situationId: string, taskId: string) => void;
  setNote: (situationId: string, taskId: string, note: string) => void;
  deleteSituation: (situationId: string) => void;

  documents: UserDocument[];
  addDocument: (doc: Omit<UserDocument, "id" | "status"> & { status?: UserDocument["status"] }) => void;
  updateDocument: (id: string, patch: Partial<UserDocument>) => void;
  deleteDocument: (id: string) => void;

  utilityAccounts: UtilityAccount[];
  addUtilityAccount: (account: Pick<UtilityAccount, "address" | "accountNumber" | "provider">) => void;
  updateUtilityAccount: (id: string, patch: Partial<UtilityAccount>) => void;
  deleteUtilityAccount: (id: string) => void;
  addUtilityPayment: (accountId: string, payment: Omit<UtilityPayment, "id" | "accountId">) => void;
  updateUtilityPayment: (accountId: string, paymentId: string, patch: Partial<UtilityPayment>) => void;
  deleteUtilityPayment: (accountId: string, paymentId: string) => void;

  taxes: TaxObligation[];
  addTax: (tax: Omit<TaxObligation, "id">) => void;
  updateTax: (id: string, patch: Partial<TaxObligation>) => void;
  deleteTax: (id: string) => void;

  // Editor / UGC publications (platform-wide, local-first).
  articles: Article[];
  addArticle: (article: Omit<Article, "id" | "views" | "updatedAt"> & Partial<Pick<Article, "id" | "views">>) => Article;
  updateArticle: (id: string, patch: Partial<Article>) => void;
  removeArticle: (id: string) => void;
  blockedSubmitters: string[];
  isSubmitterBlocked: (id: string) => boolean;
  toggleBlockedSubmitter: (id: string) => void;
  registerView: (id: string) => void;
  uploadMedia: (file: File) => Promise<string | null>;
  viewsDaily: { date: string; count: number }[];
  meId: string | null;

  favorites: string[];
  toggleFavorite: (scenarioId: string) => void;

  notifications: AppNotification[];
  markRead: (id: string) => void;
  markAllRead: () => void;
  unreadCount: number;

  profile: UserProfile;
  updateProfile: (patch: Partial<UserProfile>) => void;
  applyQuizResult: (correct: number, total: number) => void;

  // v1.1 (P4): пользовательские заметки (локальные).
  notes: UserNote[];
  addNote: (input: { text: string; category: NoteCategory; reminderAt?: string }) => void;
  updateNote: (id: string, patch: Partial<Pick<UserNote, "text" | "category" | "reminderAt" | "done">>) => void;
  toggleNote: (id: string) => void;
  removeNote: (id: string) => void;

  // v1.1 (P4): адреса пользователя (до 5 шт.). Внутри профиля, но
  // вынесенные методы для удобства UI.
  addAddress: (input: Omit<UserAddress, "id" | "isPrimary"> & { isPrimary?: boolean }) => void;
  updateAddress: (id: string, patch: Partial<UserAddress>) => void;
  removeAddress: (id: string) => void;

  // v1.1 (P4): предпочтения источников новостей (id из OFFICIAL_SOURCES).
  togglePreferredSource: (sourceId: string) => void;

  settings: Settings;
  updateSettings: (patch: Partial<Settings>) => void;
  setLang: (l: Lang) => void;

  // geography (regions → districts → city), editable by admin
  geo: GeoRegion[];
  addRegion: (name: string) => void;
  deleteRegion: (region: string) => void;
  updateRegion: (originalName: string, next: GeoRegion) => void;
  resetGeo: () => void;

  // legal updates, editable by admin
  addLegal: (item: Omit<LegalUpdate, "id">) => void;
  updateLegal: (id: string, patch: Partial<LegalUpdate>) => void;
  deleteLegal: (id: string) => void;
  resetLegal: () => void;

  // categories, editable by admin
  addCategory: (name: string) => void;
  updateCategory: (id: string, name: string) => void;
  deleteCategory: (id: string) => void;

  // institutions (authorities), editable by admin
  addAuthority: (item: Omit<Institution, "id">) => void;
  updateAuthority: (id: string, patch: Partial<Institution>) => void;
  deleteAuthority: (id: string) => void;

  // admin user management
  setAdminUserRole: (id: string, role: string) => void;
  setAdminUserActive: (id: string, active: boolean) => void;

  // helpers
  scenarioById: (id: string) => Scenario | undefined;
  problemById: (id: string) => Problem | undefined;
  situationByScenario: (scenarioId: string) => UserSituation | undefined;
  taskIsBlocked: (situation: UserSituation, taskId: string) => boolean;
  situationProgress: (situation: UserSituation) => number; // 0..100

  // Guest-guard: действия, требующие аккаунт, вызывают requireAccount().
  // Если пользователь — гость, инкрементится guestGuardSignal, и
  // GuestGuardBridge показывает модал «Войдите или зарегистрируйтесь».
  // Возвращает true, если действие разрешено; false — если заблокировано.
  requireAccount: () => boolean;
  guestGuardSignal: number;
  dismissGuestGuard: () => void;
};

const Ctx = createContext<Store | null>(null);

const GUEST_USER: AppUser = {
  id: "guest",
  name: "Гость",
  email: "",
  role: "guest",
};

const TEST_ACCOUNTS: AppUser[] = [
  {
    id: "test-citizen",
    name: "Тестовый гражданин",
    email: "citizen@test.local",
    role: "citizen",
    region: "Минская область",
    city: "Минск",
    district: "Центральный",
    password: "Test12345!",
    isTestAccount: true,
  },
  {
    id: "test-editor",
    name: "Тестовый редактор",
    email: "editor@test.local",
    role: "editor",
    region: "Минская область",
    city: "Минск",
    district: "Центральный",
    password: "Test12345!",
    isTestAccount: true,
  },
  {
    id: "test-admin",
    name: "Тестовый администратор",
    email: "admin@test.local",
    role: "admin",
    region: "Минская область",
    city: "Минск",
    district: "Центральный",
    password: "Test12345!",
    isTestAccount: true,
  },
];

const QUICK_ACCOUNTS_KEY = "belp.quickAccounts";
const CURRENT_USER_KEY = "belp.currentUserId";
const USER_DATA_PREFIX = "belp.userData.";
const ARTICLES_KEY = "belp.articles";
const BLOCKED_SUBMITTERS_KEY = "belp.blockedSubmitters";
const LEGAL_KEY = "belp.legal";
const CATEGORIES_KEY = "belp.categories";
const AUTHORITIES_KEY = "belp.authorities";

type PersistedUserData = {
  situations: UserSituation[];
  documents: UserDocument[];
  favorites: string[];
  notifications: AppNotification[];
  profile: UserProfile;
  settings: Settings;
  utilityAccounts: UtilityAccount[];
  taxes: TaxObligation[];
  // v1.1 (P4): пользовательские заметки — локальный массив, привязан
  // к пользователю через USER_DATA_PREFIX.
  notes: UserNote[];
};

function safeRead<T>(key: string, fallback: T): T {
  try {
    const raw = window.localStorage.getItem(key);
    return raw ? JSON.parse(raw) as T : fallback;
  } catch {
    return fallback;
  }
}

function safeWrite<T>(key: string, value: T) {
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // Local storage may be unavailable in some embedded browsers.
  }
}

function mergeById<T extends { id: string }>(base: T[], incoming: T[]) {
  const items = new Map(base.map(item => [item.id, item]));
  incoming.forEach(item => items.set(item.id, { ...items.get(item.id), ...item }));
  return Array.from(items.values());
}

// Settings are stored backend-side as an opaque JSON blob written by this same
// client, so a one-level-deep merge over the local defaults is enough.
function mergeSettings(base: Settings, incoming: Record<string, unknown>): Settings {
  const next: Record<string, unknown> = { ...base };
  for (const [key, value] of Object.entries(incoming)) {
    const current = (base as Record<string, unknown>)[key];
    if (value && typeof value === "object" && !Array.isArray(value) && current && typeof current === "object") {
      next[key] = { ...(current as Record<string, unknown>), ...(value as Record<string, unknown>) };
    } else if (value !== undefined && value !== null) {
      next[key] = value;
    }
  }
  return next as Settings;
}

type PublicListItem = { id: string; title: string; category?: string };

function publicKey(item: PublicListItem) {
  return `${item.category ?? "none"}::${item.title.trim().toLowerCase()}`;
}

function uniqueStrings(items: string[]) {
  return Array.from(new Set(items));
}

function isBackendNumericId(id: string) {
  return /^\d+$/.test(id);
}

function isBackendSituationId(id: string) {
  return /^[a-f0-9]{32}$/i.test(id);
}

function apiDocumentPayload(doc: Partial<UserDocument>) {
  return {
    title: doc.title ?? "Документ",
    doc_type: doc.type ?? "other",
    number: doc.number ?? "",
    issued_by: "",
    issued_date: doc.issuedAt ?? "",
    expiry_date: doc.expiresAt ?? "",
    is_sensitive: true,
    comment: "",
    scan_path: "",
  };
}

function apiSituationPayload(scenario: Scenario) {
  return {
    template_id: scenario.id,
    title: scenario.title,
    category: scenario.category,
    tasks: scenario.stages.flatMap((stage, stageIndex) =>
      stage.tasks.map((task, taskIndex) => ({
        title: task.title,
        due_date: "",
        stage_title: stage.title,
        order_index: stageIndex * 100 + taskIndex,
      }))
    ),
  };
}

function normalizeQuickAccounts(saved: AppUser[]) {
  const byId = new Map<string, AppUser>();
  [...TEST_ACCOUNTS, ...saved].forEach(account => byId.set(account.id, account));
  return Array.from(byId.values());
}

function userDataKey(userId: string) {
  return `${USER_DATA_PREFIX}${userId}`;
}

function profileForUser(user: AppUser): UserProfile {
  if (user.role === "guest") {
    return {
      ...INITIAL_PROFILE,
      name: "Гость",
      email: "",
      region: "",
      city: "",
      district: "",
      addresses: [],
      preferredSourceIds: [],
    };
  }

  return {
    ...INITIAL_PROFILE,
    name: user.name || INITIAL_PROFILE.name,
    email: user.email || INITIAL_PROFILE.email,
    region: user.region || INITIAL_PROFILE.region,
    city: user.city || INITIAL_PROFILE.city,
    district: user.district || INITIAL_PROFILE.district,
    addresses: INITIAL_PROFILE.addresses ?? [],
    preferredSourceIds: INITIAL_PROFILE.preferredSourceIds ?? [],
  };
}

function defaultUserData(user: AppUser): PersistedUserData {
  const hasPersonalArea = user.role !== "guest";
  return {
    situations: hasPersonalArea ? INITIAL_SITUATIONS : [],
    documents: hasPersonalArea ? INITIAL_DOCUMENTS : [],
    favorites: INITIAL_FAVORITES,
    notifications: INITIAL_NOTIFICATIONS,
    profile: profileForUser(user),
    settings: INITIAL_SETTINGS,
    utilityAccounts: hasPersonalArea ? INITIAL_UTILITY_ACCOUNTS : [],
    taxes: hasPersonalArea ? INITIAL_TAXES : [],
    notes: [],
  };
}

function normalizeUserData(user: AppUser, saved: Partial<PersistedUserData> | null): PersistedUserData {
  const fallback = defaultUserData(user);
  return {
    situations: Array.isArray(saved?.situations) ? saved.situations : fallback.situations,
    documents: Array.isArray(saved?.documents) ? saved.documents : fallback.documents,
    favorites: Array.isArray(saved?.favorites) ? saved.favorites : fallback.favorites,
    notifications: Array.isArray(saved?.notifications) ? saved.notifications : fallback.notifications,
    profile: saved?.profile
      ? {
          ...fallback.profile,
          ...saved.profile,
          addresses: Array.isArray(saved.profile.addresses) ? saved.profile.addresses : fallback.profile.addresses,
          preferredSourceIds: Array.isArray(saved.profile.preferredSourceIds) ? saved.profile.preferredSourceIds : fallback.profile.preferredSourceIds,
        }
      : fallback.profile,
    settings: saved?.settings ? { ...fallback.settings, ...saved.settings } : fallback.settings,
    utilityAccounts: Array.isArray(saved?.utilityAccounts) ? saved.utilityAccounts : fallback.utilityAccounts,
    taxes: Array.isArray(saved?.taxes) ? saved.taxes : fallback.taxes,
    notes: Array.isArray(saved?.notes) ? saved.notes : fallback.notes,
  };
}

function mergeApiItem<T extends PublicListItem>(fallback: T, incoming: T): T {
  const merged = { ...fallback, ...incoming } as Record<string, unknown>;
  const fallbackRecord = fallback as Record<string, unknown>;
  const incomingRecord = incoming as Record<string, unknown>;
  const richArrayKeys = ["stages", "documents", "institutions", "sources", "relatedIds", "steps", "deadlines", "mistakes"];

  richArrayKeys.forEach(key => {
    const incomingValue = incomingRecord[key];
    const fallbackValue = fallbackRecord[key];
    if (Array.isArray(incomingValue) && incomingValue.length === 0 && Array.isArray(fallbackValue) && fallbackValue.length > 0) {
      merged[key] = fallbackValue;
    }
  });

  return merged as T;
}

function reconcileApiFirst<T extends PublicListItem>(
  base: T[],
  incoming: T[],
  protectedIds = new Set<string>(),
) {
  const incomingByKey = new Map(incoming.map(item => [publicKey(item), item]));
  const aliases = new Map<string, string>();
  const reconciledBase: T[] = [];

  base.forEach(item => {
    const samePublicItem = incomingByKey.get(publicKey(item));
    if (!samePublicItem) {
      reconciledBase.push(item);
      return;
    }

    if (samePublicItem.id !== item.id) {
      aliases.set(item.id, samePublicItem.id);
      if (protectedIds.has(item.id)) {
        reconciledBase.push({ ...mergeApiItem(item, samePublicItem), id: item.id });
      } else {
        reconciledBase.push(mergeApiItem(item, samePublicItem));
      }
      return;
    }

    reconciledBase.push(mergeApiItem(item, samePublicItem));
  });

  const keptKeys = new Set(reconciledBase.map(publicKey));
  const keptIds = new Set(reconciledBase.map(item => item.id));
  const nextIncoming = incoming.filter(item => !keptKeys.has(publicKey(item)) && !keptIds.has(item.id));

  return { items: [...reconciledBase, ...nextIncoming], aliases };
}

export function AppStoreProvider({ children }: { children: ReactNode }) {
  const [quickAccounts, setQuickAccounts] = useState<AppUser[]>(() => normalizeQuickAccounts(safeRead<AppUser[]>(QUICK_ACCOUNTS_KEY, [])));
  const [currentUser, setCurrentUser] = useState<AppUser>(() => {
    const storedUserId = safeRead<string>(CURRENT_USER_KEY, "guest");
    return normalizeQuickAccounts(safeRead<AppUser[]>(QUICK_ACCOUNTS_KEY, [])).find(account => account.id === storedUserId) ?? GUEST_USER;
  });
  const role = currentUser.role;
  const [scenarios, setScenarios] = useState<Scenario[]>(SCENARIOS);
  const [problems, setProblems] = useState<Problem[]>(PROBLEMS);
  const [legal, setLegal] = useState<LegalUpdate[]>(() => safeRead<LegalUpdate[]>(LEGAL_KEY, LEGAL_UPDATES));
  const [publicDocuments, setPublicDocuments] = useState<DocumentRef[]>([]);
  const [authorities, setAuthorities] = useState<Institution[]>(() => safeRead<Institution[]>(AUTHORITIES_KEY, []));
  const [mutableCategories, setMutableCategories] = useState<Category[]>(() => safeRead<Category[]>(CATEGORIES_KEY, CATEGORIES));
  const [publicContentStatus, setPublicContentStatus] = useState<Store["publicContentStatus"]>("fallback");
  const [publicContentError, setPublicContentError] = useState<string | undefined>(undefined);
  const [situations, setSituations] = useState<UserSituation[]>(INITIAL_SITUATIONS);
  const [documents, setDocuments] = useState<UserDocument[]>(INITIAL_DOCUMENTS);
  const [utilityAccounts, setUtilityAccounts] = useState<UtilityAccount[]>(INITIAL_UTILITY_ACCOUNTS);
  const [taxes, setTaxes] = useState<TaxObligation[]>(INITIAL_TAXES);
  // Platform-wide editorial + UGC content (shared across roles so the editor's
  // moderation queue can see citizen submissions). Global localStorage, not per-user.
  const [articles, setArticles] = useState<Article[]>(() => safeRead<Article[]>(ARTICLES_KEY, []));
  const [blockedSubmitters, setBlockedSubmitters] = useState<string[]>(() => safeRead<string[]>(BLOCKED_SUBMITTERS_KEY, []));
  // Editable geography (regions → districts → city). Admin edits persist globally.
  const [geo, setGeo] = useState<GeoRegion[]>(() => safeRead<GeoRegion[]>(GEO_KEY, GEO_SEED));
  const [viewsDaily, setViewsDaily] = useState<{ date: string; count: number }[]>([]);
  const [meId, setMeId] = useState<string | null>(null);
  const [favorites, setFavorites] = useState<string[]>(INITIAL_FAVORITES);
  const [notifications, setNotifications] = useState<AppNotification[]>(INITIAL_NOTIFICATIONS);
  const [profile, setProfile] = useState<UserProfile>(INITIAL_PROFILE);
  const [settings, setSettings] = useState<Settings>(INITIAL_SETTINGS);
  // v1.1 (P4): пользовательские заметки. Локально, в userData.
  const [notes, setNotes] = useState<UserNote[]>([]);
  const notesRef = useRef<UserNote[]>([]);
  notesRef.current = notes;
  const [hydratedUserId, setHydratedUserId] = useState<string | null>(null);
  const [authSession, setAuthSession] = useState<AuthTokens | null>(null);
  const [adminScenarios, setAdminScenarios] = useState<AdminScenarioRow[]>([]);
  const [adminStatus, setAdminStatus] = useState<"loading" | "api" | "fallback">("fallback");
  const [adminUsers, setAdminUsers] = useState<AdminUserRow[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLogRow[]>([]);
  const [guestGuardSignal, setGuestGuardSignal] = useState(0);

  useEffect(() => {
    safeWrite(CURRENT_USER_KEY, currentUser.id);
    const customAccounts = quickAccounts.filter(account => !account.isTestAccount);
    safeWrite(QUICK_ACCOUNTS_KEY, customAccounts);
  }, [currentUser.id, quickAccounts]);

  useEffect(() => {
    const saved = safeRead<Partial<PersistedUserData> | null>(userDataKey(currentUser.id), null);
    const next = normalizeUserData(currentUser, saved);
    setSituations(next.situations);
    setDocuments(next.documents);
    setFavorites(next.favorites);
    setNotifications(next.notifications);
    setProfile(next.profile);
    setSettings(next.settings);
    setUtilityAccounts(next.utilityAccounts);
    setTaxes(next.taxes);
    setNotes(next.notes);
    setHydratedUserId(currentUser.id);
  }, [currentUser]);

  useEffect(() => {
    const controller = new AbortController();
    setAuthSession(null);
    // Сбросить токены в shared-хранилище apiClient, чтобы 401-refresh не сработал
    // от предыдущего пользователя.
    apiClient.saveTokens(null);

    if (currentUser.role === "guest" || !currentUser.email || !currentUser.password) {
      return () => controller.abort();
    }

    apiClient.login<AuthTokens>(currentUser.email, currentUser.password, { signal: controller.signal })
      .then(tokens => {
        if (!controller.signal.aborted) {
          setAuthSession(tokens);
          apiClient.saveTokens(tokens);
        }
      })
      .catch(error => {
        if (!controller.signal.aborted) {
          console.warn("Backend auth is unavailable; React keeps local user state.", error);
          setAuthSession(null);
          apiClient.saveTokens(null);
        }
      });

    return () => controller.abort();
  }, [currentUser.email, currentUser.password, currentUser.role]);

  useEffect(() => {
    if (hydratedUserId !== currentUser.id) return;
    safeWrite<PersistedUserData>(userDataKey(currentUser.id), {
      situations,
      documents,
      favorites,
      notifications,
      profile,
      settings,
      utilityAccounts,
      taxes,
      notes,
    });
  }, [currentUser.id, documents, favorites, hydratedUserId, notifications, profile, settings, situations, utilityAccounts, taxes, notes]);

  // Platform-wide content + moderation block-list (cached locally for offline).
  useEffect(() => { safeWrite(ARTICLES_KEY, articles); }, [articles]);
  useEffect(() => { safeWrite(BLOCKED_SUBMITTERS_KEY, blockedSubmitters); }, [blockedSubmitters]);
  useEffect(() => { safeWrite(GEO_KEY, geo); }, [geo]);
  useEffect(() => { safeWrite(LEGAL_KEY, legal); }, [legal]);
  useEffect(() => { safeWrite(CATEGORIES_KEY, mutableCategories); }, [mutableCategories]);
  useEffect(() => { safeWrite(AUTHORITIES_KEY, authorities); }, [authorities]);

  // --- Geography CRUD (admin "Регионы и города") ---
  const addRegion = useCallback((name: string) => {
    const region = name.trim();
    if (!region) return;
    setGeo((prev) => (prev.some((r) => r.region === region) ? prev : [...prev, { region, region_center: "", districts: [] }]));
  }, []);
  const deleteRegion = useCallback((region: string) => {
    setGeo((prev) => prev.filter((r) => r.region !== region));
  }, []);
  const updateRegion = useCallback((originalName: string, next: GeoRegion) => {
    const region = next.region.trim();
    if (!region) return;
    setGeo((prev) => prev.map((r) => (r.region === originalName ? { ...next, region } : r)));
  }, []);
  const resetGeo = useCallback(() => setGeo(GEO_SEED), []);

  // --- Legal updates CRUD ---
  const addLegal = useCallback((item: Omit<LegalUpdate, "id">) => {
    setLegal(prev => [{ ...item, id: uid("law") }, ...prev]);
  }, []);
  const updateLegal = useCallback((id: string, patch: Partial<LegalUpdate>) => {
    setLegal(prev => prev.map(l => l.id === id ? { ...l, ...patch } : l));
  }, []);
  const deleteLegal = useCallback((id: string) => {
    setLegal(prev => prev.filter(l => l.id !== id));
  }, []);
  const resetLegal = useCallback(() => setLegal(LEGAL_UPDATES), []);

  // --- Categories CRUD ---
  const addCategory = useCallback((name: string) => {
    const trimmed = name.trim();
    if (!trimmed) return;
    const id = `cat-${trimmed.toLowerCase().replace(/\s+/g, "-")}-${Date.now()}`;
    setMutableCategories(prev => (prev.some(c => c.name === trimmed) ? prev : [...prev, { id: id as Category["id"], name: trimmed }]));
  }, []);
  const updateCategory = useCallback((id: string, name: string) => {
    const trimmed = name.trim();
    if (!trimmed) return;
    setMutableCategories(prev => prev.map(c => c.id === id ? { ...c, name: trimmed } : c));
  }, []);
  const deleteCategory = useCallback((id: string) => {
    setMutableCategories(prev => prev.filter(c => c.id !== id));
  }, []);

  // --- Authorities CRUD ---
  const addAuthority = useCallback((item: Omit<Institution, "id">) => {
    setAuthorities(prev => [{ ...item, id: uid("inst") }, ...prev]);
  }, []);
  const updateAuthority = useCallback((id: string, patch: Partial<Institution>) => {
    setAuthorities(prev => prev.map(a => a.id === id ? { ...a, ...patch } : a));
  }, []);
  const deleteAuthority = useCallback((id: string) => {
    setAuthorities(prev => prev.filter(a => a.id !== id));
  }, []);

  // --- Admin user management (local-first; API sync later) ---
  const setAdminUserRole = useCallback((id: string, role: string) => {
    setAdminUsers(prev => prev.map(u => u.id === id ? { ...u, role } : u));
  }, []);
  const setAdminUserActive = useCallback((id: string, active: boolean) => {
    setAdminUsers(prev => prev.map(u => u.id === id ? { ...u, isActive: active } : u));
  }, []);

  // Resolve the backend numeric user id (for proposer matching + block targeting).
  useEffect(() => {
    const token = authSession?.access_token;
    if (!token) { setMeId(null); return; }
    const ctrl = new AbortController();
    apiClient.getMe<{ id: number | string }>(token, { signal: ctrl.signal })
      .then(me => { if (!ctrl.signal.aborted && me?.id != null) setMeId(String(me.id)); })
      .catch(() => { /* offline: keep local identity */ });
    return () => ctrl.abort();
  }, [authSession?.access_token]);

  // Pull platform content (and the block-list for staff) from the backend.
  // Server is the source of truth when reachable; otherwise the local cache stays.
  const loadArticles = useCallback(async (signal?: AbortSignal) => {
    const token = authSession?.access_token;
    const staff = role === "editor" || role === "admin";
    try {
      if (staff && token) {
        const raw = await apiClient.getAllArticles<Record<string, unknown>[]>(token, { signal });
        setArticles(raw.map(adaptArticle));
      } else {
        const published = await apiClient.getArticles<Record<string, unknown>[]>(undefined, { signal });
        let mine: Record<string, unknown>[] = [];
        if (token) mine = await apiClient.getMyArticles<Record<string, unknown>[]>(token, { signal }).catch(() => []);
        const byId = new Map<string, Article>();
        [...mine, ...published].map(adaptArticle).forEach(a => byId.set(a.id, a));
        setArticles(Array.from(byId.values()));
      }
    } catch (error) {
      if (!signal?.aborted) console.warn("Articles API unavailable; React keeps the local cache.", error);
    }
    if (staff && token) {
      try {
        const blocked = await apiClient.getBlockedSubmitters<(number | string)[]>(token, { signal });
        if (!signal?.aborted) setBlockedSubmitters(blocked.map(String));
      } catch { /* keep local block-list */ }
    }
    try {
      const daily = await apiClient.getDailyViews<{ date: string; count: number }[]>(7, { signal });
      if (!signal?.aborted) setViewsDaily(daily);
    } catch { /* graph falls back to demo */ }
  }, [authSession?.access_token, role]);

  useEffect(() => {
    const ctrl = new AbortController();
    loadArticles(ctrl.signal);
    return () => ctrl.abort();
  }, [loadArticles]);

  useEffect(() => {
    if (currentUser.role === "guest" || !authSession?.access_token) return;
    const controller = new AbortController();

    apiClient.getUserDocuments<Record<string, unknown>[]>(authSession.access_token, { signal: controller.signal })
      .then(items => {
        if (controller.signal.aborted || !Array.isArray(items) || items.length === 0) return;
        const apiDocuments = items.map(adaptUserDocument);
        setDocuments(prev => mergeById(prev, apiDocuments));
      })
      .catch(error => {
        if (!controller.signal.aborted) {
          console.warn("User documents API is unavailable; React keeps local documents.", error);
        }
      });

    return () => controller.abort();
  }, [authSession?.access_token, currentUser.role]);

  useEffect(() => {
    if (currentUser.role === "guest" || !authSession?.access_token) return;
    const controller = new AbortController();

    apiClient.getUserSituations<Record<string, unknown>[]>(authSession.access_token, { signal: controller.signal })
      .then(items => {
        if (controller.signal.aborted || !Array.isArray(items) || items.length === 0) return;
        const apiSituations = items.map(item => adaptUserSituation(item, scenarios));
        setSituations(prev => mergeById(prev, apiSituations));
      })
      .catch(error => {
        if (!controller.signal.aborted) {
          console.warn("User situations API is unavailable; React keeps local situations.", error);
        }
      });

    return () => controller.abort();
  }, [authSession?.access_token, currentUser.role, scenarios]);

  // v1.1 (P4): подтягиваем заметки пользователя из backend. Локальные
  // uid-ы остаются, адаптированные бэковые записи мерджатся.
  useEffect(() => {
    if (currentUser.role === "guest" || !authSession?.access_token) return;
    const controller = new AbortController();

    apiClient.getUserNotes<LooseRecord[]>(authSession.access_token, { signal: controller.signal })
      .then(items => {
        if (controller.signal.aborted || !Array.isArray(items)) return;
        const apiNotes = items.map(adaptUserNote);
        setNotes(prev => mergeById(prev, apiNotes));
      })
      .catch(error => {
        if (!controller.signal.aborted) {
          console.warn("User notes API is unavailable; React keeps local notes.", error);
        }
      });

    return () => controller.abort();
  }, [authSession?.access_token, currentUser.role]);

  // Pull the personal layer (profile, settings, notifications) from backend
  // after a JWT login; local state stays as fallback if the API is down.
  useEffect(() => {
    if (currentUser.role === "guest" || !authSession?.access_token) return;
    const controller = new AbortController();
    const token = authSession.access_token;

    apiClient.getUserProfile<Record<string, unknown>>(token, { signal: controller.signal })
      .then(data => {
        if (controller.signal.aborted || !data || typeof data !== "object") return;
        setProfile(prev => adaptUserProfile(data, prev));
      })
      .catch(error => {
        if (!controller.signal.aborted) console.warn("User profile API is unavailable; React keeps local profile.", error);
      });

    apiClient.getUserSettings<Record<string, unknown>>(token, { signal: controller.signal })
      .then(data => {
        if (controller.signal.aborted || !data || typeof data !== "object") return;
        setSettings(prev => mergeSettings(prev, data));
      })
      .catch(error => {
        if (!controller.signal.aborted) console.warn("User settings API is unavailable; React keeps local settings.", error);
      });

    apiClient.getUserNotifications<Record<string, unknown>[]>(token, { signal: controller.signal })
      .then(items => {
        if (controller.signal.aborted || !Array.isArray(items) || items.length === 0) return;
        setNotifications(prev => mergeById(prev, items.map(adaptNotification)));
      })
      .catch(error => {
        if (!controller.signal.aborted) console.warn("User notifications API is unavailable; React keeps local notifications.", error);
      });

    apiClient.getTaxes<Record<string, unknown>[]>(token, { signal: controller.signal })
      .then(items => {
        if (controller.signal.aborted || !Array.isArray(items) || items.length === 0) return;
        setTaxes(items.map(adaptTax));
      })
      .catch(error => {
        if (!controller.signal.aborted) console.warn("Taxes API is unavailable; React keeps local taxes.", error);
      });

    apiClient.getUtilityAccounts<Record<string, unknown>[]>(token, { signal: controller.signal })
      .then(items => {
        if (controller.signal.aborted || !Array.isArray(items) || items.length === 0) return;
        setUtilityAccounts(items.map(adaptUtilityAccount));
      })
      .catch(error => {
        if (!controller.signal.aborted) console.warn("Utility API is unavailable; React keeps local utility data.", error);
      });

    return () => controller.abort();
  }, [authSession?.access_token, currentUser.role]);

  // Editor/admin content: pull the scenario catalog from the protected admin API.
  useEffect(() => {
    const token = authSession?.access_token;
    if (!token || (currentUser.role !== "admin" && currentUser.role !== "editor")) {
      setAdminScenarios([]);
      setAdminStatus("fallback");
      setAdminUsers([]);
      setAuditLogs([]);
      return;
    }
    const controller = new AbortController();
    setAdminStatus("loading");

    apiClient.getAdminScenarios<Record<string, unknown>[]>(token, { signal: controller.signal })
      .then(items => {
        if (controller.signal.aborted) return;
        if (Array.isArray(items)) {
          setAdminScenarios(items.map(adaptAdminScenarioRow));
          setAdminStatus("api");
        }
      })
      .catch(error => {
        if (!controller.signal.aborted) {
          console.warn("Admin scenarios API is unavailable; admin panel keeps sample data.", error);
          setAdminStatus("fallback");
        }
      });

    apiClient.getAuditLogs<Record<string, unknown>[]>(token, { signal: controller.signal })
      .then(rows => {
        if (controller.signal.aborted || !Array.isArray(rows)) return;
        setAuditLogs(rows.map(r => ({
          id: String(r.id), actor: String(r.actor ?? ""), roleId: String(r.role_id ?? ""),
          eventType: String(r.event_type ?? ""), action: String(r.action ?? ""),
          status: String(r.status ?? ""), createdAt: String(r.created_at ?? ""),
        })));
      })
      .catch(() => { /* keep empty */ });

    if (currentUser.role === "admin") {
      apiClient.getAdminUsers<Record<string, unknown>[]>(token, { signal: controller.signal })
        .then(rows => {
          if (controller.signal.aborted || !Array.isArray(rows)) return;
          setAdminUsers(rows.map(u => ({
            id: String(u.id), email: String(u.email ?? ""), name: String(u.name ?? ""),
            role: String(u.role_id ?? ""), isActive: Boolean(u.is_active),
            city: String(u.city ?? ""), region: String(u.region ?? ""),
          })));
        })
        .catch(() => { /* keep empty */ });
    }

    return () => controller.abort();
  }, [authSession?.access_token, currentUser.role]);


  const applyUser = useCallback((user: AppUser) => {
    setCurrentUser(user);
    if (user.role !== "guest") {
      setProfile(prev => ({
        ...prev,
        name: user.name || prev.name,
        email: user.email || prev.email,
        region: user.region || prev.region,
        city: user.city || prev.city,
        district: user.district || prev.district,
      }));
    }
  }, []);

  const signInAs = useCallback((userId: string) => {
    if (userId === "guest") {
      applyUser(GUEST_USER);
      return;
    }
    const account = quickAccounts.find(item => item.id === userId);
    if (account) applyUser(account);
  }, [applyUser, quickAccounts]);

  const signInWithEmail = useCallback((email: string, password: string) => {
    const normalizedEmail = email.trim().toLowerCase();
    const account = quickAccounts.find(item => item.email.toLowerCase() === normalizedEmail);
    if (!account) return false;
    if ((account.password ?? "Test12345!") !== password) return false;
    applyUser(account);
    return true;
  }, [applyUser, quickAccounts]);

  const registerUser = useCallback((payload: Pick<AppUser, "name" | "email" | "password" | "region" | "city">) => {
    const fresh: AppUser = {
      id: uid("user"),
      name: payload.name.trim() || "Новый пользователь",
      email: payload.email.trim().toLowerCase(),
      password: payload.password || "Test12345!",
      role: "citizen",
      region: payload.region?.trim() || "Минская область",
      city: payload.city?.trim() || "Минск",
      district: "Центральный",
      isTestAccount: false,
    };
    setQuickAccounts(prev => normalizeQuickAccounts([...prev, fresh]));
    applyUser(fresh);
    if (fresh.email && fresh.password) {
      apiClient.register<AuthTokens>({ email: fresh.email, password: fresh.password, name: fresh.name })
        .then(tokens => setAuthSession(tokens))
        .catch(error => {
          console.warn("Backend register is unavailable; React registered local user only.", error);
        });
    }
    return fresh;
  }, [applyUser]);

  const signOut = useCallback(() => {
    // Дёргаем backend, чтобы refresh_token был revoke. Не блокируем UI
    // на ошибке сети: локально мы уже стираем сессию.
    void apiClient.logout().catch(() => undefined);
    setAuthSession(null);
    apiClient.saveTokens(null);
    applyUser(GUEST_USER);
  }, [applyUser]);

  const resetSession = useCallback(() => {
    setQuickAccounts(TEST_ACCOUNTS);
    applyUser(GUEST_USER);
  }, [applyUser]);

  const setRole = useCallback((nextRole: Role) => {
    if (nextRole === "guest") {
      applyUser(GUEST_USER);
      return;
    }
    const account = quickAccounts.find(item => item.role === nextRole);
    if (account) {
      applyUser(account);
      return;
    }
    applyUser({ ...GUEST_USER, id: `role-${nextRole}`, name: nextRole, role: nextRole });
  }, [applyUser, quickAccounts]);

  useEffect(() => {
    const controller = new AbortController();

    async function loadPublicContent() {
      setPublicContentStatus("loading");
      setPublicContentError(undefined);

      const [problemsResult, scenariosResult, documentsResult, authoritiesResult, legalResult] = await Promise.allSettled([
        apiClient.getProblems<Record<string, unknown>[]>({ signal: controller.signal }),
        apiClient.getScenarios<Record<string, unknown>[]>({ signal: controller.signal }),
        apiClient.getDocuments<Record<string, unknown>[]>({ signal: controller.signal }),
        apiClient.getAuthorities<Record<string, unknown>[]>({ signal: controller.signal }),
        apiClient.getLawUpdates<Record<string, unknown>[]>({ signal: controller.signal }),
      ]);

      if (controller.signal.aborted) return;

      let loadedSomething = false;
      const errors: string[] = [];

      if (problemsResult.status === "fulfilled" && Array.isArray(problemsResult.value)) {
        const nextProblems = problemsResult.value.map(adaptProblem);
        if (nextProblems.length) {
          setProblems(prev => reconcileApiFirst(prev, nextProblems).items);
          loadedSomething = true;
        }
      } else if (problemsResult.status === "rejected") {
        errors.push(problemsResult.reason instanceof Error ? problemsResult.reason.message : "Не удалось загрузить проблемы");
      }

      if (scenariosResult.status === "fulfilled" && Array.isArray(scenariosResult.value)) {
        const nextScenarios = scenariosResult.value.map(adaptScenario);
        if (nextScenarios.length) {
          const protectedScenarioIds = new Set(situations.map(situation => situation.scenarioId));
          const reconciled = reconcileApiFirst(scenarios, nextScenarios, protectedScenarioIds);
          setScenarios(reconciled.items);
          if (reconciled.aliases.size) {
            setFavorites(current => uniqueStrings(current.map(id => reconciled.aliases.get(id) ?? id)));
          }
          loadedSomething = true;
        }
      } else if (scenariosResult.status === "rejected") {
        errors.push(scenariosResult.reason instanceof Error ? scenariosResult.reason.message : "Не удалось загрузить сценарии");
      }

      if (documentsResult.status === "fulfilled" && Array.isArray(documentsResult.value)) {
        const nextDocuments = documentsResult.value.map(adaptDocumentRef);
        if (nextDocuments.length) {
          setPublicDocuments(prev => mergeById(prev, nextDocuments));
          loadedSomething = true;
        }
      } else if (documentsResult.status === "rejected") {
        errors.push(documentsResult.reason instanceof Error ? documentsResult.reason.message : "Не удалось загрузить справочник документов");
      }

      if (authoritiesResult.status === "fulfilled" && Array.isArray(authoritiesResult.value)) {
        const nextAuthorities = authoritiesResult.value.map(adaptInstitution);
        if (nextAuthorities.length) {
          setAuthorities(prev => mergeById(prev, nextAuthorities));
          loadedSomething = true;
        }
      } else if (authoritiesResult.status === "rejected") {
        errors.push(authoritiesResult.reason instanceof Error ? authoritiesResult.reason.message : "Не удалось загрузить учреждения");
      }

      if (legalResult.status === "fulfilled" && Array.isArray(legalResult.value)) {
        const nextLegal = legalResult.value.map(adaptLegalUpdate);
        if (nextLegal.length) {
          setLegal(prev => reconcileApiFirst(prev, nextLegal).items);
          loadedSomething = true;
        }
      } else if (legalResult.status === "rejected") {
        errors.push(legalResult.reason instanceof Error ? legalResult.reason.message : "Не удалось загрузить закон-апдейты");
      }

      setPublicContentStatus(loadedSomething ? "api" : "fallback");
      setPublicContentError(errors.length ? errors.join("; ") : undefined);
    }

    loadPublicContent().catch(error => {
      if (controller.signal.aborted) return;
      setPublicContentStatus("fallback");
      setPublicContentError(error instanceof Error ? error.message : "Публичный API недоступен");
    });

    return () => controller.abort();
  }, []);

  const scenarioById = useCallback((id: string) => scenarios.find(s => s.id === id), [scenarios]);
  const problemById = useCallback((id: string) => problems.find(p => p.id === id), [problems]);
  const situationByScenario = useCallback((scenarioId: string) => situations.find(s => s.scenarioId === scenarioId), [situations]);

  // Guest-guard: единая точка входа для действий, требующих аккаунт.
  // Если role === "guest" — инкрементим сигнал (GuestGuardBridge покажет
  // модал) и блокируем действие. Если залогинен — пропускаем.
  const requireAccount = useCallback(() => {
    if (role !== "guest") return true;
    setGuestGuardSignal(s => s + 1);
    return false;
  }, [role]);
  const dismissGuestGuard = useCallback(() => {
    setGuestGuardSignal(0);
  }, []);

  const loadScenarioDetail = useCallback(async (id: string) => {
    const data = await apiClient.getScenario<Record<string, unknown>>(id);
    const fullScenario = adaptScenario(data);
    setScenarios(prev => mergeById(prev, [fullScenario]));
    setPublicContentStatus("api");
    setPublicContentError(undefined);
  }, []);

  const createSituation = useCallback((scenarioId: string) => {
    if (!requireAccount()) return "";
    const existing = situations.find(s => s.scenarioId === scenarioId);
    if (existing) return existing.id;
    const scenario = scenarioById(scenarioId);
    const id = uid("us");
    const fresh: UserSituation = {
      id, scenarioId, status: "in_progress",
      startedAt: new Date().toISOString().slice(0, 10),
      completedTaskIds: [], notes: {},
    };
    setSituations(s => [fresh, ...s]);

    if (authSession?.access_token && scenario) {
      apiClient.createUserSituation<Record<string, unknown>>(authSession.access_token, apiSituationPayload(scenario))
        .then(saved => {
          const apiSituation = adaptUserSituation(saved, scenarios);
          setSituations(prev => prev.map(item => item.id === fresh.id ? apiSituation : item));
        })
        .catch(error => {
          console.warn("Situation was created locally; backend create failed.", error);
        });
    }

    return id;
  }, [authSession?.access_token, role, scenarioById, scenarios, situations]);

  const taskIsBlocked = useCallback((situation: UserSituation, taskId: string) => {
    const scenario = scenarioById(situation.scenarioId);
    if (!scenario) return false;
    const task = scenario.stages.flatMap(st => st.tasks).find(t => t.id === taskId);
    if (!task?.blockedBy?.length) return false;
    return task.blockedBy.some(dep => !situation.completedTaskIds.includes(dep));
  }, [scenarioById]);

  const situationProgress = useCallback((situation: UserSituation) => {
    const scenario = scenarioById(situation.scenarioId);
    if (!scenario) return 0;
    const total = scenario.stages.reduce((n, st) => n + st.tasks.length, 0);
    if (!total) return 0;
    return Math.round((situation.completedTaskIds.length / total) * 100);
  }, [scenarioById]);

  const toggleTask = useCallback((situationId: string, taskId: string) => {
    if (role === "guest") return;
    const current = situations.find(s => s.id === situationId);
    if (!current) return;
    const wasDone = current.completedTaskIds.includes(taskId);
    if (taskIsBlocked(current, taskId) && !wasDone) return;
    const backendTaskId = current.backendTaskIds?.[taskId];

    setSituations(prev => prev.map(s => {
      if (s.id !== situationId) return s;
      const completedTaskIds = wasDone ? s.completedTaskIds.filter(t => t !== taskId) : [...s.completedTaskIds, taskId];
      const scenario = scenarioById(s.scenarioId);
      const total = scenario?.stages.reduce((n, st) => n + st.tasks.length, 0) ?? 0;
      const status: UserSituation["status"] =
        completedTaskIds.length === 0 ? "not_started" :
        completedTaskIds.length === total ? "done" : "in_progress";
      return { ...s, completedTaskIds, status };
    }));

    if (authSession?.access_token && backendTaskId) {
      apiClient.updateUserTask<Record<string, unknown>>(authSession.access_token, backendTaskId, { completed: !wasDone })
        .catch(error => {
          console.warn("Task was toggled locally; backend task update failed.", error);
        });
    }
  }, [authSession?.access_token, role, scenarioById, situations, taskIsBlocked]);

  const setNote = useCallback((situationId: string, taskId: string, note: string) => {
    if (!requireAccount()) return;
    setSituations(prev => prev.map(s => s.id === situationId ? { ...s, notes: { ...s.notes, [taskId]: note } } : s));
  }, [requireAccount]);

  const deleteSituation = useCallback((situationId: string) => {
    if (role === "guest") return;
    setSituations(prev => prev.filter(s => s.id !== situationId));

    if (authSession?.access_token && isBackendSituationId(situationId)) {
      apiClient.deleteUserSituation(authSession.access_token, situationId)
        .catch(error => {
          console.warn("Situation was deleted locally; backend delete failed.", error);
        });
    }
  }, [authSession?.access_token, role]);

  const addDocument: Store["addDocument"] = useCallback((doc) => {
    if (!requireAccount()) return;
    const tempDocument: UserDocument = { id: uid("doc"), status: doc.status ?? "active", ...doc };
    setDocuments(prev => [tempDocument, ...prev]);

    if (authSession?.access_token) {
      apiClient.createUserDocument<Record<string, unknown>>(authSession.access_token, apiDocumentPayload(tempDocument))
        .then(saved => {
          const apiDocument = adaptUserDocument(saved);
          setDocuments(prev => prev.map(item => item.id === tempDocument.id ? apiDocument : item));
        })
        .catch(error => {
          console.warn("User document was saved locally; backend create failed.", error);
        });
    }
  }, [authSession?.access_token, role]);

  const updateDocument: Store["updateDocument"] = useCallback((id, patch) => {
    if (role === "guest") return;
    setDocuments(prev => prev.map(d => d.id === id ? { ...d, ...patch } : d));

    if (authSession?.access_token && isBackendNumericId(id)) {
      const existing = documents.find(doc => doc.id === id);
      const merged = existing ? { ...existing, ...patch } : patch;
      apiClient.updateUserDocument<Record<string, unknown>>(authSession.access_token, id, apiDocumentPayload(merged))
        .then(saved => {
          const apiDocument = adaptUserDocument(saved);
          setDocuments(prev => prev.map(item => item.id === id ? apiDocument : item));
        })
        .catch(error => {
          console.warn("User document was updated locally; backend update failed.", error);
        });
    }
  }, [authSession?.access_token, documents, role]);

  const deleteDocument = useCallback((id: string) => {
    if (role === "guest") return;
    setDocuments(prev => prev.filter(d => d.id !== id));

    if (authSession?.access_token && isBackendNumericId(id)) {
      apiClient.deleteUserDocument(authSession.access_token, id)
        .catch(error => {
          console.warn("User document was deleted locally; backend delete failed.", error);
        });
    }
  }, [authSession?.access_token, role]);

  // --- Taxes (ТЗ §18) ---
  const addTax: Store["addTax"] = useCallback((tax) => {
    if (!requireAccount()) return;
    const temp: TaxObligation = { id: uid("tax"), ...tax };
    setTaxes(prev => [temp, ...prev]);
    if (authSession?.access_token) {
      apiClient.createTax<Record<string, unknown>>(authSession.access_token, taxPayload(temp))
        .then(saved => { const t = adaptTax(saved); setTaxes(prev => prev.map(x => x.id === temp.id ? t : x)); })
        .catch(error => console.warn("Tax saved locally; backend create failed.", error));
    }
  }, [authSession?.access_token, role]);

  const updateTax: Store["updateTax"] = useCallback((id, patch) => {
    if (role === "guest") return;
    const existing = taxes.find(t => t.id === id);
    setTaxes(prev => prev.map(t => t.id === id ? { ...t, ...patch } : t));
    if (authSession?.access_token && isBackendSituationId(id)) {
      apiClient.updateTax<Record<string, unknown>>(authSession.access_token, id, taxPayload({ ...existing, ...patch }))
        .then(saved => { const t = adaptTax(saved); setTaxes(prev => prev.map(x => x.id === id ? t : x)); })
        .catch(error => console.warn("Tax updated locally; backend update failed.", error));
    }
  }, [authSession?.access_token, role, taxes]);

  const deleteTax: Store["deleteTax"] = useCallback((id) => {
    if (role === "guest") return;
    setTaxes(prev => prev.filter(t => t.id !== id));
    if (authSession?.access_token && isBackendSituationId(id)) {
      apiClient.deleteTax(authSession.access_token, id)
        .catch(error => console.warn("Tax deleted locally; backend delete failed.", error));
    }
  }, [authSession?.access_token, role]);

  // --- Синхронизация напоминаний с backend UserNotification (триггер email) ---
  // buildReminders возвращает локальные AppNotification. По ТЗ дедлайны
  // ЖКХ/налогов и истекающие документы должны также попадать в центр
  // уведомлений на бэке и инициировать email-отправку. Чтобы не дублировать,
  // помечаем каждый id напоминания в localStorage после первого пуша.
  const REMINDER_PUSHED_KEY = "belp.remindersPushed";
  const pushedRemindersRef = useRef<Set<string>>(new Set());
  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      const raw = window.localStorage.getItem(REMINDER_PUSHED_KEY);
      if (raw) pushedRemindersRef.current = new Set(JSON.parse(raw) as string[]);
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    if (role === "guest" || !authSession?.access_token) return;
    if (typeof window === "undefined") return;
    const fresh = buildReminders(documents, utilityAccounts, taxes, settings);
    for (const r of fresh) {
      if (pushedRemindersRef.current.has(r.id)) continue;
      // Маппим kind → notification_type: document_expiring → doc_expiry, остальные → task_due.
      const notificationType = r.kind === "document_expiring" ? "doc_expiry" : "task_due";
      apiClient
        .createUserNotification<unknown>(authSession.access_token, {
          title: r.title,
          description: r.body,
          notification_type: notificationType,
          due_date: r.createdAt || null,
          send_email: true,
        })
        .then(() => {
          pushedRemindersRef.current.add(r.id);
          try {
            window.localStorage.setItem(
              REMINDER_PUSHED_KEY,
              JSON.stringify(Array.from(pushedRemindersRef.current)),
            );
          } catch {
            /* ignore */
          }
        })
        .catch((err) => console.warn("Reminder sync failed; staying local-only.", err));
    }
  }, [documents, utilityAccounts, taxes, settings, authSession?.access_token, role]);

  // --- Editor / UGC publications (local-first; backend persistence later) ---
  const articleToServer = (a: Partial<Article>): Record<string, unknown> => {
    const out: Record<string, unknown> = {};
    if (a.kind !== undefined) out.kind = a.kind;
    if (a.title !== undefined) out.title = a.title;
    if (a.summary !== undefined) out.summary = a.summary;
    if (a.bodyHtml !== undefined) out.body_html = a.bodyHtml;
    if (a.cover !== undefined) out.cover = a.cover;
    if (a.video !== undefined) out.video = a.video;
    if (a.gallery !== undefined) out.gallery = a.gallery;
    if (a.tags !== undefined) out.tags = a.tags;
    if (a.category !== undefined) out.category = a.category;
    if (a.specialization !== undefined) out.specialization = a.specialization;
    if (a.audience !== undefined) out.audience = a.audience;
    if (a.source !== undefined) out.source = a.source;
    if (a.sourceUrl !== undefined) out.source_url = a.sourceUrl;
    if (a.status !== undefined) out.status = a.status;
    if (a.date !== undefined) out.date = a.date;
    if (a.reported !== undefined) out.reported = a.reported;
    return out;
  };

  const addArticle: Store["addArticle"] = useCallback((article) => {
    const full: Article = {
      views: 0,
      ...article,
      id: article.id ?? uid("art"),
      updatedAt: new Date().toISOString(),
    };
    setArticles(prev => [full, ...prev]);
    const token = authSession?.access_token;
    if (token) {
      apiClient.createArticle(token, {
        ...articleToServer(full),
        anonymous: full.author?.anonymous ?? false,
        as_proposal: full.author?.role === "citizen",
      })
        .then(() => loadArticles())
        .catch(error => console.warn("Article created locally; backend create failed.", error));
    }
    return full;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [authSession?.access_token, loadArticles]);

  const updateArticle: Store["updateArticle"] = useCallback((id, patch) => {
    setArticles(prev => prev.map(a => a.id === id ? { ...a, ...patch, updatedAt: new Date().toISOString() } : a));
    const token = authSession?.access_token;
    if (token && /^\d+$/.test(id)) {
      apiClient.updateArticleApi(token, id, articleToServer(patch))
        .then(() => loadArticles())
        .catch(error => console.warn("Article updated locally; backend update failed.", error));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [authSession?.access_token, loadArticles]);

  const removeArticle: Store["removeArticle"] = useCallback((id) => {
    setArticles(prev => prev.filter(a => a.id !== id));
    const token = authSession?.access_token;
    if (token && /^\d+$/.test(id)) {
      apiClient.deleteArticleApi(token, id)
        .catch(error => console.warn("Article removed locally; backend delete failed.", error));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [authSession?.access_token]);

  const registerView: Store["registerView"] = useCallback((id) => {
    setArticles(prev => prev.map(a => a.id === id ? { ...a, views: a.views + 1 } : a));
    const today = new Date().toISOString().slice(0, 10);
    setViewsDaily(prev => {
      if (prev.some(d => d.date === today)) return prev.map(d => d.date === today ? { ...d, count: d.count + 1 } : d);
      return [...prev, { date: today, count: 1 }];
    });
    if (/^\d+$/.test(id)) apiClient.viewArticle(id).catch(() => { /* offline: local bump only */ });
  }, []);

  const uploadMedia: Store["uploadMedia"] = useCallback(async (file) => {
    const token = authSession?.access_token;
    if (!token) return null;
    try {
      const { url } = await apiClient.uploadMedia(token, file);
      return `${API_BASE_URL}${url}`;
    } catch (error) {
      console.warn("Media upload failed; falling back to local preview.", error);
      return null;
    }
  }, [authSession?.access_token]);

  const isSubmitterBlocked: Store["isSubmitterBlocked"] = useCallback((id) => blockedSubmitters.includes(id), [blockedSubmitters]);
  const toggleBlockedSubmitter: Store["toggleBlockedSubmitter"] = useCallback((id) => {
    if (!id) return;
    setBlockedSubmitters(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
    const token = authSession?.access_token;
    if (token && /^\d+$/.test(id)) {
      apiClient.toggleBlockedSubmitterApi<(number | string)[]>(token, id)
        .then(list => setBlockedSubmitters(list.map(String)))
        .catch(error => console.warn("Block toggled locally; backend toggle failed.", error));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [authSession?.access_token]);

  // --- Utility / ЖКХ (ТЗ §18) ---
  const addUtilityAccount: Store["addUtilityAccount"] = useCallback((account) => {
    if (!requireAccount()) return;
    const temp: UtilityAccount = { id: uid("util"), payments: [], ...account };
    setUtilityAccounts(prev => [temp, ...prev]);
    if (authSession?.access_token) {
      apiClient.createUtilityAccount<Record<string, unknown>>(authSession.access_token, utilityAccountPayload(temp))
        .then(saved => { const a = adaptUtilityAccount(saved); setUtilityAccounts(prev => prev.map(x => x.id === temp.id ? a : x)); })
        .catch(error => console.warn("Utility account saved locally; backend create failed.", error));
    }
  }, [authSession?.access_token, role]);

  const updateUtilityAccount: Store["updateUtilityAccount"] = useCallback((id, patch) => {
    if (role === "guest") return;
    const existing = utilityAccounts.find(a => a.id === id);
    setUtilityAccounts(prev => prev.map(a => a.id === id ? { ...a, ...patch } : a));
    if (authSession?.access_token && isBackendSituationId(id)) {
      apiClient.updateUtilityAccount<Record<string, unknown>>(authSession.access_token, id, utilityAccountPayload({ ...existing, ...patch }))
        .catch(error => console.warn("Utility account updated locally; backend update failed.", error));
    }
  }, [authSession?.access_token, role, utilityAccounts]);

  const deleteUtilityAccount: Store["deleteUtilityAccount"] = useCallback((id) => {
    if (role === "guest") return;
    setUtilityAccounts(prev => prev.filter(a => a.id !== id));
    if (authSession?.access_token && isBackendSituationId(id)) {
      apiClient.deleteUtilityAccount(authSession.access_token, id)
        .catch(error => console.warn("Utility account deleted locally; backend delete failed.", error));
    }
  }, [authSession?.access_token, role]);

  const addUtilityPayment: Store["addUtilityPayment"] = useCallback((accountId, payment) => {
    if (role === "guest") return;
    const temp: UtilityPayment = { id: uid("upay"), accountId, ...payment };
    setUtilityAccounts(prev => prev.map(a => a.id === accountId ? { ...a, payments: [temp, ...a.payments] } : a));
    if (authSession?.access_token && isBackendSituationId(accountId)) {
      apiClient.addUtilityPayment<Record<string, unknown>>(authSession.access_token, accountId, utilityPaymentPayload(temp))
        .then(saved => { const acc = adaptUtilityAccount(saved); setUtilityAccounts(prev => prev.map(a => a.id === accountId ? acc : a)); })
        .catch(error => console.warn("Utility payment saved locally; backend create failed.", error));
    }
  }, [authSession?.access_token, role]);

  const updateUtilityPayment: Store["updateUtilityPayment"] = useCallback((accountId, paymentId, patch) => {
    if (role === "guest") return;
    const existingAccount = utilityAccounts.find(a => a.id === accountId);
    const existingPayment = existingAccount?.payments.find(p => p.id === paymentId);
    setUtilityAccounts(prev => prev.map(a => a.id === accountId ? { ...a, payments: a.payments.map(p => p.id === paymentId ? { ...p, ...patch } : p) } : a));
    if (authSession?.access_token && isBackendSituationId(paymentId)) {
      apiClient.updateUtilityPayment<Record<string, unknown>>(authSession.access_token, paymentId, utilityPaymentPayload({ ...existingPayment, ...patch }))
        .then(saved => { const p = adaptUtilityPayment(saved, accountId); setUtilityAccounts(prev => prev.map(a => a.id === accountId ? { ...a, payments: a.payments.map(x => x.id === paymentId ? p : x) } : a)); })
        .catch(error => console.warn("Utility payment updated locally; backend update failed.", error));
    }
  }, [authSession?.access_token, role, utilityAccounts]);

  const deleteUtilityPayment: Store["deleteUtilityPayment"] = useCallback((accountId, paymentId) => {
    if (role === "guest") return;
    setUtilityAccounts(prev => prev.map(a => a.id === accountId ? { ...a, payments: a.payments.filter(p => p.id !== paymentId) } : a));
    if (authSession?.access_token && isBackendSituationId(paymentId)) {
      apiClient.deleteUtilityPayment(authSession.access_token, paymentId)
        .catch(error => console.warn("Utility payment deleted locally; backend delete failed.", error));
    }
  }, [authSession?.access_token, role]);

  const toggleFavorite = useCallback((scenarioId: string) => {
    setFavorites(prev => prev.includes(scenarioId) ? prev.filter(x => x !== scenarioId) : [...prev, scenarioId]);
  }, []);

  const markRead = useCallback((id: string) => {
    setNotifications(prev => prev.map(n => n.id === id ? { ...n, read: true } : n));
    if (authSession?.access_token) {
      apiClient.markNotificationRead(authSession.access_token, id)
        .catch(error => console.warn("Notification marked read locally; backend update failed.", error));
    }
  }, [authSession?.access_token]);
  const markAllRead = useCallback(() => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
    if (authSession?.access_token) {
      apiClient.markAllNotificationsRead(authSession.access_token)
        .catch(error => console.warn("Notifications marked read locally; backend update failed.", error));
    }
  }, [authSession?.access_token]);
  const reminders = useMemo(
    () => buildReminders(documents, utilityAccounts, taxes, settings),
    [documents, utilityAccounts, taxes, settings],
  );
  const allNotifications = useMemo(() => [...reminders, ...notifications], [reminders, notifications]);
  const unreadCount = useMemo(() => allNotifications.filter(n => !n.read).length, [allNotifications]);

  const updateProfile: Store["updateProfile"] = useCallback((patch) => {
    if (role === "guest") return;
    setProfile(p => ({ ...p, ...patch }));
    if (authSession?.access_token) {
      apiClient.updateUserProfile(authSession.access_token, userProfilePayload({ ...profile, ...patch }))
        .catch(error => console.warn("Profile saved locally; backend update failed.", error));
    }
  }, [authSession?.access_token, profile, role]);
  const updateSettings: Store["updateSettings"] = useCallback((patch) => {
    setSettings(s => ({ ...s, ...patch }));
    if (authSession?.access_token) {
      apiClient.updateUserSettings(authSession.access_token, patch as Record<string, unknown>)
        .catch(error => console.warn("Settings saved locally; backend update failed.", error));
    }
  }, [authSession?.access_token]);
  const setLang = useCallback((l: Lang) => {
    setSettings(s => ({ ...s, lang: l }));
    if (authSession?.access_token) {
      apiClient.updateUserSettings(authSession.access_token, { lang: l })
        .catch(error => console.warn("Language saved locally; backend update failed.", error));
    }
  }, [authSession?.access_token]);

  const applyQuizResult: Store["applyQuizResult"] = useCallback((correct, total) => {
    if (role === "guest" || total <= 0) return;
    const score = Math.round((correct / total) * 100);
    setProfile(p => {
      const achievements = [...(p.achievements || [])];
      if (score >= 67 && !achievements.some(a => a.id === "quiz-passport")) {
        achievements.push({ id: "quiz-passport", title: "Без паники" });
      }
      return { ...p, learningProgress: Math.max(p.learningProgress || 0, score), achievements };
    });
  }, [role]);

  // v1.1 (P4): пользовательские заметки. Локально + бэк sync.
  const addNote: Store["addNote"] = useCallback((input) => {
    if (!requireAccount()) return;
    const text = input.text.trim();
    if (!text) return;
    const note: UserNote = {
      id: uid("note"),
      text,
      category: input.category,
      reminderAt: input.reminderAt || undefined,
      done: false,
      createdAt: new Date().toISOString(),
    };
    setNotes(prev => [note, ...prev]);
    if (authSession?.access_token) {
      apiClient.createUserNote<LooseRecord>(authSession.access_token, userNotePayload(note))
        .then(created => {
          const adapted = adaptUserNote(created);
          setNotes(prev => prev.map(n => n.id === note.id ? { ...n, ...adapted, id: adapted.id || n.id } : n));
        })
        .catch(err => console.warn("createUserNote API failed; local only.", err));
    }
  }, [role, authSession?.access_token]);

  const updateNote: Store["updateNote"] = useCallback((id, patch) => {
    setNotes(prev => prev.map(n => n.id === id ? { ...n, ...patch } : n));
    if (authSession?.access_token && /^\d+$/.test(String(id))) {
      apiClient.updateUserNote<LooseRecord>(authSession.access_token, String(id), userNotePayload(patch))
        .catch(err => console.warn("updateUserNote API failed; local only.", err));
    }
  }, [authSession?.access_token]);

  const toggleNote: Store["toggleNote"] = useCallback((id) => {
    setNotes(prev => prev.map(n => n.id === id ? { ...n, done: !n.done } : n));
    if (authSession?.access_token && /^\d+$/.test(String(id))) {
      const current = notesRef.current.find(n => n.id === id);
      if (current) {
        apiClient.updateUserNote<LooseRecord>(authSession.access_token, String(id), { done: !current.done })
          .catch(err => console.warn("toggleNote API failed; local only.", err));
      }
    }
  }, [authSession?.access_token]);

  const removeNote: Store["removeNote"] = useCallback((id) => {
    setNotes(prev => prev.filter(n => n.id !== id));
    if (authSession?.access_token && /^\d+$/.test(String(id))) {
      apiClient.deleteUserNote(authSession.access_token, String(id))
        .catch(err => console.warn("deleteUserNote API failed; local only.", err));
    }
  }, [authSession?.access_token]);

  // v1.1 (P4): адреса пользователя (до 5 шт.). Дубликат id, пустые записи
  // отбрасываем. Один помечается isPrimary — остальные снимаются.
  const addAddress: Store["addAddress"] = useCallback((input) => {
    if (!requireAccount()) return;
    setProfile(prev => {
      const current = prev.addresses ?? [];
      if (current.length >= 5) return prev;
      const next: UserAddress = {
        id: uid("addr"),
        label: input.label.trim().slice(0, 80),
        region: input.region.trim().slice(0, 120),
        district: input.district.trim().slice(0, 120),
        city: input.city.trim().slice(0, 120),
        street: input.street.trim().slice(0, 255),
        isPrimary: input.isPrimary ?? current.length === 0,
      };
      if (!next.label && !next.street && !next.city) return prev;
      const wantsPrimary = next.isPrimary;
      const addresses = [
        ...current.map(item => wantsPrimary ? { ...item, isPrimary: false } : item),
        next,
      ];
      const nextProfile = { ...prev, addresses };
      if (authSession?.access_token) {
        apiClient.updateUserProfile(authSession.access_token, userProfilePayload(nextProfile))
          .catch(error => console.warn("Address saved locally; backend update failed.", error));
      }
      return nextProfile;
    });
  }, [authSession?.access_token, role]);

  const updateAddress: Store["updateAddress"] = useCallback((id, patch) => {
    setProfile(prev => {
      const current = prev.addresses ?? [];
      const wantsPrimary = patch.isPrimary === true;
      const addresses = current.map(item => {
        if (item.id === id) {
          return {
            ...item,
            ...patch,
            label: (patch.label ?? item.label).trim().slice(0, 80),
            region: (patch.region ?? item.region).trim().slice(0, 120),
            district: (patch.district ?? item.district).trim().slice(0, 120),
            city: (patch.city ?? item.city).trim().slice(0, 120),
            street: (patch.street ?? item.street).trim().slice(0, 255),
          };
        }
        return wantsPrimary ? { ...item, isPrimary: false } : item;
      });
      const nextProfile = { ...prev, addresses };
      if (authSession?.access_token) {
        apiClient.updateUserProfile(authSession.access_token, userProfilePayload(nextProfile))
          .catch(error => console.warn("Address updated locally; backend update failed.", error));
      }
      return nextProfile;
    });
  }, [authSession?.access_token]);

  const removeAddress: Store["removeAddress"] = useCallback((id) => {
    setProfile(prev => {
      const current = prev.addresses ?? [];
      const filtered = current.filter(item => item.id !== id);
      // Если удалили primary — назначаем первому оставшемуся.
      const hadPrimary = current.some(item => item.id === id && item.isPrimary);
      const addresses = hadPrimary && filtered.length > 0
        ? filtered.map((item, i) => ({ ...item, isPrimary: i === 0 }))
        : filtered;
      const nextProfile = { ...prev, addresses };
      if (authSession?.access_token) {
        apiClient.updateUserProfile(authSession.access_token, userProfilePayload(nextProfile))
          .catch(error => console.warn("Address removed locally; backend update failed.", error));
      }
      return nextProfile;
    });
  }, [authSession?.access_token]);

  // v1.1 (P4): предпочтения источников новостей. Локально, без бэка.
  const togglePreferredSource: Store["togglePreferredSource"] = useCallback((sourceId) => {
    setProfile(prev => {
      const current = prev.preferredSourceIds ?? [];
      const next = current.includes(sourceId)
        ? current.filter(id => id !== sourceId)
        : [...current, sourceId];
      return { ...prev, preferredSourceIds: next };
    });
  }, []);

  const value: Store = useMemo(() => ({
    role, setRole,
    currentUser, quickAccounts, isAuthenticated: role !== "guest",
    signInAs, signInWithEmail, registerUser, signOut, resetSession,
    categories: mutableCategories, scenarios, problems, legal, publicDocuments, authorities,
    publicContentStatus, publicContentError, loadScenarioDetail,
    admin: { scenarios: adminScenarios, status: adminStatus, users: adminUsers, auditLogs: auditLogs },
    situations, createSituation, toggleTask, setNote, deleteSituation,
    documents, addDocument, updateDocument, deleteDocument,
    utilityAccounts, addUtilityAccount, updateUtilityAccount, deleteUtilityAccount, addUtilityPayment, updateUtilityPayment, deleteUtilityPayment,
    taxes, addTax, updateTax, deleteTax,
    articles, addArticle, updateArticle, removeArticle,
    blockedSubmitters, isSubmitterBlocked, toggleBlockedSubmitter, registerView, uploadMedia, viewsDaily, meId,
    favorites, toggleFavorite,
    notifications: allNotifications, markRead, markAllRead, unreadCount,
    profile, updateProfile, applyQuizResult,
    notes, addNote, updateNote, toggleNote, removeNote,
    addAddress, updateAddress, removeAddress,
    togglePreferredSource,
    settings, updateSettings, setLang,
    geo, addRegion, deleteRegion, updateRegion, resetGeo,
    addLegal, updateLegal, deleteLegal, resetLegal,
    addCategory, updateCategory, deleteCategory,
    addAuthority, updateAuthority, deleteAuthority,
    setAdminUserRole, setAdminUserActive,
    scenarioById, problemById, situationByScenario, taskIsBlocked, situationProgress,
    requireAccount, guestGuardSignal, dismissGuestGuard,
  }), [
    role, currentUser, quickAccounts, scenarios, problems, legal, publicDocuments, authorities, publicContentStatus, publicContentError,
    adminScenarios, adminStatus, adminUsers, auditLogs,
    situations, documents, favorites, notifications, profile, settings, utilityAccounts, taxes, articles,
    notes, addNote, updateNote, toggleNote, removeNote,
    addAddress, updateAddress, removeAddress, togglePreferredSource,
    addArticle, updateArticle, removeArticle, blockedSubmitters, isSubmitterBlocked, toggleBlockedSubmitter, registerView, uploadMedia, viewsDaily, meId, loadArticles,
    signInAs, signInWithEmail, registerUser, signOut, resetSession, setRole,
    createSituation, toggleTask, setNote, deleteSituation,
    addDocument, updateDocument, deleteDocument, toggleFavorite,
    addUtilityAccount, updateUtilityAccount, deleteUtilityAccount, addUtilityPayment, updateUtilityPayment, deleteUtilityPayment,
    addTax, updateTax, deleteTax,
    reminders, allNotifications,
    markRead, markAllRead, unreadCount,
    updateProfile, applyQuizResult, updateSettings, setLang,
    geo, addRegion, deleteRegion, updateRegion, resetGeo,
    addLegal, updateLegal, deleteLegal, resetLegal,
    addCategory, updateCategory, deleteCategory, mutableCategories,
    addAuthority, updateAuthority, deleteAuthority,
    setAdminUserRole, setAdminUserActive,
    scenarioById, problemById, situationByScenario, taskIsBlocked, situationProgress,
    loadScenarioDetail,
    requireAccount, guestGuardSignal, dismissGuestGuard,
  ]);

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useStore() {
  const v = useContext(Ctx);
  if (!v) throw new Error("useStore must be used inside <AppStoreProvider>");
  return v;
}

export function maskDocumentNumber(num: string, show: boolean) {
  if (show) return num;
  if (num.length <= 4) return num;
  const tail = num.slice(-4);
  return `•••• •••• ${tail}`;
}

export const DOC_TYPE_LABEL: Record<UserDocumentType, string> = {
  passport: "Паспорт / ID",
  driver: "Водительское удостоверение",
  medical: "Медкнижка",
  birth: "Свидетельство о рождении",
  housing: "Документ на жильё",
  receipt: "Квитанция",
  other: "Другое",
};
