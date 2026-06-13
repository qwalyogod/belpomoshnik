# API_CONTRACTS.md — Контракты API «Белпомощник»

Обновлено: 2026-06-13.

---

## Базовые параметры

| Параметр | Значение |
|---|---|
| Base URL | `http://127.0.0.1:8060` |
| Prefix | `/api` |
| Формат | JSON |
| Аутентификация | JWT Bearer для пользовательских и административных действий |
| Документация | `http://127.0.0.1:8060/docs` (Swagger UI) |

---

## Публичные эндпоинты (no auth required)

### Проблемы

| Метод | Путь | Описание |
|---|---|---|
| GET | `/api/problems` | Список опубликованных проблем |
| GET | `/api/problems/{slug}` | Проблема + связанные сценарии |

### Сценарии

| Метод | Путь | Описание |
|---|---|---|
| GET | `/api/scenarios/{slug}` | Полный сценарий с этапами, шагами, документами |
| GET | `/api/scenarios/{slug}/steps` | Только шаги сценария |

### Контент

| Метод | Путь | Описание |
|---|---|---|
| GET | `/api/documents` | Справочник документов |
| GET | `/api/authorities` | Справочник учреждений |
| GET | `/api/law-updates` | Опубликованные закон-апдейты (статус APPLIED) |
| GET | `/api/law-updates/{id}` | Один закон-апдейт |

### Системные

| Метод | Путь | Описание |
|---|---|---|
| GET | `/api/health` | `{"status": "ok"}` |
| GET | `/api/public/system-state` | Публичное состояние платформы: баннер, обслуживание, feature flags, branding |
| GET | `/api/admin/bootstrap/problems` | Временный: список проблем для Flet-админки |

### Control Center (скрытый системный слой)

> Не является обычной админ-панелью и не привязан к пользовательским ролям. Окно открывается во frontend только командой `belpomoshnikControl()`, но пароль проверяется backend’ом.

| Метод | Путь | Защита | Описание |
|---|---|---|---|
| POST | `/api/control-center/unlock` | Пароль backend | Выдаёт временный `control_token` |
| POST | `/api/control-center/lock` | `X-Control-Center-Token` | Отзывает текущую control-сессию |
| GET | `/api/control-center/status` | `X-Control-Center-Token` | Live status платформы |
| PUT | `/api/control-center/maintenance` | `X-Control-Center-Token` | Обслуживание |
| PUT | `/api/control-center/readonly` | `X-Control-Center-Token` | Режим только чтения |
| PUT | `/api/control-center/banner` | `X-Control-Center-Token` | Системный баннер |
| PUT | `/api/control-center/feature-flags` | `X-Control-Center-Token` | Feature flags разделов |
| PUT | `/api/control-center/branding` | `X-Control-Center-Token` | Брендинг |
| PUT | `/api/control-center/navigation-layout` | `X-Control-Center-Token` | Сохранение порядка меню |
| POST | `/api/control-center/broadcast-notification` | `X-Control-Center-Token` | Системная in-app рассылка |
| POST | `/api/control-center/service-actions/{action}` | `X-Control-Center-Token` | Сервисные сценарии |
| GET | `/api/control-center/audit-log` | `X-Control-Center-Token` | Журнал действий Control Center |

---

## Административные эндпоинты (prefix `/api/admin`)

> Требуется JWT. Базовые контентные действия доступны `content_editor` и выше. Управление пользователями, ролями, блокировками, сессиями и системными уведомлениями доступно только `platform_admin`.

### Обзор

| Метод | Путь | Описание |
|---|---|---|
| GET | `/api/admin/dashboard/stats` | Реальная сводка админ-панели |

### Проблемы

| Метод | Путь |
|---|---|
| GET | `/api/admin/problems` |
| POST | `/api/admin/problems` |
| PUT | `/api/admin/problems/{id}` |
| DELETE | `/api/admin/problems/{id}` |

### Сценарии

| Метод | Путь |
|---|---|
| GET/POST | `/api/admin/scenarios` |
| GET/PUT/DELETE | `/api/admin/scenarios/{id}` |
| GET | `/api/admin/scenarios/{id}/integrity` |
| GET/POST | `/api/admin/scenarios/{id}/stages` |
| GET/POST | `/api/admin/stages/{id}/steps` |
| PUT/DELETE | `/api/admin/stages/{id}`, `/api/admin/steps/{id}` |

### Зависимости и связи

| Метод | Путь |
|---|---|
| POST/DELETE | `/api/admin/dependencies` / `/{id}` |
| POST/DELETE | `/api/admin/related-scenarios` / `/{id}` |

### Пользователи и роли (`platform_admin`)

| Метод | Путь | Описание |
|---|---|---|
| GET | `/api/admin/roles` | Справочник ролей |
| GET | `/api/admin/users` | Список пользователей с фильтрами `search`, `role`, `active`, `limit`, `offset` |
| GET | `/api/admin/users/{id}` | Карточка пользователя с счётчиками связанных сущностей |
| PATCH | `/api/admin/users/{id}/role` | Изменить роль |
| PATCH | `/api/admin/users/{id}/active` | Заблокировать/разблокировать |
| POST | `/api/admin/users/{id}/sessions/revoke` | Отозвать refresh-сессии пользователя |
| POST | `/api/admin/users/{id}/notifications` | Создать системное in-app уведомление |
| DELETE | `/api/admin/users/{id}` | Soft-delete: деактивация и отзыв сессий |

