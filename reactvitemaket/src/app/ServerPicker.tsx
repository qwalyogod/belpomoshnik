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

type Candidate = { url: string; status: "checking" | "ok" | "fail" };

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

// WebRTC SDP — best-effort, не всегда даёт IPv4 (iOS фильтрует).
// Возвращаем уникальные IPv4-кандидаты.
async function discoverLocalIps(): Promise<string[]> {
  if (typeof window === "undefined") return [];
  const out = new Set<string>();
  try {
    const RTCPeer = (window as unknown as { RTCPeerConnection?: typeof RTCPeerConnection }).RTCPeerConnection;
    if (RTCPeer) {
      const pc = new RTCPeer({ iceServers: [] });
      pc.createDataChannel("");
      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);
      await new Promise<void>(r => setTimeout(r, 250));
      const lines = (pc.localDescription?.sdp ?? "").split("\n");
      for (const line of lines) {
        const m = line.match(/a=candidate:.*? (\d+\.\d+\.\d+\.\d+) \d+ typ/);
        if (m && m[1]) {
          const ip = m[1];
          // Отсеиваем явно бесполезные: 0.0.0.0, 169.254.* (link-local),
          // 127.* (loopback) — для кандидатов на сервер они не подходят.
          if (ip !== "0.0.0.0" && !ip.startsWith("127.") && !ip.startsWith("169.254.")) {
            out.add(ip);
          }
        }
      }
      pc.close();
    }
  } catch { /* ignore */ }
  return Array.from(out);
}

