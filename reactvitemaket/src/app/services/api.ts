export type ApiRequestOptions = {
  signal?: AbortSignal;
};

export type AuthTokens = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
};

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";

export const API_BASE_URL =
  (import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL).replace(/\/$/, "");

async function requestJson<T>(path: string, options: RequestInit & ApiRequestOptions = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      Accept: "application/json",
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...options.headers,
    },
  });

  if (!response.ok) {
    const message = await response.text().catch(() => "");
    throw new Error(message || `API request failed: ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
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
};