### Аудит

| Метод | Путь | Описание |
|---|---|---|
| GET | `/api/admin/audit-logs` | Журнал действий; фильтры `actor`, `entity_type`, `event_type`, `status`, `limit` |

### Регионы и города

На 2026-06-14 географический справочник админки хранится во frontend/store (`localStorage: belp.geo`) и использует расширенную модель `GeoRegion` с координатами карточек на карте. Backend API `/api/admin/regions/*` запланирован следующим инфраструктурным шагом, чтобы перенести этот справочник из локального состояния в БД.
| POST/DELETE | `/api/admin/source-references` / `/{id}` |

### Контент

| Метод | Путь |
|---|---|
| GET/POST/PUT/DELETE | `/api/admin/documents/{id}` |
| GET/POST/PUT/DELETE | `/api/admin/authorities/{id}` |
| GET/POST | `/api/admin/deadlines` |
| GET/POST/PUT | `/api/admin/law-updates` / `/{id}` |

---

## Плановые эндпоинты (Этап H — после внедрения JWT)

### Авторизация

| Метод | Путь | Описание |
|---|---|---|
| POST | `/api/auth/register` | Регистрация пользователя |
| POST | `/api/auth/login` | Получение JWT-токена |
| POST | `/api/auth/refresh` | Обновление токена |
| POST | `/api/auth/logout` | Инвалидация токена |

### Профиль пользователя (G3)

| Метод | Путь | Описание |
|---|---|---|
| GET | `/api/user/profile` | Профиль текущего пользователя |
| PUT | `/api/user/profile` | Обновление профиля |
| PATCH | `/api/user/settings` | Обновление настроек |

### Личные ситуации и задачи (G5)

| Метод | Путь | Описание |
|---|---|---|
| GET | `/api/user/situations` | Список ситуаций пользователя |
| POST | `/api/user/situations` | Создать ситуацию из шаблона |
| GET/PUT/DELETE | `/api/user/situations/{id}` | CRUD ситуации |
| GET | `/api/user/situations/{id}/tasks` | Задачи ситуации |
| PATCH | `/api/user/tasks/{id}/complete` | Отметить задачу выполненной |

### Личные документы (G6)

| Метод | Путь | Описание |
|---|---|---|
| GET | `/api/user/documents` | Список личных документов |
| POST | `/api/user/documents` | Добавить документ |
| GET/PUT/DELETE | `/api/user/documents/{id}` | CRUD документа |

### Уведомления (G7)

| Метод | Путь | Описание |
|---|---|---|
| GET | `/api/user/notifications` | Список уведомлений |
| PATCH | `/api/user/notifications/{id}/read` | Отметить прочитанным |
| POST | `/api/user/notifications/read-all` | Прочитать все |
| DELETE | `/api/user/notifications/{id}` | Удалить своё уведомление |
| POST | `/api/user/push/native-token` | Зарегистрировать зашифрованный iOS/Android token |
| DELETE | `/api/user/push/native-token` | Деактивировать token текущего пользователя |
| GET | `/api/user/push/status` | Разрешения, readiness и маски зарегистрированных устройств |
| POST | `/api/user/push/test` | Создать in-app тест и попытаться доставить системно |

### Трекеры (ЖКХ + налоги)

| Метод | Путь | Описание |
|---|---|---|
| GET/POST | `/api/user/utility-accounts` | Лицевые счета ЖКХ |
| GET/POST | `/api/user/utility-payments` | Платежи ЖКХ |
| GET/POST | `/api/user/tax-obligations` | Налоговые обязательства |

### Аудит (F7)

| Метод | Путь | Описание |
|---|---|---|
| GET | `/api/admin/audit-logs` | Журнал действий редактора |

---

## Стратегия интеграции (G8 — offline/cache)

```
Flet-клиент:
  1. Пытается GET /api/health — если OK:
       → загружает данные из backend
       → сохраняет в app_state.json (cache)
  2. Если backend недоступен:
       → читает из app_state.json (последний актуальный кэш)
       → показывает баннер "Оффлайн-режим"
  3. Личные данные (ситуации, документы):
       → до Этапа H хранятся только локально
       → после H: синхронизация при каждом save_current_state()
```

---

## Схемы (краткие)

### LawUpdateOut
```json
{
  "id": 1,
  "title": "Изменения в ...",
  "description": "...",
  "source_url": "https://...",
  "affected_scenario_id": null,
  "update_date": "2026-07-01T00:00:00Z",
  "status": "applied"
}
```

### ProblemPublicOut
```json
{
  "id": 1,
  "title": "Потерял паспорт",
  "slug": "lost-passport",
  "short_description": "...",
  "description": "...",
  "icon": "BADGE_OUTLINED",
  "category": "docs",
  "status": "published"
}
```

### AuditLogOut (F7, production)
```json
{
  "id": 1,
  "actor": "editor@example.by",
  "role_id": "content_editor",
  "event_type": "create",
  "action": "Создан сценарий «...»",
  "status": "ok",
  "created_at": "2026-05-24T12:00:00Z"
}
```
