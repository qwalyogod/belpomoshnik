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
// 1) Если в текущем origin сохранён API URL — используем его.
// 2) Если сохранён serverUrl — конвертируем порт 8560/8550 → 8060.
// 3) Если VITE_API_BASE_URL задан реальным внешним URL — используем его.
// 4) Если VITE_API_BASE_URL указывает на localhost, а frontend открыт по LAN,
//    заменяем host на текущий host страницы. На iPhone 127.0.0.1 — это сам
//    телефон, а не компьютер с backend.
// 5) Фолбэк для dev-LAN — текущий host страницы + порт 8060.
// 6) Последний фолбэк — 127.0.0.1:8000.
//
// Меняйте через env или ServerPicker, не правя код.
const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";
const DEV_BACKEND_PORT = "8060";
const DEV_FRONTEND_PORTS = new Set(["8560", "8550"]);
const LOCAL_HOSTS = new Set(["localhost", "127.0.0.1", "::1"]);

function trimSlash(value: string): string {
  return value.replace(/\/$/, "");
}

function isAutoEnv(value: string | undefined): boolean {
  return !value || value.trim().toLowerCase() === "auto";
}

function isLocalHost(hostname: string): boolean {
  return LOCAL_HOSTS.has(hostname.toLowerCase());
}

function isHttpProtocol(protocol: string): boolean {
  return protocol === "http:" || protocol === "https:";
}

function apiFromUrlLike(raw: string): string {
  const u = new URL(raw);
  const nextPort = DEV_FRONTEND_PORTS.has(u.port) || !u.port ? DEV_BACKEND_PORT : u.port;
  return `${u.protocol}//${u.hostname}:${nextPort}`;
}

function apiFromCurrentLocation(): string | null {
  if (typeof window === "undefined" || !isHttpProtocol(window.location.protocol)) return null;
  if (!window.location.hostname) return null;
  return `${window.location.protocol}//${window.location.hostname}:${DEV_BACKEND_PORT}`;
}

function apiUrlForCurrentDevice(raw: string): string | null {
  const value = trimSlash(raw.trim());
  try {
    const parsedUrl = new URL(value);
    const currentApi = apiFromCurrentLocation();
    if (
      currentApi &&
      isLocalHost(parsedUrl.hostname) &&
      typeof window !== "undefined" &&
      !isLocalHost(window.location.hostname)
    ) {
      return currentApi;
    }
    return value;
  } catch {
    return null;
  }
}

function envApiForCurrentDevice(fromEnv: string | undefined): string | null {
  if (isAutoEnv(fromEnv)) return apiFromCurrentLocation();
  const envValue = fromEnv?.trim() ?? "";
  return apiUrlForCurrentDevice(envValue);
}

