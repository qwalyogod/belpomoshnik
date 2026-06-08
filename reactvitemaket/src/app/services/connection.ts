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
import { API_BASE_URL } from "./api";

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
  // GET {API_BASE_URL}/api/health (см. src/backend/app.py).
  // Относительный /api/health здесь не годится: в Capacitor WebView он
  // уйдёт на Vite origin (:8560), а бэкенд на :8060 — это разные хосты.
  // Возвращаем true если HTTP-статус 2xx, иначе false. При network failure — false.
  // При успехе сбрасываем server-error, чтобы баннер исчез, если до этого
  // loadPublicContent при cold start'е зафиксировал «все 5 упали» и больше
  // не повторяется.
  const url = `${API_BASE_URL}/api/health`;
  return fetch(url, { method: "GET", cache: "no-store" })
    .then(r => {
      if (r.ok) {
        setServerError(false);
        return true;
      }
      return false;
    })
    .catch(() => false);
}

/**
 * Запустить фоновый health-ping, который самовосстанавливает баннер.
 *
 * Проблема: loadPublicContent срабатывает один раз при mount. Если при cold
 * start'е бэкенд не ответил (был выключен / WebView опередил dev-сервер),
 * serverErrorDetected залипает в true навсегда — даже после того как бэк
 * поднимется и обычные fetch'и начнут возвращать 200.
 *
 * Фоновая проверка раз в 15 сек: на 1 успехе сбрасывает serverErrorDetected.
 *
 * Запускается ВЕЗДЕ (включая обычный браузер / Vite dev), потому что в WebView
 * на http://<host>:8560 Capacitor.isNativePlatform() может вернуть false —
 * иначе фикс не работает в самом важном для нас сценарии. 15-секундный
 * /api/health — копеечный трафик.
 */
export function startBackgroundHealthLoop(): () => void {
  if (typeof window === "undefined") return () => {};
  let consecutiveFails = 0;
  const tick = async () => {
    const ok = await pingHealth();
    if (ok) {
      consecutiveFails = 0;
    } else {
      consecutiveFails = Math.min(consecutiveFails + 1, 10);
    }
  };
  const handle = window.setInterval(tick, 15_000);
  // Сразу первый тик — чтобы не ждать 15 сек после mount.
  void tick();
  return () => window.clearInterval(handle);
}
