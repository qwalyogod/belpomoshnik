/**
 * ServerPicker — экран выбора сервера.
 *
 * Появляется при каждом запуске нативного Capacitor-приложения (iOS/Android).
 * В браузере/Vite dev — невидим.
 *
 * - Поле предзаполнено последним использованным URL (localStorage)
 * - «Подключиться» → сохраняет URL и редиректит на него
 * - «Пропустить» → закрывает picker, приложение работает из бандла
 */
import { useEffect, useState } from "react";
import { Server, ExternalLink, AlertTriangle, Package } from "lucide-react";

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
  if (typeof window === "undefined" || !isCapacitorShell()) return null;

  // eslint-disable-next-line react-hooks/rules-of-hooks
  const [open, setOpen] = useState(true);
  // eslint-disable-next-line react-hooks/rules-of-hooks
  const [value, setValue] = useState(() => {
    try { return localStorage.getItem(STORAGE_KEY) ?? ""; } catch { return ""; }
  });
  // eslint-disable-next-line react-hooks/rules-of-hooks
  const [error, setError] = useState<string | null>(null);

  // Закрываем если уже переданы на dev-сервер (чтобы не мигать после редиректа)
  // eslint-disable-next-line react-hooks/rules-of-hooks
  useEffect(() => {
    const saved = (() => { try { return localStorage.getItem(STORAGE_KEY); } catch { return null; } })();
    if (saved && window.location.origin.startsWith(saved)) {
      setOpen(false);
    }
  }, []);

  if (!open) return null;

  const submit = () => {
    const url = normalizeUrl(value);
    if (!url) {
      setError("Введите корректный URL, например http://192.168.1.10:8560");
      return;
    }
    try { localStorage.setItem(STORAGE_KEY, url); } catch { /* ignore */ }
    window.location.replace(url);
  };

  const skip = () => setOpen(false);

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
        padding: "calc(env(safe-area-inset-top) + 24px) 24px calc(env(safe-area-inset-bottom) + 24px)",
        fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Text', system-ui, sans-serif",
      }}
    >
      <div style={{ margin: "auto", width: "100%", maxWidth: 380, display: "flex", flexDirection: "column", gap: 16 }}>

        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{
            display: "grid", placeItems: "center", width: 40, height: 40,
            borderRadius: 14, background: "linear-gradient(135deg,#0056FF,#2277FF)",
            boxShadow: "0 8px 20px -6px rgba(0,86,255,0.5)",
          }}>
            <Server size={20} color="#fff" />
          </span>
          <div style={{ fontSize: 20, fontWeight: 600, letterSpacing: -0.3 }}>Белпомощник</div>
        </div>

        <p style={{ margin: 0, fontSize: 14, lineHeight: 1.55, color: "rgba(255,255,255,0.6)" }}>
          Введите адрес сервера из строки{" "}
          <code style={{ fontFamily: "ui-monospace, monospace", color: "#7FA8FF" }}>Network:</code>{" "}
          в терминале (<code style={{ fontFamily: "ui-monospace, monospace", color: "#7FA8FF" }}>pnpm dev</code>).
          Или нажмите «Пропустить» для встроенной версии.
        </p>

        <div style={{
          display: "flex", alignItems: "center", gap: 8,
          background: "rgba(255,255,255,0.06)",
          border: `1px solid ${error ? "rgba(252,165,165,0.5)" : "rgba(255,255,255,0.1)"}`,
          borderRadius: 16, padding: "12px 14px",
        }}>
          <ExternalLink size={16} color="rgba(255,255,255,0.4)" />
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
              color: "#fff", fontSize: 15, fontFamily: "ui-monospace, monospace", letterSpacing: -0.1,
            }}
          />
          {value && (
            <button onClick={() => { setValue(""); setError(null); }}
              style={{ background: "none", border: "none", color: "rgba(255,255,255,0.3)", cursor: "pointer", padding: 2, fontSize: 14 }}>
              ✕
            </button>
          )}
        </div>

        {error && (
          <div style={{ display: "flex", alignItems: "center", gap: 8, color: "#FCA5A5", fontSize: 13 }}>
            <AlertTriangle size={14} /> {error}
          </div>
        )}

        <button onClick={submit} style={{
          height: 50, borderRadius: 14,
          background: "linear-gradient(135deg,#0056FF,#2277FF)",
          color: "#fff", fontSize: 15, fontWeight: 600, letterSpacing: -0.1,
          border: "none", cursor: "pointer",
          boxShadow: "0 16px 34px -10px rgba(0,86,255,0.5)",
        }}>
          Подключиться
        </button>

        <button onClick={skip} style={{
          display: "flex", alignItems: "center", justifyContent: "center", gap: 6,
          height: 44, background: "rgba(255,255,255,0.06)",
          border: "1px solid rgba(255,255,255,0.1)", borderRadius: 14,
          color: "rgba(255,255,255,0.7)", fontSize: 14, fontWeight: 500, cursor: "pointer",
        }}>
          <Package size={15} /> Пропустить — встроенная версия
        </button>

        <p style={{ margin: 0, fontSize: 11, lineHeight: 1.5, color: "rgba(255,255,255,0.3)" }}>
          ПК и телефон должны быть в одной Wi-Fi. Последний адрес запоминается.
        </p>
      </div>
    </div>
  );
}

export default ServerPicker;
