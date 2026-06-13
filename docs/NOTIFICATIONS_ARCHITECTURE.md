# Архитектура уведомлений

Обновлено: 2026-06-13.

## Принцип работы

Любое событие сначала записывается в таблицу `user_notifications` и доступно на странице `/notifications`. Этот канал работает независимо от разрешений ОС и браузера. Поле `dedupe_key` не позволяет правилам сроков создавать одну запись повторно.

Системная доставка является дополнительной:

- desktop web использует стандартный браузерный `Notification API` только после нажатия пользователя;
- Capacitor-приложение использует `@capacitor/local-notifications` для известных заранее сроков;
- внезапные серверные события подготовлены к доставке через `@capacitor/push-notifications`, FCM и APNs;
- если разрешение не выдано, никаких всплывающих уведомлений нет, но in-app запись сохраняется.

## Backend

- `notifications/service.py` — создание in-app записи и безопасный payload;
- `notifications/rules.py` — документы, задачи, ЖКХ и налоги;
- `notifications/delivery.py` — проверка предпочтений и выбор внешнего канала;
- `notifications/native_push.py` — production-граница FCM/APNs;
- `scheduler.py` — периодический запуск правил.

Push payload не содержит номер документа, адрес, скан или иные персональные подробности. Device token хранится зашифрованно, наружу возвращается только маска.

## Frontend

- `nativeNotifications.ts` — локальное расписание Capacitor;
- `nativePush.ts` — разрешение, регистрация и деактивация device token;
- `webNotifications.ts` — браузерные уведомления desktop;
- `/notifications` — внутренний центр, состояния каналов, настройки типов и тестовая отправка.

Разрешения не запрашиваются при запуске. Если пользователь уже выдал их ранее, приложение восстанавливает расписание после входа.

## Production-настройка

Android требует Firebase Cloud Messaging и `google-services.json`. iOS требует Apple Developer Account, Push Notifications capability и APNs key/certificate. Пока credentials не настроены, backend честно возвращает `native_push_ready=false` и `reason=credentials_not_configured`.

WebView сам по себе не гарантирует доставку при закрытом приложении. Поэтому сроки планируются нативно, а серверные события в production должны идти через FCM/APNs.
