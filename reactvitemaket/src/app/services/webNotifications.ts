import { Capacitor } from "@capacitor/core";

export function isDesktopBrowserNotificationAvailable(): boolean {
  if (Capacitor.isNativePlatform() || typeof window === "undefined") return false;
  const mobile = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
  return !mobile && "Notification" in window;
}

export function checkWebNotificationPermission(): NotificationPermission | "unavailable" {
  if (!isDesktopBrowserNotificationAvailable()) return "unavailable";
  return Notification.permission;
}

export async function requestWebNotificationPermission(): Promise<NotificationPermission | "unavailable"> {
  if (!isDesktopBrowserNotificationAvailable()) return "unavailable";
  return Notification.requestPermission();
}

export function showWebNotification(title: string, body: string, route = "/notifications"): boolean {
  if (!isDesktopBrowserNotificationAvailable() || Notification.permission !== "granted") return false;
  const notification = new Notification(title, { body, icon: "/favicon.svg", tag: `belpomoshnik-${Date.now()}` });
  notification.onclick = () => {
    window.focus();
    window.location.assign(route);
    notification.close();
  };
  return true;
}