async function probeBase(url: string, timeoutMs = 2500): Promise<boolean> {
  try {
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), timeoutMs);
    const r = await fetch(`${url}/api/health`, { signal: ctrl.signal, cache: "no-store" });
    clearTimeout(t);
    return r.ok;
  } catch {
    return false;
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
  const [busy, setBusy] = useState(false);

  // eslint-disable-next-line react-hooks/rules-of-hooks
  useEffect(() => {
    if (window.location.protocol !== "capacitor:") {
      setOpen(false);
      return;
    }

    let saved: string | null = null;
    try {
      saved = localStorage.getItem(STORAGE_KEY);
      if (saved) setValue(saved);
    } catch { /* ignore */ }

    // Формируем стартовый список кандидатов. Первым — сохранённый,
    // затем — найденные WebRTC-кандидаты. Плюс в конец — localhost
    // как запасной (на некоторых эмуляторах WebRTC даёт пусто).
    (async () => {
      const localIps = await discoverLocalIps();
      console.info("[ServerPicker] local IPs from WebRTC:", localIps);

      const initial: Candidate[] = [];
      if (saved) initial.push({ url: saved, status: "checking" });
      for (const ip of localIps) {
        if (initial.some(c => c.url.startsWith(`http://${ip}:`))) continue;
        initial.push({ url: `http://${ip}:8560`, status: "checking" });
      }
      setCandidates(initial);

      // Параллельная проверка. Vite-url (порт 8560) → backend-url (порт 8060).
      await Promise.all(initial.map(async (c, idx) => {
        let probeUrl = c.url;
        try {
          const u = new URL(c.url);
          if (u.port === "8560" || u.port === "8550") u.port = "8060";
          probeUrl = u.toString().replace(/\/$/, "");
        } catch { /* keep as-is */ }
        const ok = await probeBase(probeUrl);
        console.info(`[ServerPicker] probe ${probeUrl} -> ${ok ? "OK" : "fail"}`);
        setCandidates(prev => prev.map((p, i) => i === idx ? { ...p, status: ok ? "ok" : "fail" } : p));
      }));
    })();

    setOpen(true);
  }, []);

  const submit = (override?: string) => {
    if (busy) return;
    const url = normalizeUrl(override ?? value);
    if (!url) {
      setError("Введите корректный URL, например http://192.168.1.10:8560");
      return;
    }
    console.info(`[ServerPicker] submit -> ${url}`);
    setBusy(true);
    try { localStorage.setItem(STORAGE_KEY, url); } catch { /* ignore */ }
    // Небольшая задержка, чтобы state ушёл, потом replace.
    setTimeout(() => {
      window.location.replace(url);
    }, 50);
  };

  if (!open) return null;

  const okCandidates = candidates.filter(c => c.status === "ok");
  const pendingCount = candidates.filter(c => c.status === "checking").length;
  const failedCount = candidates.filter(c => c.status === "fail").length;

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
          На ПК запустите{" "}
          <code style={{ fontFamily: "ui-monospace, monospace", fontSize: 13, color: "#7FA8FF", background: "rgba(127,168,255,0.1)", padding: "1px 5px", borderRadius: 5 }}>pnpm dev:all</code>.
          Ниже появятся серверы, до которых бэкенд ответил — тапните на рабочий.
          ПК и телефон — в одной Wi-Fi.
        </p>

        {/* Найденные кандидаты */}
        {candidates.length > 0 && (
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            <div style={{ fontSize: 11, letterSpacing: 0.4, textTransform: "uppercase", color: "rgba(255,255,255,0.35)" }}>
              Найденные серверы
            </div>

            {okCandidates.length === 0 && pendingCount > 0 && (
              <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, color: "rgba(255,255,255,0.55)" }}>
                <Loader2 size={14} style={{ animation: "belp-spin 1s linear infinite" }} /> Проверяем доступные серверы…
              </div>
            )}

            {okCandidates.map((c) => (
              <button
                key={c.url}
                type="button"
                onClick={() => submit(c.url)}
                disabled={busy}
                style={{
                  display: "flex", alignItems: "center", justifyContent: "space-between", gap: 10,
                  background: "rgba(0,86,255,0.18)",
                  border: "1px solid rgba(127,168,255,0.45)",
                  borderRadius: 14, padding: "13px 14px",
                  color: "#fff", fontSize: 14, fontFamily: "ui-monospace, monospace",
                  cursor: busy ? "wait" : "pointer",
                  WebkitTapHighlightColor: "transparent",
                  opacity: busy ? 0.5 : 1,
                }}
              >
                <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{c.url}</span>
                <CheckCircle2 size={16} color="#7FA8FF" style={{ flexShrink: 0 }} />
              </button>
            ))}

            {okCandidates.length === 0 && pendingCount === 0 && failedCount > 0 && (
              <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, color: "#FCA5A5" }}>
                <AlertTriangle size={14} style={{ flexShrink: 0 }} />
                Не нашли бэкенд. Проверьте, что pnpm dev:all запущен на ПК, и введите адрес вручную.
              </div>
            )}
          </div>
        )}

        {/* Поле ввода (ручной fallback) */}
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
              type="button"
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
          type="button"
          onClick={() => submit()}
          disabled={busy || !value.trim()}
          style={{
            height: 52, borderRadius: 16,
            background: busy || !value.trim() ? "rgba(0,86,255,0.4)" : "linear-gradient(135deg,#0056FF,#2277FF)",
            color: "#fff", fontSize: 16, fontWeight: 600, letterSpacing: -0.2,
            border: "none", cursor: busy || !value.trim() ? "not-allowed" : "pointer",
            boxShadow: "0 18px 36px -10px rgba(0,86,255,0.55)",
            transition: "opacity 0.15s, transform 0.1s",
            WebkitTapHighlightColor: "transparent",
          }}
        >
          {busy ? "Подключаем…" : "Подключиться"}
        </button>

        <p style={{ margin: 0, textAlign: "center", fontSize: 11, lineHeight: 1.5, color: "rgba(255,255,255,0.22)" }}>
          Адрес сохраняется — следующий раз заполнится автоматически
        </p>
      </div>
      <style>{`@keyframes belp-spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}

export default ServerPicker;
