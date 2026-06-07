export type ApiRequestOptions = {
  signal?: AbortSignal;
};

export type AuthTokens = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
};

// API_BASE_URL — динамический.
// 1) Если задан VITE_API_BASE_URL в env — используем его (dev/prod).
// 2) Иначе — берём origin из ServerPicker (там же, где React на iPhone).
// 3) Фолбэк — 127.0.0.1:8000 для локального запуска вне Capacitor.
//
// Идея: Vite-сервер и бэк живут на одном origin (vite на :8560, бэк на :8060).
// Если picker хранит http://192.168.x.x:8560, то API_BASE = http://192.168.x.x:8060.
// Меняйте порт через env если у вас другое разнесение.
const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";
const DEV_BACKEND_PORT = "8060";

function resolveApiBaseUrl(): string {
  const fromEnv = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, "");
  if (fromEnv) return fromEnv;
  if (typeof window === "undefined") return DEFAULT_API_BASE_URL;
  try {
    const raw = window.localStorage.getItem("belpomoshnik.serverUrl");
    if (raw) {
      const u = new URL(raw);
      // Vite origin -> API на соседнем порту
      const nextPort = u.port === "8560" || u.port === "8550" ? DEV_BACKEND_PORT : u.port;
      return `${u.protocol}//${u.hostname}:${nextPort}`;
    }
  } catch {
    /* ignore */
  }
  return DEFAULT_API_BASE_URL;
}

export const API_BASE_URL = resolveApiBaseUrl();

const REFRESH_STORAGE_KEY = "belpomoshnik.authTokens";
const REFRESH_INFLIGHT: { promise: Promise<AuthTokens | null> | null } = { promise: null };

function loadStoredTokens(): AuthTokens | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(REFRESH_STORAGE_KEY);
    return raw ? (JSON.parse(raw) as AuthTokens) : null;
  } catch {
    return null;
  }
}

function saveStoredTokens(tokens: AuthTokens | null): void {
  if (typeof window === "undefined") return;
  try {
    if (tokens) window.localStorage.setItem(REFRESH_STORAGE_KEY, JSON.stringify(tokens));
    else window.localStorage.removeItem(REFRESH_STORAGE_KEY);
  } catch {
    /* ignore */
  }
}

