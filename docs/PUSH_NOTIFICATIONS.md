# PUSH_NOTIFICATIONS.md — Push-уведомления (Перспектива, I6)

> Этот документ описывает архитектурный план реализации push-уведомлений.
> В текущем MVP (Этап I) реализована только email-рассылка. Push — следующий шаг.

---

## Текущее состояние (MVP)

| Канал | Статус | Файл |
|-------|--------|------|
| In-app уведомления | ✅ Готово | `src/pages/notifications_page.py` |
| Email (SMTP) | ✅ Готово | `src/backend/email_service.py` |
| Push (FCM/APNs) | 📋 Перспектива | — |

---

## Архитектура push (перспектива)

### Шаг 1. Push-подписки

При запуске приложения клиент регистрирует устройство:

```
POST /api/user/push-subscriptions
{
  "platform": "android" | "ios" | "web",
  "token": "<FCM token / APNs device token / Web Push subscription>",
  "device_id": "unique-device-uuid"
}
```

Хранится в таблице `push_subscriptions`:

```sql
CREATE TABLE push_subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    platform TEXT NOT NULL,              -- android / ios / web
    token TEXT NOT NULL UNIQUE,
    device_id TEXT NOT NULL DEFAULT '',
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

### Шаг 2. Отправка push

Сервис `PushService` (аналог `EmailService`):

```python
from firebase_admin import messaging

def send_push(token: str, title: str, body: str, data: dict | None = None):
    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        data=data or {},
        token=token,
    )
    messaging.send(message)
```

Зависимости: `pip install firebase-admin` (Android/web FCM) или `apns2` (iOS).

### Шаг 3. Триггеры

Push отправляется в тех же случаях, что и email:

| Событие | Тип | Канал |
|---------|-----|-------|
| Истекает документ (7/30 дней) | `doc_expiry` | email + push |
| Новый опубликованный закон-апдейт | `law_important` | push |
| Срок задачи ситуации | `task_due` | push |
| ЖКХ: срок показаний/оплаты | `utility` | push |

### Шаг 4. Очередь

Переиспользовать механизм `enqueue_email()` — добавить аналог `enqueue_push()` в `email_service.py` или вынести в общий `notification_service.py`:

```python
def enqueue_push(db, user_id, title, body, data=None, notification_type="general"):
    # Аналог enqueue_email, но записывает в push_queue
    ...
```

### Шаг 5. Flet + push

Flet 0.85 имеет ограниченную нативную поддержку push. Рекомендуемый путь:

- **Mobile**: использовать `flet_contrib.push_notification` (experimental) или встроить native module.
- **Web (PWA)**: Web Push API через Service Worker.
- **Desktop**: системные уведомления через `plyer` / `playsound`.

На Flet 1.x+ будет нативная поддержка.

---

## Ограничения MVP

- FCM/APNs требуют Google Service Account / Apple Developer аккаунт — не входит в дипломный MVP.
- В MVP push заменены in-app уведомлениями (notifications_state) и demo email.
- Когда понадобится: добавить `push_subscriptions` таблицу, `PushService`, и вызов в `sync_task_notifications()`.

---

## Что делать следующим (после дипломной защиты)

1. Зарегистрировать приложение в Firebase → скачать `google-services.json`.
2. Создать таблицу `push_subscriptions`.
3. Реализовать `POST /api/user/push-subscriptions`.
4. Реализовать `PushService.send()`.
5. Добавить trigerr в scheduler рядом с `send_pending_emails()`.
6. Добавить настройку в профиле «Получать push-уведомления».
