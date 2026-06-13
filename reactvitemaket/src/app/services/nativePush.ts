import { Capacitor } from "@capacitor/core";
import { PushNotifications } from "@capacitor/push-notifications";
import { apiClient } from "./api";

const TOKEN_KEY = "belpomoshnik.nativePushToken";

export function isNativeApp(): boolean {
  return Capacitor.isNativePlatform();
}

export async function checkPushPermission(): Promise<PermissionState | "unavailable"> {
  if (!isNativeApp()) return "unavailable";
  return (await PushNotifications.checkPermissions()).receive;
}

export async function requestPushPermission(): Promise<PermissionState | "unavailable"> {
  if (!isNativeApp()) return "unavailable";
  return (await PushNotifications.requestPermissions()).receive;
}

export async function sendPushTokenToBackend(token: string, platform: "ios" | "android", accessToken: string) {
  return apiClient.registerNativePushToken(accessToken, {
    token,
    platform,
    device_label: `${Capacitor.getPlatform()} device`,
  });
}

export async function registerNativePush(accessToken: string): Promise<string | null> {
  if (!isNativeApp() || await checkPushPermission() !== "granted") return null;
  return new Promise<string | null>(async resolve => {
    let settled = false;
    const finish = (value: string | null) => {
      if (settled) return;
      settled = true;
      resolve(value);
    };
    const registration = await PushNotifications.addListener("registration", async token => {
      localStorage.setItem(TOKEN_KEY, token.value);
      await sendPushTokenToBackend(token.value, Capacitor.getPlatform() === "ios" ? "ios" : "android", accessToken);
      finish(token.value);
    });
    const registrationError = await PushNotifications.addListener("registrationError", () => finish(null));
    window.setTimeout(() => finish(null), 12_000);
    try {
      await PushNotifications.register();
    } catch {
      finish(null);
    } finally {
      window.setTimeout(() => {
        void registration.remove();
        void registrationError.remove();
      }, 12_500);
    }
  });
}

export async function unregisterNativePushToken(accessToken: string): Promise<void> {
  if (!isNativeApp()) return;
  const token = localStorage.getItem(TOKEN_KEY);
  await apiClient.unregisterNativePushToken(accessToken, token || undefined);
  localStorage.removeItem(TOKEN_KEY);
}
