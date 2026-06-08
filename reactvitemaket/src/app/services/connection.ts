/**
 * Глобальный подписчик на состояние подключения.
 *
 * Принцип: «честный» баннер. Показываем ТОЛЬКО если прямо сейчас нет связи.
 * Источник истины — результат последнего health-ping + navigator.onLine.
 *
 * Алгоритм:
 * 1. Каждые 10 секунд активный пинг на ${API_BASE_URL}/api/health.
 * 2. Пинг OK → status = "online", баннер скрыт.
 * 3. Пинг FAIL (network error или HTTP ≥ 400) → status = "server-error",
 *    баннер виден.
 * 4. navigator.onLine === false → status = "offline", баннер виден.
 * 5. window события online/offline обновляют статус немедленно.
 *
 * Никаких «залипающих» флагов — state всегда отражает реальность.
 *
 * В нативной WebView пробрасывается через postMessage в обёртку
 * (для нативных экранов ошибок, если будут).
 */

import { useSyncExternalStore } from "react";
import { API_BASE_URL } from "./api";

export type ConnectionStatus = "online" | "offline" | "server-error";

type Listener = (status: ConnectionStatus) => void;

// Начальный статус — сразу запускаем первый пинг из startHealthLoop.
let currentStatus: ConnectionStatus = "online";
const listeners = new Set<Listener>();
let activeProbe: Promise<boolean> | null = null;

function setStatus(next: ConnectionStatus) {
  if (next === currentStatus) return;
  currentStatus = next;
  for (const cb of listeners) cb(currentStatus);
  notifyNativeShell(currentStatus);
}

function deriveStatus(): ConnectionStatus {
  if (typeof navigator !== "undefined" && navigator.onLine === false) return "offline";
  // Если последний пинг был fail — server-error. Иначе online.
  return currentStatus === "server-error" ? "server-error" : "online";
}

function notifyNativeShell(status: ConnectionStatus) {
  if (typeof window === "undefined") return;
  const w = window as unknown as {
    flet?: { postMessage?: (data: string) => void; page?: { postMessage?: (data: string) => void } };
  };
  const payload = JSON.stringify({ type: "belpomoshchik:connection", status });
  try {
    if (w.flet?.postMessage) w.flet.postMessage(payload);
    else if (w.flet?.page?.postMessage) w.flet.page.postMessage(payload);
  } catch {
    /* ignore */
  }
}

if (typeof window !== "undefined") {
  window.addEventListener("online", () => setStatus(deriveStatus()));
  window.addEventListener("offline", () => setStatus("offline"));
}

/**
 * Активный пинг бэкенда. Возвращает true если HTTP 2xx, иначе false.
 * Дедупликация: если пинг уже идёт — переиспользуем тот же promise.
 */
export function pingHealth(): Promise<boolean> {
  if (typeof window === "undefined") return Promise.resolve(false);
  if (activeProbe) return activeProbe;
  const url = `${API_BASE_URL}/api/health`;
  activeProbe = (async () => {
    try {
      const ctrl = new AbortController();
      const t = setTimeout(() => ctrl.abort(), 5000);
      const r = await fetch(url, { method: "GET", cache: "no-store", signal: ctrl.signal });
      clearTimeout(t);
      return r.ok;
    } catch {
      return false;
    } finally {
      activeProbe = null;
    }
  })();
  return activeProbe;
}

/**
 * Фоновый цикл активного пинга. Каждые 10 сек пингует бэкенд и
 * немедленно обновляет статус. Запускается из main.tsx ОДИН раз.
 */
export function startHealthLoop(): () => void {
  if (typeof window === "undefined") return () => {};
  console.info("[belp:health-loop] start, API_BASE_URL =", API_BASE_URL);
  let stopped = false;

  const tick = async () => {
    if (stopped) return;
    const ok = await pingHealth();
    if (stopped) return;
    console.info(`[belp:health-loop] ping -> ${ok ? "OK" : "FAIL"}`);
    if (ok) {
      setStatus(deriveStatus()); // online (если navigator.onLine)
    } else {
      setStatus(deriveStatus() === "offline" ? "offline" : "server-error");
    }
  };

  // Сразу первый пинг — без задержки.
  void tick();
  const handle = window.setInterval(tick, 10_000);
  return () => {
    stopped = true;
    window.clearInterval(handle);
  };
}

export function getStatus(): ConnectionStatus {
  return currentStatus;
}

export function subscribeConnection(cb: Listener): () => void {
  listeners.add(cb);
  return () => {
    listeners.delete(cb);
  };
}

export function useConnectionStatus(): ConnectionStatus {
  return useSyncExternalStore(subscribeConnection, getStatus, getStatus);
}
