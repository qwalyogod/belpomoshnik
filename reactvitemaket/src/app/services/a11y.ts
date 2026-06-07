// v1.1 (P8): real accessibility + push + privacy helpers.
// Применяет настройки к DOM (font-scale, high-contrast) и управляет
// Notification API + определением native-оболочки (Capacitor / Flet / WebView).
//
// Использовать в корне приложения после hydrate настроек:
//   useEffect(() => applyAccessibilitySettings(settings), [settings]);
import type { Settings } from "../data/types";

const STYLE_ID = "belp-a11y-style";
const HC_CLASS = "belp-high-contrast";
const LF_CLASS = "belp-large-font";

function isNativeShell(): boolean {
  if (typeof window === "undefined") return false;
  const w = window as unknown as {
    Capacitor?: { isNativePlatform?: () => boolean };
    flet?: unknown;
    ReactNativeWebView?: unknown;
  };
  if (w.Capacitor?.isNativePlatform?.()) return true;
  if (w.flet) return true;
  if (w.ReactNativeWebView) return true;
  // WebView UA heuristic: строгий матч по токенам iOS/Android WebView, не Safari/Chrome.
  const ua = navigator.userAgent || "";
  return /; (wv\)|WebView\)|\bFB_IAB\b|\bFBAN\b)/i.test(ua);
}

export function isNative(): boolean {
  return isNativeShell();
}

export function applyAccessibilitySettings(settings: Settings | undefined | null): void {
  if (typeof document === "undefined" || !settings) return;
  const root = document.documentElement;

  // --- Large font: реально меняем CSS scale на <html>. ---
  if (settings.accessibility.largeFont) {
    if (!root.classList.contains(LF_CLASS)) root.classList.add(LF_CLASS);
    root.style.fontSize = "18px";
  } else {
    if (root.classList.contains(LF_CLASS)) root.classList.remove(LF_CLASS);
    root.style.fontSize = "";
  }

  // --- High contrast: ставим data-атрибут + добавляем CSS-переопределения. ---
  if (settings.accessibility.highContrast) {
    if (!root.classList.contains(HC_CLASS)) root.classList.add(HC_CLASS);
    ensureHighContrastStyle();
  } else {
    if (root.classList.contains(HC_CLASS)) root.classList.remove(HC_CLASS);
    removeHighContrastStyle();
  }
}

function ensureHighContrastStyle(): void {
  if (document.getElementById(STYLE_ID)) return;
  const style = document.createElement("style");
  style.id = STYLE_ID;
  // Минимальный набор переопределений: усиливаем контраст текста и границ.
  // Не ломаем токены, а добавляем поверх — выключается удалением <style>.
  style.textContent = `
    html.belp-high-contrast {
      --a11y-text: #000;
      --a11y-text-dim: #1a1a1a;
      --a11y-border: #000;
    }
    html.belp-high-contrast body { background: #fff !important; }
    html.belp-high-contrast .text-black\\/55,
    html.belp-high-contrast .text-black\\/50,
    html.belp-high-contrast .text-black\\/45,
    html.belp-high-contrast .text-black\\/40,
    html.belp-high-contrast .text-white\\/55,
    html.belp-high-contrast .text-white\\/50,
    html.belp-high-contrast .text-white\\/45,
    html.belp-high-contrast .text-white\\/40 {
      color: #000 !important;
      opacity: 1 !important;
    }
    html.belp-high-contrast [class*="border-black\\/"],
    html.belp-high-contrast [class*="border-white\\/"] {
      border-color: #000 !important;
    }
    html.dark.belp-high-contrast body { background: #000 !important; }
    html.dark.belp-high-contrast { color-scheme: dark; }
  `;
  document.head.appendChild(style);
}

function removeHighContrastStyle(): void {
  document.getElementById(STYLE_ID)?.remove();
}

/* --- Push: Notification API (web). На mobile Capacitor/Flet покажут
   по-другому — см. applyPushPermission. Возвращает фактический статус. */
export type PushStatus = "unsupported" | "default" | "granted" | "denied";

export function getPushStatus(): PushStatus {
  if (typeof window === "undefined" || !("Notification" in window)) return "unsupported";
  return (Notification.permission as PushStatus) || "default";
}

export async function requestPushPermission(): Promise<PushStatus> {
  if (typeof window === "undefined" || !("Notification" in window)) return "unsupported";
  try {
    const result = await Notification.requestPermission();
    return (result as PushStatus) || "default";
  } catch {
    return "denied";
  }
}

/** Тестовое локальное уведомление (только при granted). */
export function sendTestNotification(title: string, body: string): boolean {
  if (typeof window === "undefined" || !("Notification" in window)) return false;
  if (Notification.permission !== "granted") return false;
  try {
    new Notification(title, { body, icon: "/favicon.ico" });
    return true;
  } catch {
    return false;
  }
}

/** В native-оболочке Face/Touch ID будет жить; в web — не показываем. */
export function isBiometricAvailable(): boolean {
  if (isNativeShell()) {
    // Capacitor / Flet — в нативной обёртке. Реальный native hook ещё не подключён,
    // но UI не должен обещать то, что web не умеет.
    return true;
  }
  // WebAuthn доступен в браузерах, но не равен Face/Touch ID и без телефона бесполезен.
  return false;
}
