import { Capacitor } from "@capacitor/core";
import { LocalNotifications } from "@capacitor/local-notifications";
import type { AppNotification } from "../data/types";

const SCHEDULE_KEY = "belpomoshnik.nativeNotificationIds";

export function isNativeApp(): boolean {
  return Capacitor.isNativePlatform();
}

export async function checkNativeNotificationPermission(): Promise<PermissionState | "unavailable"> {
  if (!isNativeApp()) return "unavailable";
  const status = await LocalNotifications.checkPermissions();
  return status.display;
}

export async function requestNativeNotificationPermission(): Promise<PermissionState | "unavailable"> {
  if (!isNativeApp()) return "unavailable";
  const status = await LocalNotifications.requestPermissions();
  return status.display;
}

function stableNotificationId(value: string): number {
  let hash = 0;
  for (let i = 0; i < value.length; i += 1) hash = ((hash << 5) - hash + value.charCodeAt(i)) | 0;
  return Math.max(1, Math.abs(hash));
}

function reminderDate(value: string): Date | null {
  if (!value) return null;
  const date = new Date(value.length <= 10 ? `${value}T09:00:00` : value);
  if (Number.isNaN(date.getTime()) || date.getTime() <= Date.now()) return null;
  return date;
}

export async function scheduleLocalNotification(reminder: AppNotification): Promise<number | null> {
  if (!isNativeApp()) return null;
  if (await checkNativeNotificationPermission() !== "granted") return null;
  const at = reminderDate(reminder.createdAt);
  if (!at) return null;
  const id = stableNotificationId(reminder.id);
  await LocalNotifications.schedule({
    notifications: [{
      id,
      title: reminder.title,
      body: reminder.body || "Откройте Белпомощник, чтобы посмотреть подробности.",
      schedule: { at, allowWhileIdle: true },
      extra: { reminderId: reminder.id, route: reminder.link?.page ? `/${reminder.link.page}` : "/notifications" },
    }],
  });
  return id;
}

export async function cancelLocalNotification(id: number): Promise<void> {
  if (!isNativeApp()) return;
  await LocalNotifications.cancel({ notifications: [{ id }] });
}

export async function scheduleUpcomingLocalNotifications(reminders: AppNotification[]): Promise<number[]> {
  const ids: number[] = [];
  for (const reminder of reminders) {
    const id = await scheduleLocalNotification(reminder);
    if (id !== null) ids.push(id);
  }
  return ids;
}

function readScheduledIds(): number[] {
  try {
    const raw = localStorage.getItem(SCHEDULE_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed.filter(Number.isInteger) : [];
  } catch {
    return [];
  }
}

export async function syncNativeNotificationSchedule(reminders: AppNotification[]): Promise<number[]> {
  if (!isNativeApp() || await checkNativeNotificationPermission() !== "granted") return [];
  const previous = readScheduledIds();
  if (previous.length > 0) {
    await LocalNotifications.cancel({ notifications: previous.map(id => ({ id })) });
  }
  const ids = await scheduleUpcomingLocalNotifications(reminders);
  localStorage.setItem(SCHEDULE_KEY, JSON.stringify(ids));
  return ids;
}

export async function clearNativeNotificationSchedule(): Promise<void> {
  if (!isNativeApp()) return;
  const previous = readScheduledIds();
  if (previous.length > 0) {
    await LocalNotifications.cancel({ notifications: previous.map(id => ({ id })) });
  }
  localStorage.removeItem(SCHEDULE_KEY);
}
