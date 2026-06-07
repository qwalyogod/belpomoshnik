/**
 * ServerPicker — экран ввода адреса сервера.
 *
 * Показывается при каждом запуске нативного Capacitor-приложения
 * (пока мы на capacitor://localhost — значит бандл, надо ввести сервер).
 *
 * После window.location.replace(url) WebView переходит на http://...,
 * там protocol !== 'capacitor:' — пикер закрывается мгновенно.
 *
 * В браузере/Vite dev — не рендерится совсем.
 */
import { useEffect, useState } from "react";
import { Server, ExternalLink, AlertTriangle } from "lucide-react";

const STORAGE_KEY = "belpomoshnik.serverUrl";

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

function isCapacitorShell(): boolean {
  if (typeof window === "undefined") return false;
  const cap = (window as unknown as { Capacitor?: { isNativePlatform?: () => boolean } }).Capacitor;
  return !!(cap && typeof cap.isNativePlatform === "function" && cap.isNativePlatform());
}

export function ServerPicker() {
  // Не рендерить в браузере / Vite dev
  if (typeof window === "undefined" || !isCapacitorShell()) return null;

  // eslint-disable-next-line react-hooks/rules-of-hooks
  const [open, setOpen] = useState(false);
  // eslint-disable-next-line react-hooks/rules-of-hooks
  const [value, setValue] = useState("");
  // eslint-disable-next-line react-hooks/rules-of-hooks
  const [error, setError] = useState<string | null>(null);

  // eslint-disable-next-line react-hooks/rules-of-hooks
  useEffect(() => {
    // Уже на внешнем сервере (http/https) — пикер не нужен
    if (window.location.protocol !== "capacitor:") {
      setOpen(false);
      return;
    }

    // На capacitor://localhost — показываем пикер, предзаполняем последним URL
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) setValue(saved);
    } catch { /* ignore */ }

    setOpen(true);
  }, []);

  if (!open) return null;

  const submit = () => {
    const url = normalizeUrl(value);
    if (!url) {
      setError("Введите корректный URL, например http://192.168.1.10:8560");
      return;
    }
    // Сохраняем для следующего запуска (читается только с capacitor:// origin — OK)
    try { localStorage.setItem(STORAGE_KEY, url); } catch { /* ignore */ }
    // Переходим на сервер внутри WebView (не в Safari)
    // allowNavigation в capacitor.config.json разрешает это для iOS WKWebView
    window.location.replace(url);
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
          {" "}будет адрес — вставьте его сюда.
          ПК и телефон должны быть в одной Wi-Fi.
        </p>

        {/* Поле ввода */}
        <div style={{
          display: "flex", alignItems: "center", gap: 10,
          background: "rgba(255,255,255,0.065)",
          border: `1.5px solid ${error ? "rgba(252,165,165,0.6)" : "rgba(255,255,255,0.12)"}`,
          borderRadius: 16, padding: "13px 14px",
          transition: "border-color 0.2s",
        }}>
          <ExternalLink size={16} color="rgba(255,255,255,0.35)" style={{ flexShrink: 0 }} />
          <input
            autoFocus
            inputMode="url"
            type="url"
            placeholder="http://192.168.1.10:8560"
            value={value}
            onChange={(e) => { setValue(e.target.value); if (error) setError(null); }}
            onKeyDown={(e) => { if (e.key === "Enter") submit(); }}
            style={{
              flex: 1, background: "transparent", border: "none", outline: "none",
              color: "#fff", fontSize: 15, fontFamily: "ui-monospace, monospace",
              letterSpacing: -0.2, minWidth: 0,
            }}
          />
          {value && (
            <button
              onClick={() => { setValue(""); setError(null); }}
              style={{
                background: "rgba(255,255,255,0.1)", border: "none",
                color: "rgba(255,255,255,0.5)", cursor: "pointer",
                padding: "2px 6px", borderRadius: 6, fontSize: 12, lineHeight: 1,
                flexShrink: 0,
              }}
            >
              ✕
            </button>
          )}
        </div>

        {/* Ошибка */}
        {error && (
          <div style={{ display: "flex", alignItems: "center", gap: 8, color: "#FCA5A5", fontSize: 13 }}>
            <AlertTriangle size={14} style={{ flexShrink: 0 }} /> {error}
          </div>
        )}

        {/* Кнопка подключения */}
        <button
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
          Адрес сохраняется — следующий раз заполнится автоматически
        </p>
      </div>
    </div>
  );
}

export default ServerPicker;