function resolveApiBaseUrl(): string {
  const fromEnv = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim();
  if (typeof window === "undefined") return DEFAULT_API_BASE_URL;
  try {
    // 1) Явно заданный в ServerPicker API URL
    const explicitApi = window.localStorage.getItem("belpomoshnik.apiBaseUrl");
    if (explicitApi) {
      const api = apiUrlForCurrentDevice(explicitApi);
      if (api) return api;
    }
    // 2) Фолбэк — автоконверсия из serverUrl
    const serverUrl = window.localStorage.getItem("belpomoshnik.serverUrl");
    if (serverUrl) {
      return apiFromUrlLike(serverUrl);
    }
  } catch {
    /* ignore */
  }
  const envApi = envApiForCurrentDevice(fromEnv);
  if (envApi) return envApi;
  const currentApi = apiFromCurrentLocation();
  if (currentApi) return currentApi;
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
      // Бэкенд ожидает JSON-body: Pydantic RefreshRequest.
      // form-urlencoded здесь даст 422, и пользователь будет выкинут из сессии через 30 мин.
      const res = await fetch(`${API_BASE_URL}/api/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ refresh_token: current.refresh_token }),
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

function controlHeaders(controlToken: string) {
  return { "X-Control-Center-Token": controlToken };
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

  /** P14: RAG-ассистент с поиском по БД. Только для авторизованных (citizen+). */
  askAssistantChat: <T>(
    accessToken: string,
    payload: { message: string; role?: string; is_guest?: boolean },
    options?: ApiRequestOptions,
  ) =>
    requestJson<T>("/api/assistant/chat", {
      method: "POST",
      headers: authHeaders(accessToken),
      body: JSON.stringify({
        message: payload.message,
        role: payload.role ?? "citizen",
        is_guest: payload.is_guest ?? false,
      }),
      ...options,
    }),

  // Промпт 3+4: история чатов + structured response + actions.
  listAssistantSessions: <T>(accessToken: string, options?: ApiRequestOptions) =>
    requestJson<T>("/api/assistant/chat/sessions", { headers: authHeaders(accessToken), ...options }),
  createAssistantSession: <T>(accessToken: string, payload: { title?: string; mode?: string } = {}, options?: ApiRequestOptions) =>
    requestJson<T>("/api/assistant/chat/sessions", {
      method: "POST",
      headers: authHeaders(accessToken),
      body: JSON.stringify({ title: payload.title ?? "", mode: payload.mode ?? "citizen" }),
      ...options,
    }),
  patchAssistantSession: <T>(accessToken: string, sessionId: string, patch: { title?: string; archived?: boolean }, options?: ApiRequestOptions) =>
    requestJson<T>(`/api/assistant/chat/sessions/${encodeURIComponent(sessionId)}`, {
      method: "PATCH",
      headers: authHeaders(accessToken),
      body: JSON.stringify(patch),
      ...options,
    }),
  deleteAssistantSession: (accessToken: string, sessionId: string, options?: ApiRequestOptions) =>
    requestJson<void>(`/api/assistant/chat/sessions/${encodeURIComponent(sessionId)}`, {
      method: "DELETE",
      headers: authHeaders(accessToken),
      ...options,
    }),
  listAssistantMessages: <T>(accessToken: string, sessionId: string, options?: ApiRequestOptions) =>
    requestJson<T>(`/api/assistant/chat/sessions/${encodeURIComponent(sessionId)}/messages`, {
      headers: authHeaders(accessToken),
      ...options,
    }),
  sendAssistantMessage: <T>(accessToken: string, sessionId: string, content: string, options?: ApiRequestOptions) =>
    requestJson<T>(`/api/assistant/chat/sessions/${encodeURIComponent(sessionId)}/messages`, {
      method: "POST",
      headers: authHeaders(accessToken),
      body: JSON.stringify({ content }),
      ...options,
    }),
  /** Промпт 3: action из чата — добавить сценарий в «Мои ситуации». */
  createSituationFromAssistant: <T>(accessToken: string, scenarioId: string, sessionId?: string, options?: ApiRequestOptions) =>
    requestJson<T>("/api/assistant/actions/create-situation", {
      method: "POST",
      headers: authHeaders(accessToken),
      body: JSON.stringify({ scenario_id: scenarioId, session_id: sessionId ?? null }),
      ...options,
    }),

  /** Промпт 3/4 (п.7): статус AI и управление личным Groq-ключом. */
  getAiSettings: <T>(accessToken: string, options?: ApiRequestOptions) =>
    requestJson<T>("/api/user/ai-settings", { headers: authHeaders(accessToken), ...options }),
  putGroqKey: <T>(accessToken: string, apiKey: string, model: string, verify: boolean, options?: ApiRequestOptions) =>
    requestJson<T>("/api/user/ai-settings/groq-key", {
      method: "PUT",
      headers: authHeaders(accessToken),
      body: JSON.stringify({ api_key: apiKey, model, verify }),
      ...options,
    }),
  deleteGroqKey: <T>(accessToken: string, options?: ApiRequestOptions) =>
    requestJson<T>("/api/user/ai-settings/groq-key", {
      method: "DELETE",
      headers: authHeaders(accessToken),
      ...options,
    }),
  testAiSettings: <T>(accessToken: string, options?: ApiRequestOptions) =>
    requestJson<T>("/api/user/ai-settings/test", {
      method: "POST",
      headers: authHeaders(accessToken),
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
  getContentTags: <T>(options?: ApiRequestOptions) => requestJson<T>("/api/content-tags", options),
  getLawUpdates: <T>(options?: ApiRequestOptions) => requestJson<T>("/api/law-updates", options),

  // Admin: учреждения (authorities)
  createAdminAuthority: <T>(accessToken: string, payload: Record<string, unknown>, options?: ApiRequestOptions) =>
    requestJson<T>("/api/admin/authorities", {
      method: "POST",
      headers: authHeaders(accessToken),
      body: JSON.stringify(payload),
      ...options,
    }),
  updateAdminAuthority: <T>(accessToken: string, id: number, payload: Record<string, unknown>, options?: ApiRequestOptions) =>
    requestJson<T>(`/api/admin/authorities/${id}`, {
      method: "PUT",
      headers: authHeaders(accessToken),
      body: JSON.stringify(payload),
      ...options,
    }),
  deleteAdminAuthority: <T>(accessToken: string, id: number, options?: ApiRequestOptions) =>
    requestJson<T>(`/api/admin/authorities/${id}`, {
      method: "DELETE",
      headers: authHeaders(accessToken),
      ...options,
    }),

  getUserProfile: <T>(accessToken: string, options?: ApiRequestOptions) =>
    requestJson<T>("/api/user/profile", { headers: authHeaders(accessToken), ...options }),
  updateUserProfile: <T>(accessToken: string, payload: Record<string, unknown>, options?: ApiRequestOptions) =>
    requestJson<T>("/api/user/profile", {
      method: "PUT",
      headers: authHeaders(accessToken),
      body: JSON.stringify(payload),
      ...options,
    }),
  changeUserEmail: <T>(accessToken: string, payload: { email: string; password: string }, options?: ApiRequestOptions) =>
    requestJson<T>("/api/user/account/email", {
      method: "PATCH",
      headers: authHeaders(accessToken),
      body: JSON.stringify(payload),
      ...options,
    }),
  changeUserPassword: <T>(accessToken: string, payload: { old_password: string; new_password: string }, options?: ApiRequestOptions) =>
    requestJson<T>("/api/user/account/password", {
      method: "PATCH",
      headers: authHeaders(accessToken),
      body: JSON.stringify(payload),
      ...options,
    }),
  uploadUserAvatar: async (
    accessToken: string,
    blob: Blob,
    options?: ApiRequestOptions,
  ): Promise<{ avatar_url: string; size: number }> => {
    const form = new FormData();
    // Имя файла с расширением — чтобы бэк/мультипарт корректно определил тип.
    const ext = blob.type === "image/png" ? "png" : blob.type === "image/jpeg" ? "jpg" : "webp";
    form.append("file", blob, `avatar.${ext}`);
    const res = await fetch(`${API_BASE_URL}/api/user/avatar`, {
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
  deleteUserAvatar: (accessToken: string, options?: ApiRequestOptions) =>
    requestJson<void>("/api/user/avatar", {
      method: "DELETE",
      headers: authHeaders(accessToken),
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
    payload: { title: string; description?: string; notification_type?: string; due_date?: string | null; send_email?: boolean; route?: string; dedupe_key?: string },
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
  getNativePushStatus: <T>(accessToken: string, options?: ApiRequestOptions) =>
    requestJson<T>("/api/user/push/status", { headers: authHeaders(accessToken), ...options }),
  registerNativePushToken: <T = unknown>(
    accessToken: string,
    payload: { token: string; platform: "ios" | "android"; device_label?: string },
    options?: ApiRequestOptions,
  ) => requestJson<T>("/api/user/push/native-token", {
    method: "POST",
    headers: authHeaders(accessToken),
    body: JSON.stringify(payload),
    ...options,
  }),
  unregisterNativePushToken: <T = unknown>(accessToken: string, token?: string, options?: ApiRequestOptions) =>
    requestJson<T>("/api/user/push/native-token", {
      method: "DELETE",
      headers: authHeaders(accessToken),
      body: JSON.stringify(token ? { token } : {}),
      ...options,
    }),
  sendTestPushNotification: <T>(accessToken: string, options?: ApiRequestOptions) =>
    requestJson<T>("/api/user/push/test", {
      method: "POST",
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
  /** Промпт 1: загрузка скана (PDF/JPG/PNG/WEBP). Файл шифруется на сервере. */
  uploadDocumentScan: async (
    accessToken: string,
    docId: string,
    file: File,
    options?: ApiRequestOptions,
  ): Promise<{
    doc_id: number;
    scan: {
      has_scan: boolean;
      mime_type: string;
      size: number;
      original_filename: string;
      uploaded_at: string;
      download_url: string;
    };
  }> => {
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
  /** Промпт 1: безопасное скачивание скана. Возвращает Blob, который UI
   * превращает в ObjectURL для предпросмотра. */
  downloadDocumentScan: async (
    accessToken: string,
    docId: string,
    options?: ApiRequestOptions,
  ): Promise<{ blob: Blob; mimeType: string; filename: string }> => {
    const res = await fetch(`${API_BASE_URL}/api/user/documents/${encodeURIComponent(docId)}/scan`, {
      method: "GET",
      headers: authHeaders(accessToken),
      ...options,
    });
    if (!res.ok) {
      const message = await res.text().catch(() => "");
      throw new Error(message || `Download failed: ${res.status}`);
    }
    const blob = await res.blob();
    const mimeType = res.headers.get("Content-Type") || blob.type || "application/octet-stream";
    const disposition = res.headers.get("Content-Disposition") || "";
    const match = /filename="?([^"]+)"?/i.exec(disposition);
    const filename = match?.[1] || `document-${docId}`;
    return { blob, mimeType, filename };
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

  // Промпт 2: заявки 115.
  getUtilityRequests: <T>(accessToken: string, options?: ApiRequestOptions) =>
    requestJson<T>("/api/user/utility/requests", { headers: authHeaders(accessToken), ...options }),
  createUtilityRequest: <T>(accessToken: string, payload: Record<string, unknown>, options?: ApiRequestOptions) =>
    requestJson<T>("/api/user/utility/requests", {
      method: "POST",
      headers: authHeaders(accessToken),
      body: JSON.stringify(payload),
      ...options,
    }),
  updateUtilityRequest: <T>(accessToken: string, id: string, payload: Record<string, unknown>, options?: ApiRequestOptions) =>
    requestJson<T>(`/api/user/utility/requests/${encodeURIComponent(id)}`, {
      method: "PUT",
      headers: authHeaders(accessToken),
      body: JSON.stringify(payload),
      ...options,
    }),
  deleteUtilityRequest: (accessToken: string, id: string, options?: ApiRequestOptions) =>
    requestJson<void>(`/api/user/utility/requests/${encodeURIComponent(id)}`, {
      method: "DELETE",
      headers: authHeaders(accessToken),
      ...options,
    }),

  getAdminScenarios: <T>(accessToken: string, options?: ApiRequestOptions) =>
    requestJson<T>("/api/admin/scenarios", { headers: authHeaders(accessToken), ...options }),
  getAdminDashboardStats: <T>(accessToken: string, options?: ApiRequestOptions) =>
    requestJson<T>("/api/admin/dashboard/stats", { headers: authHeaders(accessToken), ...options }),
  checkAdminScenarioIntegrity: <T>(accessToken: string, scenarioId: string | number, options?: ApiRequestOptions) =>
    requestJson<T>(`/api/admin/scenarios/${encodeURIComponent(String(scenarioId))}/integrity`, { headers: authHeaders(accessToken), ...options }),
  getAdminUsers: <T>(accessToken: string, options?: ApiRequestOptions) =>
    requestJson<T>("/api/admin/users", { headers: authHeaders(accessToken), ...options }),
  getAdminUser: <T>(accessToken: string, userId: number, options?: ApiRequestOptions) =>
    requestJson<T>(`/api/admin/users/${userId}`, { headers: authHeaders(accessToken), ...options }),
  updateAdminUserRole: <T>(accessToken: string, userId: number, role: string, options?: ApiRequestOptions) =>
    requestJson<T>(`/api/admin/users/${userId}/role`, {
      method: "PATCH",
      headers: authHeaders(accessToken),
      body: JSON.stringify({ role }),
      ...options,
    }),
  updateAdminUserActive: <T>(accessToken: string, userId: number, isActive: boolean, options?: ApiRequestOptions) =>
    requestJson<T>(`/api/admin/users/${userId}/active`, {
      method: "PATCH",
      headers: authHeaders(accessToken),
      body: JSON.stringify({ is_active: isActive }),
      ...options,
    }),
  deleteAdminUser: <T>(accessToken: string, userId: number, options?: ApiRequestOptions) =>
    requestJson<T>(`/api/admin/users/${userId}`, {
      method: "DELETE",
      headers: authHeaders(accessToken),
      ...options,
    }),
  revokeAdminUserSessions: <T>(accessToken: string, userId: number, options?: ApiRequestOptions) =>
    requestJson<T>(`/api/admin/users/${userId}/sessions/revoke`, {
      method: "POST",
      headers: authHeaders(accessToken),
      ...options,
    }),
  createAdminUserNotification: <T>(accessToken: string, userId: number, payload: Record<string, unknown>, options?: ApiRequestOptions) =>
    requestJson<T>(`/api/admin/users/${userId}/notifications`, {
      method: "POST",
      headers: authHeaders(accessToken),
      body: JSON.stringify(payload),
      ...options,
    }),
  getAuditLogs: <T>(accessToken: string, options?: ApiRequestOptions) =>
    requestJson<T>("/api/admin/audit-logs", { headers: authHeaders(accessToken), ...options }),
  getAdminContentTags: <T>(accessToken: string, options?: ApiRequestOptions) =>
    requestJson<T>("/api/admin/content-tags", { headers: authHeaders(accessToken), ...options }),
  createAdminContentTag: <T>(accessToken: string, payload: Record<string, unknown>, options?: ApiRequestOptions) =>
    requestJson<T>("/api/admin/content-tags", {
      method: "POST",
      headers: authHeaders(accessToken),
      body: JSON.stringify(payload),
      ...options,
    }),
  updateAdminContentTag: <T>(accessToken: string, id: string | number, payload: Record<string, unknown>, options?: ApiRequestOptions) =>
    requestJson<T>(`/api/admin/content-tags/${encodeURIComponent(String(id))}`, {
      method: "PATCH",
      headers: authHeaders(accessToken),
      body: JSON.stringify(payload),
      ...options,
    }),
  deleteAdminContentTag: (accessToken: string, id: string | number, options?: ApiRequestOptions) =>
    requestJson<void>(`/api/admin/content-tags/${encodeURIComponent(String(id))}`, {
      method: "DELETE",
      headers: authHeaders(accessToken),
      ...options,
    }),
  getAdminRegions: <T>(accessToken: string, options?: ApiRequestOptions) =>
    requestJson<T>("/api/admin/regions", { headers: authHeaders(accessToken), ...options }),
  saveAdminRegions: <T>(accessToken: string, regions: unknown[], options?: ApiRequestOptions) =>
    requestJson<T>("/api/admin/regions", {
      method: "PUT",
      headers: authHeaders(accessToken),
      body: JSON.stringify({ regions }),
      ...options,
    }),
  getAdminProblems: <T>(accessToken: string, options?: ApiRequestOptions) =>
    requestJson<T>("/api/admin/problems", { headers: authHeaders(accessToken), ...options }),
  createAdminProblem: <T>(accessToken: string, payload: Record<string, unknown>, options?: ApiRequestOptions) =>
    requestJson<T>("/api/admin/problems", {
      method: "POST",
      headers: authHeaders(accessToken),
      body: JSON.stringify(payload),
      ...options,
    }),
  updateAdminProblem: <T>(accessToken: string, id: string | number, payload: Record<string, unknown>, options?: ApiRequestOptions) =>
    requestJson<T>(`/api/admin/problems/${encodeURIComponent(String(id))}`, {
      method: "PUT",
      headers: authHeaders(accessToken),
      body: JSON.stringify(payload),
      ...options,
    }),
  updateAdminScenario: <T>(accessToken: string, id: string, payload: Record<string, unknown>, options?: ApiRequestOptions) =>
    requestJson<T>(`/api/admin/scenarios/${encodeURIComponent(id)}`, {
      method: "PUT",
      headers: authHeaders(accessToken),
      body: JSON.stringify(payload),
      ...options,
    }),

  getSystemState: <T>(options?: ApiRequestOptions) =>
    requestJson<T>("/api/public/system-state", { ...options }),
  unlockControlCenter: <T>(password: string, options?: ApiRequestOptions) =>
    requestJson<T>("/api/control-center/unlock", {
      method: "POST",
      body: JSON.stringify({ password }),
      ...options,
    }),
  lockControlCenter: <T>(controlToken: string, options?: ApiRequestOptions) =>
    requestJson<T>("/api/control-center/lock", {
      method: "POST",
      headers: controlHeaders(controlToken),
      ...options,
    }),
  getControlCenterStatus: <T>(controlToken: string, options?: ApiRequestOptions) =>
    requestJson<T>("/api/control-center/status", {
      headers: controlHeaders(controlToken),
      ...options,
    }),
  updateControlMaintenance: <T>(controlToken: string, payload: Record<string, unknown>, options?: ApiRequestOptions) =>
    requestJson<T>("/api/control-center/maintenance", {
      method: "PUT",
      headers: controlHeaders(controlToken),
      body: JSON.stringify(payload),
      ...options,
    }),
  updateControlReadonly: <T>(controlToken: string, payload: Record<string, unknown>, options?: ApiRequestOptions) =>
    requestJson<T>("/api/control-center/readonly", {
      method: "PUT",
      headers: controlHeaders(controlToken),
      body: JSON.stringify(payload),
      ...options,
    }),
  updateControlBanner: <T>(controlToken: string, payload: Record<string, unknown>, options?: ApiRequestOptions) =>
    requestJson<T>("/api/control-center/banner", {
      method: "PUT",
      headers: controlHeaders(controlToken),
      body: JSON.stringify(payload),
      ...options,
    }),
  updateControlFeatureFlags: <T>(controlToken: string, flags: Record<string, boolean>, options?: ApiRequestOptions) =>
    requestJson<T>("/api/control-center/feature-flags", {
      method: "PUT",
      headers: controlHeaders(controlToken),
      body: JSON.stringify({ flags }),
      ...options,
    }),
  updateControlBranding: <T>(controlToken: string, payload: Record<string, unknown>, options?: ApiRequestOptions) =>
    requestJson<T>("/api/control-center/branding", {
      method: "PUT",
      headers: controlHeaders(controlToken),
      body: JSON.stringify(payload),
      ...options,
    }),
  updateControlNavigationLayout: <T>(controlToken: string, payload: Record<string, unknown>, options?: ApiRequestOptions) =>
    requestJson<T>("/api/control-center/navigation-layout", {
      method: "PUT",
      headers: controlHeaders(controlToken),
      body: JSON.stringify(payload),
      ...options,
    }),
  sendControlBroadcast: <T>(controlToken: string, payload: Record<string, unknown>, options?: ApiRequestOptions) =>
    requestJson<T>("/api/control-center/broadcast-notification", {
      method: "POST",
      headers: controlHeaders(controlToken),
      body: JSON.stringify(payload),
      ...options,
    }),
  runControlAction: <T>(controlToken: string, action: string, options?: ApiRequestOptions) =>
    requestJson<T>(`/api/control-center/service-actions/${encodeURIComponent(action)}`, {
      method: "POST",
      headers: controlHeaders(controlToken),
      ...options,
    }),
  getControlAuditLog: <T>(controlToken: string, options?: ApiRequestOptions) =>
    requestJson<T>("/api/control-center/audit-log", {
      headers: controlHeaders(controlToken),
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

  getExtremistEntries: <T>(options?: ApiRequestOptions) =>
    requestJson<T>("/api/extremist-entries", options),
  getExtremistEntry: <T>(id: string | number, options?: ApiRequestOptions) =>
    requestJson<T>(`/api/extremist-entries/${encodeURIComponent(String(id))}`, options),
  getAdminExtremistEntries: <T>(accessToken: string, options?: ApiRequestOptions) =>
    requestJson<T>("/api/admin/extremist-entries", { headers: authHeaders(accessToken), ...options }),
  getAdminExtremistEntry: <T>(accessToken: string, id: string | number, options?: ApiRequestOptions) =>
    requestJson<T>(`/api/admin/extremist-entries/${encodeURIComponent(String(id))}`, { headers: authHeaders(accessToken), ...options }),
  createExtremistEntry: <T>(accessToken: string, payload: Record<string, unknown>, options?: ApiRequestOptions) =>
    requestJson<T>("/api/admin/extremist-entries", {
      method: "POST",
      headers: authHeaders(accessToken),
      body: JSON.stringify(payload),
      ...options,
    }),
  updateExtremistEntry: <T>(accessToken: string, id: string | number, payload: Record<string, unknown>, options?: ApiRequestOptions) =>
    requestJson<T>(`/api/admin/extremist-entries/${encodeURIComponent(String(id))}`, {
      method: "PATCH",
      headers: authHeaders(accessToken),
      body: JSON.stringify(payload),
      ...options,
    }),
  deleteExtremistEntry: (accessToken: string, id: string | number, options?: ApiRequestOptions) =>
    requestJson<void>(`/api/admin/extremist-entries/${encodeURIComponent(String(id))}`, {
      method: "DELETE",
      headers: authHeaders(accessToken),
      ...options,
    }),

  // --- Auth helpers (хранилище токенов и выход) ---

  /** Промпт 5: редакторский AI с расширенными режимами и тоном/длиной. */
  aiAssistContent: <T>(
    accessToken: string,
    payload: {
      mode:
        | "generate" | "rewrite" | "expand" | "summarize" | "translate"
        | "headline" | "outline" | "simplify" | "proofread" | "fact_check"
        | "seo" | "social" | "neutralize";
      kind?: "news" | "scenario" | "problem" | "law" | "guide";
      current_title?: string;
      current_summary?: string;
      current_body_html?: string;
      hint?: string;
      tone?: "official" | "simple" | "newsworthy" | "neutral";
      length?: "short" | "medium" | "long";
      category?: string;
      tags?: string[];
      audience?: string;
      source_label?: string;
      source_url?: string;
    },
    options?: ApiRequestOptions,
  ) =>
    requestJson<T>("/api/admin/assistant/content", {
      method: "POST",
      headers: authHeaders(accessToken),
      body: JSON.stringify({
        mode: payload.mode,
        kind: payload.kind ?? "news",
        current_title: payload.current_title ?? "",
        current_summary: payload.current_summary ?? "",
        current_body_html: payload.current_body_html ?? "",
        hint: payload.hint ?? "",
        tone: payload.tone ?? null,
        length: payload.length ?? null,
        category: payload.category ?? "",
        tags: payload.tags ?? [],
        audience: payload.audience ?? "",
        source_label: payload.source_label ?? "",
        source_url: payload.source_url ?? "",
      }),
      ...options,
    }),

  saveTokens: (tokens: AuthTokens | null) => saveStoredTokens(tokens),
  loadTokens: () => loadStoredTokens(),

  logout: async (options?: ApiRequestOptions): Promise<void> => {
    const current = loadStoredTokens();
    saveStoredTokens(null);
    if (!current?.refresh_token) return;
    try {
      // Бэкенд ожидает JSON (Pydantic RefreshRequest). form-urlencoded → 422.
      await fetch(`${API_BASE_URL}/api/auth/logout`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ refresh_token: current.refresh_token }),
        ...options,
      });
    } catch {
      // На бэке refresh всё равно истечёт, локально мы уже стёрли токены.
    }
  },
};