async function refreshTokens(): Promise<AuthTokens | null> {
  if (REFRESH_INFLIGHT.promise) return REFRESH_INFLIGHT.promise;
  const current = loadStoredTokens();
  if (!current?.refresh_token) return null;
  const p = (async () => {
    try {
      const body = new URLSearchParams();
      body.set("refresh_token", current.refresh_token);
      const res = await fetch(`${API_BASE_URL}/api/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body,
      });
      if (!res.ok) {
        saveStoredTokens(null);
        return null;
      }
      const next = (await res.json()) as AuthTokens;
      saveStoredTokens(next);
      return next;
    } catch {
      return null;
    } finally {
      REFRESH_INFLIGHT.promise = null;
    }
  })();
  REFRESH_INFLIGHT.promise = p;
  return p;
}

async function requestJson<T>(path: string, options: RequestInit & ApiRequestOptions = {}): Promise<T> {
  // На 401 пытаемся один раз обновить access_token и повторить исходный запрос.
  // Не делаем этого для самого /api/auth/*, чтобы не зациклиться.
  const isAuthEndpoint = path.startsWith("/api/auth/");
  let attempt = 0;
  let lastError: Error | null = null;

  while (attempt < 2) {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: {
        Accept: "application/json",
        ...(options.body ? { "Content-Type": "application/json" } : {}),
        ...options.headers,
      },
    });

    if (response.status === 401 && !isAuthEndpoint && attempt === 0) {
      const next = await refreshTokens();
      if (next?.access_token) {
        // Подменяем токен в заголовке и пробуем ещё раз.
        const headers = new Headers(options.headers || {});
        headers.set("Authorization", `Bearer ${next.access_token}`);
        options = { ...options, headers };
        attempt++;
        continue;
      }
    }

    if (!response.ok) {
      const message = await response.text().catch(() => "");
      lastError = new Error(message || `API request failed: ${response.status}`);
      break;
    }

    if (response.status === 204) {
      return undefined as T;
    }

    return response.json() as Promise<T>;
  }

  throw lastError ?? new Error("API request failed");
}

function authHeaders(accessToken: string) {
  return { Authorization: `Bearer ${accessToken}` };
}

export const apiClient = {
  login: <T = AuthTokens>(email: string, password: string, options?: ApiRequestOptions) => {
    const body = new URLSearchParams();
    body.set("username", email);
    body.set("password", password);
    return requestJson<T>("/api/auth/login", {
      method: "POST",
      body,
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      ...options,
    });
  },
  register: <T = AuthTokens>(payload: { email: string; password: string; name: string }, options?: ApiRequestOptions) =>
    requestJson<T>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
      ...options,
    }),
  getMe: <T>(accessToken: string, options?: ApiRequestOptions) =>
    requestJson<T>("/api/auth/me", { headers: authHeaders(accessToken), ...options }),

  askAssistant: <T>(payload: { message: string; role: string; is_guest: boolean }, options?: ApiRequestOptions) =>
    requestJson<T>("/api/assistant", {
      method: "POST",
      body: JSON.stringify(payload),
      ...options,
    }),

  getProblems: <T>(options?: ApiRequestOptions) => requestJson<T>("/api/problems", options),
  getProblem: <T>(slug: string, options?: ApiRequestOptions) =>
    requestJson<T>(`/api/problems/${encodeURIComponent(slug)}`, options),
  getScenarios: <T>(options?: ApiRequestOptions) => requestJson<T>("/api/scenarios", options),
  getScenario: <T>(slug: string, options?: ApiRequestOptions) =>
    requestJson<T>(`/api/scenarios/${encodeURIComponent(slug)}`, options),
  getScenarioSteps: <T>(slug: string, options?: ApiRequestOptions) =>
    requestJson<T>(`/api/scenarios/${encodeURIComponent(slug)}/steps`, options),
  getDocuments: <T>(options?: ApiRequestOptions) => requestJson<T>("/api/documents", options),
  getAuthorities: <T>(options?: ApiRequestOptions) => requestJson<T>("/api/authorities", options),
  getLawUpdates: <T>(options?: ApiRequestOptions) => requestJson<T>("/api/law-updates", options),

  getUserProfile: <T>(accessToken: string, options?: ApiRequestOptions) =>
    requestJson<T>("/api/user/profile", { headers: authHeaders(accessToken), ...options }),
  updateUserProfile: <T>(accessToken: string, payload: Record<string, unknown>, options?: ApiRequestOptions) =>
    requestJson<T>("/api/user/profile", {
      method: "PUT",
      headers: authHeaders(accessToken),
      body: JSON.stringify(payload),
      ...options,
    }),
  getUserSettings: <T>(accessToken: string, options?: ApiRequestOptions) =>
    requestJson<T>("/api/user/settings", { headers: authHeaders(accessToken), ...options }),
  updateUserSettings: <T>(accessToken: string, payload: Record<string, unknown>, options?: ApiRequestOptions) =>
    requestJson<T>("/api/user/settings", {
      method: "PATCH",
      headers: authHeaders(accessToken),
      body: JSON.stringify(payload),
      ...options,
    }),
  getUserNotifications: <T>(accessToken: string, options?: ApiRequestOptions) =>
    requestJson<T>("/api/user/notifications", { headers: authHeaders(accessToken), ...options }),
  createUserNotification: <T>(
    accessToken: string,
    payload: { title: string; description?: string; notification_type?: string; due_date?: string | null; send_email?: boolean },
    options?: ApiRequestOptions,
  ) =>
    requestJson<T>("/api/user/notifications", {
      method: "POST",
      headers: authHeaders(accessToken),
      body: JSON.stringify(payload),
      ...options,
    }),
  markNotificationRead: <T>(accessToken: string, id: string, options?: ApiRequestOptions) =>
    requestJson<T>(`/api/user/notifications/${encodeURIComponent(id)}/read`, {
      method: "PATCH",
      headers: authHeaders(accessToken),
      ...options,
    }),
  markAllNotificationsRead: <T>(accessToken: string, options?: ApiRequestOptions) =>
    requestJson<T>("/api/user/notifications/read-all", {
      method: "POST",
      headers: authHeaders(accessToken),
      ...options,
    }),
  deleteUserNotification: (accessToken: string, id: string, options?: ApiRequestOptions) =>
    requestJson<void>(`/api/user/notifications/${encodeURIComponent(id)}`, {
      method: "DELETE",
      headers: authHeaders(accessToken),
      ...options,
    }),
  getUserDocuments: <T>(accessToken: string, options?: ApiRequestOptions) =>
    requestJson<T>("/api/user/documents", { headers: authHeaders(accessToken), ...options }),
  createUserDocument: <T>(accessToken: string, payload: Record<string, unknown>, options?: ApiRequestOptions) =>
    requestJson<T>("/api/user/documents", {
      method: "POST",
      headers: authHeaders(accessToken),
      body: JSON.stringify(payload),
      ...options,
    }),
  updateUserDocument: <T>(accessToken: string, id: string, payload: Record<string, unknown>, options?: ApiRequestOptions) =>
    requestJson<T>(`/api/user/documents/${encodeURIComponent(id)}`, {
      method: "PUT",
      headers: authHeaders(accessToken),
      body: JSON.stringify(payload),
      ...options,
    }),
  deleteUserDocument: (accessToken: string, id: string, options?: ApiRequestOptions) =>
    requestJson<void>(`/api/user/documents/${encodeURIComponent(id)}`, {
      method: "DELETE",
      headers: authHeaders(accessToken),
      ...options,
    }),

  // v1.1 (P4): пользовательские заметки
  getUserNotes: <T>(accessToken: string, options?: ApiRequestOptions) =>
    requestJson<T>("/api/user/notes", { headers: authHeaders(accessToken), ...options }),
  createUserNote: <T>(
    accessToken: string,
    payload: { text: string; category?: string; reminder_at?: string; done?: boolean },
    options?: ApiRequestOptions,
  ) =>
    requestJson<T>("/api/user/notes", {
      method: "POST",
      headers: authHeaders(accessToken),
      body: JSON.stringify(payload),
      ...options,
    }),
  updateUserNote: <T>(
    accessToken: string,
    id: string,
    payload: { text?: string; category?: string; reminder_at?: string; done?: boolean },
    options?: ApiRequestOptions,
  ) =>
    requestJson<T>(`/api/user/notes/${encodeURIComponent(id)}`, {
      method: "PUT",
      headers: authHeaders(accessToken),
      body: JSON.stringify(payload),
      ...options,
    }),
  deleteUserNote: (accessToken: string, id: string, options?: ApiRequestOptions) =>
    requestJson<void>(`/api/user/notes/${encodeURIComponent(id)}`, {
      method: "DELETE",
      headers: authHeaders(accessToken),
      ...options,
    }),
  uploadDocumentScan: async (
    accessToken: string,
    docId: string,
    file: File,
    options?: ApiRequestOptions,
  ): Promise<{ doc_id: number; scan_url: string; scan_size: number; updated_at: string | null }> => {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${API_BASE_URL}/api/user/documents/${encodeURIComponent(docId)}/scan`, {
      method: "POST",
      headers: authHeaders(accessToken), // browser sets multipart boundary
      body: form,
      ...options,
    });
    if (!res.ok) {
      const message = await res.text().catch(() => "");
      throw new Error(message || `Upload failed: ${res.status}`);
    }
    return res.json();
  },
  deleteDocumentScan: (accessToken: string, id: string, options?: ApiRequestOptions) =>
    requestJson<void>(`/api/user/documents/${encodeURIComponent(id)}/scan`, {
      method: "DELETE",
      headers: authHeaders(accessToken),
      ...options,
    }),

  getUserSituations: <T>(accessToken: string, options?: ApiRequestOptions) =>
    requestJson<T>("/api/user/situations", { headers: authHeaders(accessToken), ...options }),
  createUserSituation: <T>(accessToken: string, payload: Record<string, unknown>, options?: ApiRequestOptions) =>
    requestJson<T>("/api/user/situations", {
      method: "POST",
      headers: authHeaders(accessToken),
      body: JSON.stringify(payload),
      ...options,
    }),
  updateUserSituation: <T>(accessToken: string, id: string, payload: Record<string, unknown>, options?: ApiRequestOptions) =>
    requestJson<T>(`/api/user/situations/${encodeURIComponent(id)}`, {
      method: "PUT",
      headers: authHeaders(accessToken),
      body: JSON.stringify(payload),
      ...options,
    }),
  deleteUserSituation: (accessToken: string, id: string, options?: ApiRequestOptions) =>
    requestJson<void>(`/api/user/situations/${encodeURIComponent(id)}`, {
      method: "DELETE",
      headers: authHeaders(accessToken),
      ...options,
    }),
  addUserTask: <T>(accessToken: string, situationId: string, payload: Record<string, unknown>, options?: ApiRequestOptions) =>
    requestJson<T>(`/api/user/situations/${encodeURIComponent(situationId)}/tasks`, {
      method: "POST",
      headers: authHeaders(accessToken),
      body: JSON.stringify(payload),
      ...options,
    }),
  updateUserTask: <T>(accessToken: string, taskId: string, payload: Record<string, unknown>, options?: ApiRequestOptions) =>
    requestJson<T>(`/api/user/tasks/${encodeURIComponent(taskId)}`, {
      method: "PATCH",
      headers: authHeaders(accessToken),
      body: JSON.stringify(payload),
      ...options,
    }),
  deleteUserTask: (accessToken: string, taskId: string, options?: ApiRequestOptions) =>
    requestJson<void>(`/api/user/tasks/${encodeURIComponent(taskId)}`, {
      method: "DELETE",
      headers: authHeaders(accessToken),
      ...options,
    }),

  getTaxes: <T>(accessToken: string, options?: ApiRequestOptions) =>
    requestJson<T>("/api/user/taxes", { headers: authHeaders(accessToken), ...options }),
  createTax: <T>(accessToken: string, payload: Record<string, unknown>, options?: ApiRequestOptions) =>
    requestJson<T>("/api/user/taxes", {
      method: "POST",
      headers: authHeaders(accessToken),
      body: JSON.stringify(payload),
      ...options,
    }),
  updateTax: <T>(accessToken: string, id: string, payload: Record<string, unknown>, options?: ApiRequestOptions) =>
    requestJson<T>(`/api/user/taxes/${encodeURIComponent(id)}`, {
      method: "PUT",
      headers: authHeaders(accessToken),
      body: JSON.stringify(payload),
      ...options,
    }),
  deleteTax: (accessToken: string, id: string, options?: ApiRequestOptions) =>
    requestJson<void>(`/api/user/taxes/${encodeURIComponent(id)}`, {
      method: "DELETE",
      headers: authHeaders(accessToken),
      ...options,
    }),

  getUtilityAccounts: <T>(accessToken: string, options?: ApiRequestOptions) =>
    requestJson<T>("/api/user/utility/accounts", { headers: authHeaders(accessToken), ...options }),
  createUtilityAccount: <T>(accessToken: string, payload: Record<string, unknown>, options?: ApiRequestOptions) =>
    requestJson<T>("/api/user/utility/accounts", {
      method: "POST",
      headers: authHeaders(accessToken),
      body: JSON.stringify(payload),
      ...options,
    }),
  updateUtilityAccount: <T>(accessToken: string, id: string, payload: Record<string, unknown>, options?: ApiRequestOptions) =>
    requestJson<T>(`/api/user/utility/accounts/${encodeURIComponent(id)}`, {
      method: "PUT",
      headers: authHeaders(accessToken),
      body: JSON.stringify(payload),
      ...options,
    }),
  deleteUtilityAccount: (accessToken: string, id: string, options?: ApiRequestOptions) =>
    requestJson<void>(`/api/user/utility/accounts/${encodeURIComponent(id)}`, {
      method: "DELETE",
      headers: authHeaders(accessToken),
      ...options,
    }),
  addUtilityPayment: <T>(accessToken: string, accountId: string, payload: Record<string, unknown>, options?: ApiRequestOptions) =>
    requestJson<T>(`/api/user/utility/accounts/${encodeURIComponent(accountId)}/payments`, {
      method: "POST",
      headers: authHeaders(accessToken),
      body: JSON.stringify(payload),
      ...options,
    }),
  updateUtilityPayment: <T>(accessToken: string, paymentId: string, payload: Record<string, unknown>, options?: ApiRequestOptions) =>
    requestJson<T>(`/api/user/utility/payments/${encodeURIComponent(paymentId)}`, {
      method: "PATCH",
      headers: authHeaders(accessToken),
      body: JSON.stringify(payload),
      ...options,
    }),
  deleteUtilityPayment: (accessToken: string, paymentId: string, options?: ApiRequestOptions) =>
    requestJson<void>(`/api/user/utility/payments/${encodeURIComponent(paymentId)}`, {
      method: "DELETE",
      headers: authHeaders(accessToken),
      ...options,
    }),

  getAdminScenarios: <T>(accessToken: string, options?: ApiRequestOptions) =>
    requestJson<T>("/api/admin/scenarios", { headers: authHeaders(accessToken), ...options }),
  getAdminUsers: <T>(accessToken: string, options?: ApiRequestOptions) =>
    requestJson<T>("/api/admin/users", { headers: authHeaders(accessToken), ...options }),
  getAuditLogs: <T>(accessToken: string, options?: ApiRequestOptions) =>
    requestJson<T>("/api/admin/audit-logs", { headers: authHeaders(accessToken), ...options }),
  getAdminProblems: <T>(accessToken: string, options?: ApiRequestOptions) =>
    requestJson<T>("/api/admin/problems", { headers: authHeaders(accessToken), ...options }),
  updateAdminScenario: <T>(accessToken: string, id: string, payload: Record<string, unknown>, options?: ApiRequestOptions) =>
    requestJson<T>(`/api/admin/scenarios/${encodeURIComponent(id)}`, {
      method: "PUT",
      headers: authHeaders(accessToken),
      body: JSON.stringify(payload),
      ...options,
    }),

  // K-этап: публикации (редакторские + UGC) + модерация + блок-лист.
  getArticles: <T>(kind?: string, options?: ApiRequestOptions) =>
    requestJson<T>(`/api/articles${kind ? `?kind=${encodeURIComponent(kind)}` : ""}`, options),
  viewArticle: <T>(id: string, options?: ApiRequestOptions) =>
    requestJson<T>(`/api/articles/${encodeURIComponent(id)}/view`, { method: "POST", ...options }),
  getDailyViews: <T>(days = 7, options?: ApiRequestOptions) =>
    requestJson<T>(`/api/articles/views/daily?days=${days}`, options),
  uploadMedia: async (accessToken: string, file: File): Promise<{ url: string }> => {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${API_BASE_URL}/api/articles/upload`, {
      method: "POST",
      headers: authHeaders(accessToken), // no Content-Type: browser sets multipart boundary
      body: form,
    });
    if (!res.ok) throw new Error((await res.text().catch(() => "")) || `Upload failed: ${res.status}`);
    return res.json() as Promise<{ url: string }>;
  },
  getAllArticles: <T>(accessToken: string, options?: ApiRequestOptions) =>
    requestJson<T>("/api/articles/all", { headers: authHeaders(accessToken), ...options }),
  getMyArticles: <T>(accessToken: string, options?: ApiRequestOptions) =>
    requestJson<T>("/api/articles/mine", { headers: authHeaders(accessToken), ...options }),
  createArticle: <T>(accessToken: string, payload: Record<string, unknown>, options?: ApiRequestOptions) =>
    requestJson<T>("/api/articles", {
      method: "POST",
      headers: authHeaders(accessToken),
      body: JSON.stringify(payload),
      ...options,
    }),
  updateArticleApi: <T>(accessToken: string, id: string, payload: Record<string, unknown>, options?: ApiRequestOptions) =>
    requestJson<T>(`/api/articles/${encodeURIComponent(id)}`, {
      method: "PUT",
      headers: authHeaders(accessToken),
      body: JSON.stringify(payload),
      ...options,
    }),
  moderateArticle: <T>(accessToken: string, id: string, action: string, options?: ApiRequestOptions) =>
    requestJson<T>(`/api/articles/${encodeURIComponent(id)}/moderate`, {
      method: "POST",
      headers: authHeaders(accessToken),
      body: JSON.stringify({ action }),
      ...options,
    }),
  deleteArticleApi: (accessToken: string, id: string, options?: ApiRequestOptions) =>
    requestJson<void>(`/api/articles/${encodeURIComponent(id)}`, {
      method: "DELETE",
      headers: authHeaders(accessToken),
      ...options,
    }),
  getBlockedSubmitters: <T>(accessToken: string, options?: ApiRequestOptions) =>
    requestJson<T>("/api/articles/blocked", { headers: authHeaders(accessToken), ...options }),
  toggleBlockedSubmitterApi: <T>(accessToken: string, userId: string, options?: ApiRequestOptions) =>
    requestJson<T>(`/api/articles/blocked/${encodeURIComponent(userId)}`, {
      method: "POST",
      headers: authHeaders(accessToken),
      ...options,
    }),

  // --- Auth helpers (хранилище токенов и выход) ---

  saveTokens: (tokens: AuthTokens | null) => saveStoredTokens(tokens),
  loadTokens: () => loadStoredTokens(),

  logout: async (options?: ApiRequestOptions): Promise<void> => {
    const current = loadStoredTokens();
    saveStoredTokens(null);
    if (!current?.refresh_token) return;
    try {
      const body = new URLSearchParams();
      body.set("refresh_token", current.refresh_token);
      await fetch(`${API_BASE_URL}/api/auth/logout`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body,
        ...options,
      });
    } catch {
      // На бэке refresh всё равно истечёт, локально мы уже стёрли токены.
    }
  },
};
