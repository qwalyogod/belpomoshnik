/**
 * ServerPicker — экран ввода адресов сервера.
 *
 * Показывается при каждом запуске нативного Capacitor-приложения
 * (пока мы на capacitor://localhost — значит бандл, надо ввести серверы).
 *
 * Два независимых адреса:
 *   - serverUrl  (Vite dev origin)   : куда грузить React
 *   - apiBaseUrl (FastAPI backend)   : куда ходить за данными
 *
 * По умолчанию apiBaseUrl — соседний порт относительно serverUrl
 * (vite 8560 → fastapi 8060). Пользователь может переопределить.
 *
 * После window.location.replace(serverUrl) WebView переходит на http://...,
 * там protocol !== 'capacitor:' — пикер закрывается мгновенно.
 *
 * В браузере/Vite dev — не рендерится совсем.
 */
import { useEffect, useState } from "react";
import { Server, ExternalLink, AlertTriangle, Database } from "lucide-react";

const SERVER_KEY = "belpomoshnik.serverUrl";
const API_KEY = "belpomoshnik.apiBaseUrl";
const DEV_BACKEND_PORT = "8060";

function normalizeUrl(raw: string): string | null {
  const s = raw.trim();
  if (!s) return null;
  const withScheme = /^https?:\/\//i.test(s) ? s : `http://${s}`;
  try {
    const u = new URL(withScheme);
    if (u.protocol !== "http:" && u.protocol !== "https:") return null;
    return u.toString().replace(/\/$/, "");
  } catch {
    return null;
  }
}

function defaultApiFromServer(serverUrl: string): string {
  try {
    const u = new URL(serverUrl);
    if (u.port === "8560" || u.port === "8550" || !u.port) {
      u.port = DEV_BACKEND_PORT;
    }
    return u.toString().replace(/\/$/, "");
  } catch {
    return "";
  }
}

function withShellCacheBust(serverUrl: string): string {
  try {
    const u = new URL(serverUrl);
    u.searchParams.set("__belp_shell_ts", String(Date.now()));
    return u.toString();
  } catch {
    return serverUrl;
  }
}

function isCapacitorShell(): boolean {
  if (typeof window === "undefined") return false;
  const cap = (window as unknown as { Capacitor?: { isNativePlatform?: () => boolean } }).Capacitor;
  return !!(cap && typeof cap.isNativePlatform === "function" && cap.isNativePlatform());
}

