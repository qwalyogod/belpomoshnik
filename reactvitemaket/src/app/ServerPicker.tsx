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
import { Server, ExternalLink, AlertTriangle, CheckCircle2, Loader2 } from "lucide-react";

const STORAGE_KEY = "belpomoshnik.serverUrl";

type Candidate = { url: string; status: "checking" | "ok" | "fail"; detail?: string };

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

// Резолвим все IPv4 у текущего устройства. На iPhone Capacitor WKWebView
// видит все Wi-Fi/VPN интерфейсы; пробуем их как кандидаты.
async function discoverLocalCandidates(): Promise<string[]> {
  if (typeof window === "undefined") return [];
  const cands: string[] = [];
  // Попытка через WebRTC — даёт все локальные IPv4 (best-effort, не всегда работает).
  try {
    const RTCPeer = (window as unknown as { RTCPeerConnection?: typeof RTCPeerConnection }).RTCPeerConnection;
    if (RTCPeer) {
      const pc = new RTCPeer({ iceServers: [] });
      pc.createDataChannel("");
      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);
      await new Promise<void>(r => setTimeout(r, 200));
      const lines = (pc.localDescription?.sdp ?? "").split("\n");
      for (const line of lines) {
        const m = line.match(/a=candidate:.*? (\d+\.\d+\.\d+\.\d+) \d+ typ/);
        if (m && m[1]) cands.push(m[1]);
      }
      pc.close();
    }
  } catch { /* ignore */ }
  return Array.from(new Set(cands));
}

async function probeBase(url: string, timeoutMs = 2500): Promise<"ok" | "fail"> {
  // Пробуем /api/health (тот же endpoint, что ConnectionBanner). На 2xx — OK.
  try {
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), timeoutMs);
    const r = await fetch(`${url}/api/health`, { signal: ctrl.signal, cache: "no-store" });
    clearTimeout(t);
    return r.ok ? "ok" : "fail";
  } catch {
    return "fail";
  }
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
  const [candidates, setCandidates] = useState<Candidate[]>([]);

  // eslint-disable-next-line react-hooks/rules-of-hooks
  useEffect(() => {
    if (window.location.protocol !== "capacitor:") {
      setOpen(false);
      return;
    }

    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) setValue(saved);
    } catch { /* ignore */ }

    // Автопоиск кандидатов: пробуем сохранённый URL + найденные локальные IP.
    (async () => {
      const localIps = await discoverLocalCandidates();
      const initial: Candidate[] = [];
      // Сохранённый — первый.
      try {
        const saved = localStorage.getItem(STORAGE_KEY);
        if (saved) initial.push({ url: saved, status: "checking" });
      } catch { /* ignore */ }
      // Локальные IPv4 — http://<ip>:8060 (бэк) и сразу с портом 8560 не проверяем,
      // потому что dev бэк идёт на 8060. Но пикер ожидает Vite-адрес (8560),
      // а бэк уже подтверждён через /api/health, так что покажем "http://<ip>:8560".
      for (const ip of localIps) {
        if (initial.some(c => c.url.startsWith(`http://${ip}:`))) continue;
        initial.push({ url: `http://${ip}:8560`, status: "checking" });
      }
      setCandidates(initial);

      // Параллельно проверяем каждый.
      await Promise.all(initial.map(async (c, idx) => {
        // Преобразуем Vite-url (8560) → backend-url (8060) для health-проверки.
        let probeUrl = c.url;
        try {
          const u = new URL(c.url);
          if (u.port === "8560" || u.port === "8550") u.port = "8060";
          probeUrl = u.toString().replace(/\/$/, "");
        } catch { /* keep as-is */ }
        const status = await probeBase(probeUrl);
        setCandidates(prev => prev.map((p, i) => i === idx ? { ...p, status } : p));
      }));
    })();

    setOpen(true);
  }, []);

  if (!open) return null;

  const submit = (override?: string) => {
    const url = normalizeUrl(override ?? value);
    if (!url) {
      setError("Введите корректный URL, например http://192.168.1.10:8560");
      return;
    }
    try { localStorage.setItem(STORAGE_KEY, url); } catch { /* ignore */ }
    window.location.replace(url);
  };

  // Кандидаты, до которых бэк ответил OK — кликабельные.
  const okCandidates = candidates.filter(c => c.status === "ok");
  const pendingCandidates = candidates.filter(c => c.status === "checking");
  const failedCandidates = candidates.filter(c => c.status === "fail");

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

        {/* Авто-найденные кандидаты (если есть рабочие — кликабельные) */}
        {candidates.length > 0 && (
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            <div style={{ fontSize: 11, letterSpacing: 0.4, textTransform: "uppercase", color: "rgba(255,255,255,0.35)" }}>
              Найденные серверы
            </div>
            {okCandidates.length === 0 && pendingCandidates.length > 0 && (
              <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, color: "rgba(255,255,255,0.55)" }}>
                <Loader2 size={14} style={{ animation: "spin 1s linear infinite" }} /> Проверяем доступные серверы…
              </div>
            )}
            {okCandidates.map((c) => (
              <button
                key={c.url}
                onClick={() => submit(c.url)}
                style={{
                  display: "flex", alignItems: "center", justifyContent: "space-between", gap: 10,
                  background: "rgba(0,86,255,0.12)",
                  border: "1px solid rgba(127,168,255,0.4)",
                  borderRadius: 14, padding: "12px 14px",
                  color: "#fff", fontSize: 14, fontFamily: "ui-monospace, monospace",
                  cursor: "pointer", WebkitTapHighlightColor: "transparent",
                  transition: "transform 0.1s, background 0.15s",
                }}
                onTouchStart={(e) => (e.currentTarget.style.background = "rgba(0,86,255,0.22)")}
                onTouchEnd={(e) => (e.currentTarget.style.background = "rgba(0,86,255,0.12)")}
              >
                <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{c.url}</span>
                <CheckCircle2 size={16} color="#7FA8FF" style={{ flexShrink: 0 }} />
              </button>
            ))}
            {okCandidates.length === 0 && pendingCandidates.length === 0 && failedCandidates.length > 0 && (
              <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, color: "#FCA5A5" }}>
                <AlertTriangle size={14} style={{ flexShrink: 0 }} />
                Не нашли бэкенд. Проверьте, что pnpm dev:all запущен на ПК.
              </div>
            )}
          </div>
        )}

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
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}

export default ServerPicker;
