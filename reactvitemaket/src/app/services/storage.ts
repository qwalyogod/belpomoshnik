/**
 * Утилиты для очистки кэша публичного контента.
 *
 * Если backend упал или вернул пустые массивы по ВСЕМ public-эндпойнтам,
 * пользователь видит «пустые» страницы (например, /law-detail показывает
 * «Новость не найдена»). Чтобы при следующем mount-е поднялись mock-данные
 * или свежий API-ответ, чистим ключи belp.legal / belp.authorities /
 * belp.categories / belp.userData.*.
 *
 * Auth-токены (belp.quickAccounts, belp.currentUserId, belp.authTokens) НЕ
 * трогаем — пользователь остаётся залогинен.
 */

const PUBLIC_KEYS = [
  "belp.legal",
  "belp.authorities",
  "belp.categories",
];

const USER_DATA_PREFIX = "belp.userData.";

export function clearPublicContentCache(): void {
  if (typeof window === "undefined") return;
  try {
    for (const key of PUBLIC_KEYS) {
      window.localStorage.removeItem(key);
    }
    // Удаляем все ключи, начинающиеся с belp.userData.
    const toRemove: string[] = [];
    for (let i = 0; i < window.localStorage.length; i += 1) {
      const key = window.localStorage.key(i);
      if (key && key.startsWith(USER_DATA_PREFIX)) toRemove.push(key);
    }
    for (const key of toRemove) {
      window.localStorage.removeItem(key);
    }
  } catch {
    /* localStorage может быть недоступен в приватном режиме — это не критично. */
  }
}
