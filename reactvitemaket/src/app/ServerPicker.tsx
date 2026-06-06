/**
 * ServerPicker — экран ввода URL React-сервера.
 *
 * Используется в dev-сборке на iPhone/Android, пока приложение ходит за
 * фронтендом на ПК разработчика. При фиксированном URL (production) этот
 * компонент можно удалить — приложение просто пойдёт по `server.url` из
 * capacitor.config.json.
 *
 * Логика:
 *  - при старте читаем `localStorage["belpomoshnik.serverUrl"]`
 *  - если есть — НЕ показываем picker, приложение рендерится как обычно
 *  - если нет — picker перекрывает экран и блокирует навигацию
 *  - при сохранении пишем в localStorage и редиректим на URL
 *  - «Сбросить» очищает localStorage и возвращает picker (кнопка из настроек)
 *
 * localStorage в Capacitor WebView живёт на origin самого приложения
 * (capacitor://localhost), а вводимый URL — это origin следующей страницы.
 * Это нормально: нам нужно лишь сохранить строку, а не шарить сессию.
 */
import { useEffect, useState } from "react";
import { Server, RefreshCw, ExternalLink, AlertTriangle } from "lucide-react";

const STORAGE_KEY = "belpomoshnik.serverUrl";

function normalizeUrl(raw: string): string | null {
  const s = raw.trim();
  if (!s) return null;
  // Добавим http://, если пользователь ввёл просто IP/домен
  const withScheme = /^https?:\/\//i.test(s) ? s : `http://${s}`;
  try {
    const u = new URL(withScheme);
    // Запретим заведомо опасные схемы
    if (u.protocol !== "http:" && u.protocol !== "https:") return null;
    // Хвостовой слэш для origin-форм не нужен, но оставляем pathname если есть
    return u.toString().replace(/\/$/, "");
  } catch {
    return null;
  }
}

function readSavedUrl(): string | null {
  try {
    return localStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

function isCapacitorShell(): boolean {
  // Picker нужен ТОЛЬКО в Capacitor-сборке (мобильное приложение).
  // В обычном вебе (Vite dev, продакшен) он не должен появляться.
  if (typeof window === "undefined") return false;
  const cap = (window as unknown as { Capacitor?: { isNativePlatform?: () => boolean } })
    .Capacitor;
  if (cap && typeof cap.isNativePlatform === "function") {
    return cap.isNativePlatform();
  }
  return false;
}

export function ServerPicker() {
  // Picker активен только в Capacitor (нативная оболочка). В обычном вебе/Vite
  // dev — return null, чтобы не перекрывать основной UI.
  if (typeof window === "undefined" || !isCapacitorShell()) {
    return null;
  }

  const [value, setValue] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState<string | null>(null);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const s = readSavedUrl();
    setSaved(s);
    // Если URL уже сохранён — picker закрыт, приложение рендерится.
    // Но оставляем hook для кнопки «Сбросить» из настроек.
    setOpen(!s);
  }, []);

  // Глобальный хук: SettingsPage дёргает `window.belpomoshnik.resetServer()`.
  useEffect(() => {
    (window as unknown as { belpomoshnik?: Record<string, unknown> }).belpomoshnik = {
      ...((window as unknown as { belpomoshnik?: Record<string, unknown> }).belpomoshnik || {}),
      resetServer: () => {
        try {
          localStorage.removeItem(STORAGE_KEY);
        } catch {
          /* ignore */
        }
        setSaved(null);
        setOpen(true);
      },
    };
  }, []);

  if (!open) {
    // Если picker закрыт и есть сохранённый URL — пробрасываем пользователя
    // на dev-сервер. На production-сборке (с зашитым server.url) этого не будет,
    // потому что saved будет null и условие ниже не сработает.
    if (saved && typeof window !== "undefined") {
      const currentOrigin = window.location.origin;
      if (!currentOrigin.startsWith(saved)) {
        // Запускаем только один раз на загрузку
        const flag = "belpomoshnik.redirectedOnce";
        if (!sessionStorage.getItem(flag)) {
          sessionStorage.setItem(flag, "1");
          window.location.replace(saved);
        }
      }
    }
    return null;
  }

  const submit = () => {
    const url = normalizeUrl(value);
    if (!url) {
      setError("Введите корректный URL, например http://192.168.1.10:8560");
      return;
    }
    try {
      localStorage.setItem(STORAGE_KEY, url);
    } catch {
      setError("Не удалось сохранить (WebView storage недоступен)");
      return;
    }
    setError(null);
    // Сбросим флаг редиректа, чтобы он сработал
    try {
      sessionStorage.removeItem("belpomoshnik.redirectedOnce");
    } catch {
      /* ignore */
    }
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
        padding: "calc(env(safe-area-inset-top) + 24px) 24px calc(env(safe-area-inset-bottom) + 24px)",
        fontFamily:
          "-apple-system, BlinkMacSystemFont, 'SF Pro Text', system-ui, sans-serif",
      }}
    >
      <div
        style={{
          margin: "auto",
          width: "100%",
          maxWidth: 380,
          display: "flex",
          flexDirection: "column",
          gap: 20,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span
            style={{
              display: "grid",
              placeItems: "center",
              width: 36,
              height: 36,
              borderRadius: 12,
              background: "linear-gradient(135deg,#0056FF,#2277FF)",
            }}
          >
            <Server size={18} color="#fff" />
          </span>
          <div style={{ fontSize: 20, fontWeight: 600, letterSpacing: -0.2 }}>
            Укажите сервер
          </div>
        </div>

        <p style={{ margin: 0, fontSize: 14, lineHeight: 1.5, color: "rgba(255,255,255,0.6)" }}>
          Приложение пока работает в режиме разработки и должно получать интерфейс
          с компьютера. Введите адрес Vite-сервера (виден в терминале:{" "}
          <code style={{ fontFamily: "ui-monospace, monospace", color: "#7FA8FF" }}>
            Network: http://&lt;IP&gt;:8560
          </code>
          ).
        </p>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            background: "rgba(255,255,255,0.06)",
            border: "1px solid rgba(255,255,255,0.1)",
            borderRadius: 16,
            padding: "12px 14px",
          }}
        >
          <ExternalLink size={16} color="rgba(255,255,255,0.4)" />
          <input
            autoFocus
            inputMode="url"
            type="url"
            placeholder="http://192.168.1.10:8560"
            value={value}
            onChange={(e) => {
              setValue(e.target.value);
              if (error) setError(null);
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter") submit();
            }}
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
        </div>

        {error && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              color: "#FCA5A5",
              fontSize: 13,
            }}
          >
            <AlertTriangle size={14} />
            {error}
          </div>
        )}

        <button
          onClick={submit}
          style={{
            height: 48,
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
          Открыть
        </button>

        {saved && (
          <button
            onClick={() => {
              try {
                localStorage.removeItem(STORAGE_KEY);
              } catch {
                /* ignore */
              }
              setSaved(null);
              setError(null);
              setValue("");
            }}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: 6,
              height: 40,
              background: "transparent",
              border: "none",
              color: "rgba(255,255,255,0.4)",
              fontSize: 13,
              cursor: "pointer",
            }}
          >
            <RefreshCw size={12} /> Сбросить сохранённый адрес
          </button>
        )}

        <p style={{ margin: 0, fontSize: 11, lineHeight: 1.5, color: "rgba(255,255,255,0.35)" }}>
          ПК и телефон должны быть в одной Wi-Fi. URL сохраняется на устройстве.
          В production-сборке (когда приложение зальётся на сервер) этот экран
          уберут.
        </p>
      </div>
    </div>
  );
}

export default ServerPicker;
