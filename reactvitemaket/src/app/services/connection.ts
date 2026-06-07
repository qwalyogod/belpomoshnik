/**
 * Глобальный подписчик на состояние подключения.
 *
 * Источник истины — два слоя:
 * - navigator.onLine + события online/offline window (быстро и точно
 *   для «упал Wi-Fi»).
 * - publicContentStatus / publicContentError из стора (для случая
 *   «интернет есть, но сервер вернул 5xx»).
 *
 * Стейт: "online" | "offline" | "server-error".
 *
 * В нативной Flet-обёртке (src/mobile_webview.py) подписка дополнительно
 * пробрасывается через postMessage в WebView — обёртка показывает свой
 * «нативный» экран «Нет подключения / Сервис временно недоступен».
 */

import { useEffect, useSyncExternalStore } from "react";

export type ConnectionStatus = "online" | "offline" | "server-error";

type Listener = (status: ConnectionStatus) => void;

let currentStatus: ConnectionStatus =
  typeof navigator !== "undefined" && navigator.onLine === false
    ? "offline"
    : "online";

let serverErrorDetected = false;
const listeners = new Set<Listener>();

function emit() {
  const next = serverErrorDetected
    ? "server-error"
    : typeof navigator !== "undefined" && navigator.onLine === false
      ? "offline"
      : "online";
  if (next === currentStatus) return;
  currentStatus = next;
  for (const cb of listeners) cb(currentStatus);
  notifyNativeShell(currentStatus);
}

function notifyNativeShell(status: ConnectionStatus) {
  if (typeof window === "undefined") return;
  // Flet / Capacitor / WebView: оборачиваем статус в сообщение, которое
  // обёртка (src/mobile_webview.py) ловит в on_message и рисует
  // соответствующий «нативный» экран (show_offline / show_server_error).
  const w = window as unknown as {
    flet?: { postMessage?: (data: string) => void; page?: { postMessage?: (data: string) => void } };
    Capacitor?: { isNativePlatform?: () => boolean };
  };
  const payload = JSON.stringify({ type: "belpomoshchik:connection", status });
  try {
    if (w.flet?.postMessage) w.flet.postMessage(payload);
    else if (w.flet?.page?.postMessage) w.flet.page.postMessage(payload);
    // Иначе просто ничего — React-баннер всё равно покажется через подписку.
  } catch {
    /* postMessage может не существовать в обычном браузере — это нормально. */
  }
}

if (typeof window !== "undefined") {
  window.addEventListener("online", () => emit());
  window.addEventListener("offline", () => emit());
}

export function setServerError(detected: boolean): void {
  if (serverErrorDetected === detected) return;
  serverErrorDetected = detected;
  emit();
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

export function pingHealth(): Promise<boolean> {
  // Используем GET /api/health (см. src/backend/app.py). Возвращаем true
  // если HTTP-статус 2xx, иначе false. При network failure — тоже false.
  return fetch("/api/health", { method: "GET" })
    .then(r => r.ok)
    .catch(() => false);
}
