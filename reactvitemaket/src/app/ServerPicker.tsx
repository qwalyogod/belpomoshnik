/**
 * ServerPicker — экран ввода URL dev-сервера.
 *
 * Показывается ТОЛЬКО в нативной Capacitor-оболочке (iOS/Android), при первом
 * запуске или после «Сбросить». В обычном браузере/Vite dev — невидим.
 *
 * Поведение:
 *  - При старте читает `localStorage["belpomoshnik.serverUrl"]`
 *  - Если URL сохранён — редиректит на него автоматически (один раз за сессию)
 *  - Если нет — показывает экран ввода
 *  - «Пропустить» — закрывает picker, приложение работает из бандла
 *  - «Сбросить» — очищает localStorage и возвращает экран ввода
 *    (вызывается через window.belpomoshnik.resetServer() из настроек)
 */
import { useEffect, useState } from "react";
import { Server, RefreshCw, ExternalLink, AlertTriangle, Package } from "lucide-react";

const STORAGE_KEY = "belpomoshnik.serverUrl";
const SKIP_KEY = "belpomoshnik.serverSkipped";

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
  const [value, setValue] = useState("");
  // eslint-disable-next-line react-hooks/rules-of-hooks
  const [error, setError] = useState<string | null>(null);
  // eslint-disable-next-line react-hooks/rules-of-hooks
  const [open, setOpen] = useState(false);
  // eslint-disable-next-line react-hooks/rules-of-hooks
  const [savedUrl, setSavedUrl] = useState<string | null>(null);

  // eslint-disable-next-line react-hooks/rules-of-hooks
  useEffect(() => {
    try {
      const skipped = localStorage.getItem(SKIP_KEY);
      const saved = localStorage.getItem(STORAGE_KEY);

      if (skipped) {
        // Пользователь нажал «Пропустить» — не показываем picker
        setOpen(false);
        return;
      }

      if (saved) {
        // URL сохранён — редиректим один раз за сессию
        setSavedUrl(saved);
        const flag = "belpomoshnik.redirectedOnce";
        if (!sessionStorage.getItem(flag)) {
          sessionStorage.setItem(flag, "1");
          window.location.replace(saved);
        }
        setOpen(false);
        return;
      }

      // Первый запуск — показываем picker
      setOpen(true);
    } catch {
      setOpen(true);
    }
  }, []);

  // Глобальный хук для кнопки «Сбросить сервер» из настроек
  // eslint-disable-next-line react-hooks/rules-of-hooks
  useEffect(() => {
    (window as unknown as { belpomoshnik?: Record<string, unknown> }).belpomoshnik = {
      ...((window as unknown as { belpomoshnik?: Record<string, unknown> }).belpomoshnik ?? {}),
      resetServer: () => {
        try {
          localStorage.removeItem(STORAGE_KEY);
          localStorage.removeItem(SKIP_KEY);
          sessionStorage.removeItem("belpomoshnik.redirectedOnce");
        } catch { /* ignore */ }
        setSavedUrl(null);
        setValue("");
        setError(null);
        setOpen(true);
      },
    };
  }, []);

  if (!open) return null;

  const submit = () => {
    const url = normalizeUrl(value);
    if (!url) {
      setError("Введите корректный URL, например http://192.168.1.10:8560");
      return;
    }
    try {
      localStorage.setItem(STORAGE_KEY, url);
      localStorage.removeItem(SKIP_KEY);
      sessionStorage.removeItem("belpomoshnik.redirectedOnce");
    } catch {
      setError("Не удалось сохранить (WebView storage недоступен)");
      return;
    }
    setError(null);
    window.location.replace(url);
  };

  const skip = () => {
    try {
      localStorage.setItem(SKIP_KEY, "1");
      localStorage.removeItem(STORAGE_KEY);
    } catch { /* ignore */ }
    setOpen(false);
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
        padding: "calc(env(safe-area-inset-top) + 24px) 24px calc(env(safe-area-inset-bottom) + 24px)",
        fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Text', system-ui, sans-serif",
      }}
    >
      <div
        style={{
          margin: "auto",
          width: "100%",
          maxWidth: 380,
          display: "flex",
          flexDirection: "column",
          gap: 16,
        }}
      >
        {/* Logo row */}
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span
            style={{
              display: "grid",
              placeItems: "center",
              width: 40,
              height: 40,
              borderRadius: 14,
              background: "linear-gradient(135deg,#0056FF,#2277FF)",
              boxShadow: "0 8px 20px -6px rgba(0,86,255,0.5)",
            }}
          >
            <Server size={20} color="#fff" />
          </span>
          <div style={{ fontSize: 20, fontWeight: 600, letterSpacing: -0.3 }}>
            Укажите сервер
          </div>
        </div>

        <p style={{ margin: 0, fontSize: 14, lineHeight: 1.55, color: "rgba(255,255,255,0.6)" }}>
          Запустите на компьютере <code style={{ fontFamily: "ui-monospace, monospace", color: "#7FA8FF" }}>pnpm dev</code>{" "}
          и введите адрес из строки{" "}
          <code style={{ fontFamily: "ui-monospace, monospace", color: "#7FA8FF" }}>Network:</code>.
          Или нажмите «Пропустить» — приложение откроется из встроенной версии.
        </p>

        {/* Input */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            background: "rgba(255,255,255,0.06)",
            border: `1px solid ${error ? "rgba(252,165,165,0.5)" : "rgba(255,255,255,0.1)"}`,
            borderRadius: 16,
            padding: "12px 14px",
            transition: "border-color 0.2s",
          }}
        >
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
              flex: 1,
              background: "transparent",
              border: "none",
              outline: "none",
              color: "#fff",
              fontSize: 15,
              fontFamily: "ui-monospace, monospace",
              letterSpacing: -0.1,
            }}
          />
          {value && (
            <button
              onClick={() => { setValue(""); setError(null); }}
              style={{ background: "none", border: "none", color: "rgba(255,255,255,0.3)", cursor: "pointer", padding: 2 }}
            >
              ✕
            </button>
          )}
        </div>

        {error && (
          <div style={{ display: "flex", alignItems: "center", gap: 8, color: "#FCA5A5", fontSize: 13 }}>
            <AlertTriangle size={14} />
            {error}
          </div>
        )}

        {/* Primary CTA */}
        <button
          onClick={submit}
          style={{
            height: 50,
            borderRadius: 14,
            background: "linear-gradient(135deg,#0056FF,#2277FF)",
            color: "#fff",
            fontSize: 15,
            fontWeight: 600,
            letterSpacing: -0.1,
            border: "none",
            cursor: "pointer",
            boxShadow: "0 16px 34px -10px rgba(0,86,255,0.5)",
          }}
        >
          Подключиться
        </button>

        {/* Skip button */}
        <button
          onClick={skip}
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 6,
            height: 44,
            background: "rgba(255,255,255,0.06)",
            border: "1px solid rgba(255,255,255,0.1)",
            borderRadius: 14,
            color: "rgba(255,255,255,0.7)",
            fontSize: 14,
            fontWeight: 500,
            cursor: "pointer",
          }}
        >
          <Package size={15} /> Пропустить — встроенная версия
        </button>

        {/* Reset saved */}
        {savedUrl && (
          <button
            onClick={() => {
              try { localStorage.removeItem(STORAGE_KEY); } catch { /* ignore */ }
              setSavedUrl(null);
              setValue("");
            }}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: 6,
              height: 36,
              background: "transparent",
              border: "none",
              color: "rgba(255,255,255,0.35)",
              fontSize: 12,
              cursor: "pointer",
            }}
          >
            <RefreshCw size={12} /> Сбросить сохранённый адрес
          </button>
        )}

        <p style={{ margin: 0, fontSize: 11, lineHeight: 1.5, color: "rgba(255,255,255,0.3)" }}>
          ПК и телефон должны быть в одной Wi-Fi. Адрес сохраняется на устройстве.
        </p>
      </div>
    </div>
  );
}

export default ServerPicker;