export function ServerPicker() {
  // Хуки вызываются ВСЕГДА в одном порядке, чтобы React-правила не нарушались.
  // Решение о рендере принимается ПОСЛЕ хуков на основе их результата.
  const [open, setOpen] = useState(false);
  const [serverValue, setServerValue] = useState("");
  const [apiValue, setApiValue] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Не рендерить в браузере / Vite dev
    if (typeof window === "undefined" || !isCapacitorShell()) {
      setOpen(false);
      return;
    }
    // Уже на внешнем сервере (http/https) — пикер не нужен
    if (window.location.protocol !== "capacitor:") {
      setOpen(false);
      return;
    }

    // На capacitor://localhost — показываем пикер, предзаполняем сохранёнными URL
    try {
      const savedServer = localStorage.getItem(SERVER_KEY) || "";
      const savedApi = localStorage.getItem(API_KEY) || "";
      setServerValue(savedServer);
      // Если API URL не сохранён — вычислим дефолт из server URL
      setApiValue(savedApi || defaultApiFromServer(savedServer));
    } catch { /* ignore */ }

    setOpen(true);
  }, []);

  if (!open) return null;

  const submit = () => {
    const server = normalizeUrl(serverValue);
    if (!server) {
      setError("Введите корректный адрес фронтенда, например http://192.168.1.10:8560");
      return;
    }
    // API: если поле пустое — автодефолт по serverUrl (соседний порт).
    // Если введено — валидируем.
    const apiTrimmed = apiValue.trim();
    let api: string;
    if (!apiTrimmed) {
      api = defaultApiFromServer(server);
    } else {
      const normalized = normalizeUrl(apiTrimmed);
      if (!normalized) {
        setError("Введите корректный адрес бэкенда, например http://192.168.1.10:8060");
        return;
      }
      api = normalized;
    }

    // Сохраняем оба URL для следующего запуска
    try {
      localStorage.setItem(SERVER_KEY, server);
      localStorage.setItem(API_KEY, api);
    } catch { /* ignore */ }
    // Переходим на фронт-сервер внутри WebView (не в Safari)
    // allowNavigation в capacitor.config.json разрешает это для iOS WKWebView
    window.location.replace(withShellCacheBust(server));
  };

  // Общий стиль поля (переиспользуется для двух инпутов)
  const fieldStyle = (hasError: boolean): React.CSSProperties => ({
    display: "flex", alignItems: "center", gap: 10,
    background: "rgba(255,255,255,0.065)",
    border: `1.5px solid ${hasError ? "rgba(252,165,165,0.6)" : "rgba(255,255,255,0.12)"}`,
    borderRadius: 16, padding: "13px 14px",
    transition: "border-color 0.2s",
  });

  const inputStyle: React.CSSProperties = {
    flex: 1, background: "transparent", border: "none", outline: "none",
    color: "#fff", fontSize: 15, fontFamily: "ui-monospace, monospace",
    letterSpacing: -0.2, minWidth: 0,
  };

  const clearBtnStyle: React.CSSProperties = {
    background: "rgba(255,255,255,0.1)", border: "none",
    color: "rgba(255,255,255,0.5)", cursor: "pointer",
    padding: "2px 6px", borderRadius: 6, fontSize: 12, lineHeight: 1,
    flexShrink: 0,
  };

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 2147483647,
        background: "#07080C",
        color: "#fff",
        display: "flex",
        flexDirection: "column",
        padding: "calc(env(safe-area-inset-top) + 32px) 24px calc(env(safe-area-inset-bottom) + 32px)",
        fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Text', system-ui, sans-serif",
        overflowY: "auto",
      }}
    >
      <div style={{ margin: "auto", width: "100%", maxWidth: 380, display: "flex", flexDirection: "column", gap: 20 }}>

        {/* Логотип */}
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{
            display: "grid", placeItems: "center", width: 48, height: 48,
            borderRadius: 16, background: "linear-gradient(135deg,#0056FF,#2277FF)",
            boxShadow: "0 10px 24px -6px rgba(0,86,255,0.55)",
            flexShrink: 0,
          }}>
            <Server size={22} color="#fff" />
          </span>
          <div>
            <div style={{ fontSize: 20, fontWeight: 700, letterSpacing: -0.4, lineHeight: 1.1 }}>Белпомощник</div>
            <div style={{ fontSize: 12, color: "rgba(255,255,255,0.4)", marginTop: 2 }}>Подключение к серверу</div>
          </div>
        </div>

        {/* Инструкция */}
        <p style={{ margin: 0, fontSize: 14, lineHeight: 1.6, color: "rgba(255,255,255,0.55)" }}>
          Запустите{" "}
          <code style={{ fontFamily: "ui-monospace, monospace", fontSize: 13, color: "#7FA8FF", background: "rgba(127,168,255,0.1)", padding: "1px 5px", borderRadius: 5 }}>pnpm dev</code>
          {" "}на ПК. В строке{" "}
          <code style={{ fontFamily: "ui-monospace, monospace", fontSize: 13, color: "#7FA8FF", background: "rgba(127,168,255,0.1)", padding: "1px 5px", borderRadius: 5 }}>Network:</code>
          {" "}будет адрес фронта — вставьте ниже. Бэкенд обычно на том же хосте, порт 8060.
        </p>

        {/* Поле 1: Vite dev URL */}
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          <label style={{ fontSize: 11, letterSpacing: 0.4, textTransform: "uppercase", color: "rgba(255,255,255,0.4)" }}>
            Фронтенд (Vite dev)
          </label>
          <div style={fieldStyle(!!error && !normalizeUrl(serverValue))}>
            <ExternalLink size={16} color="rgba(255,255,255,0.35)" style={{ flexShrink: 0 }} />
            <input
              autoFocus
              inputMode="url"
              type="url"
              placeholder="http://192.168.1.10:8560"
              value={serverValue}
              onChange={(e) => { setServerValue(e.target.value); if (error) setError(null); }}
              onKeyDown={(e) => { if (e.key === "Enter") submit(); }}
              style={inputStyle}
            />
            {serverValue && (
              <button type="button" onClick={() => { setServerValue(""); if (error) setError(null); }} style={clearBtnStyle}>✕</button>
            )}
          </div>
        </div>

        {/* Поле 2: API URL */}
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          <label style={{ fontSize: 11, letterSpacing: 0.4, textTransform: "uppercase", color: "rgba(255,255,255,0.4)" }}>
            Бэкенд (FastAPI)
          </label>
          <div style={fieldStyle(!!error && !normalizeUrl(apiValue) && !!apiValue.trim())}>
            <Database size={16} color="rgba(255,255,255,0.35)" style={{ flexShrink: 0 }} />
            <input
              inputMode="url"
              type="url"
              placeholder={serverValue ? defaultApiFromServer(serverValue) || "http://192.168.1.10:8060" : "http://192.168.1.10:8060"}
              value={apiValue}
              onChange={(e) => { setApiValue(e.target.value); if (error) setError(null); }}
              onKeyDown={(e) => { if (e.key === "Enter") submit(); }}
              style={inputStyle}
            />
            {apiValue && (
              <button type="button" onClick={() => { setApiValue(""); if (error) setError(null); }} style={clearBtnStyle}>✕</button>
            )}
          </div>
          <div style={{ fontSize: 11, color: "rgba(255,255,255,0.35)", lineHeight: 1.4 }}>
            Оставьте пустым — подставится автоматически (порт 8060).
          </div>
        </div>

        {/* Ошибка */}
        {error && (
          <div style={{ display: "flex", alignItems: "center", gap: 8, color: "#FCA5A5", fontSize: 13 }}>
            <AlertTriangle size={14} style={{ flexShrink: 0 }} /> {error}
          </div>
        )}

        {/* Кнопка подключения */}
        <button
          type="button"
          onClick={submit}
          style={{
            height: 52, borderRadius: 16,
            background: "linear-gradient(135deg,#0056FF,#2277FF)",
            color: "#fff", fontSize: 16, fontWeight: 600, letterSpacing: -0.2,
            border: "none", cursor: "pointer",
            boxShadow: "0 18px 36px -10px rgba(0,86,255,0.55)",
            transition: "opacity 0.15s, transform 0.1s",
            WebkitTapHighlightColor: "transparent",
          }}
          onMouseDown={(e) => (e.currentTarget.style.transform = "scale(0.98)")}
          onMouseUp={(e) => (e.currentTarget.style.transform = "")}
          onTouchStart={(e) => (e.currentTarget.style.opacity = "0.85")}
          onTouchEnd={(e) => (e.currentTarget.style.opacity = "")}
        >
          Подключиться
        </button>

        <p style={{ margin: 0, textAlign: "center", fontSize: 11, lineHeight: 1.5, color: "rgba(255,255,255,0.22)" }}>
          Адреса сохраняются — следующий раз заполнятся автоматически
        </p>
      </div>
    </div>
  );
}

export default ServerPicker;
