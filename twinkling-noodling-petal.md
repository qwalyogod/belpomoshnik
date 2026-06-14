# План выполнения rework-промптов 1–10

## Контекст

У пользователя 10 detailed промптов (`rework project + promts/1..10`) с большими ТЗ:
1. Шифрование «Моих документов» + demo seed
2. ЖКХ и налоги (новый UX, заявки 115, demo seed)
3. Backend AI-помощника (RAG, history, провайдер, settings)
4. Frontend AI-помощника (ChatGPT-like UI, sidebar истории, actions)
5. Редакторский AI в админке (preview-before-apply, новые режимы)
6. Уведомления (in-app + Capacitor local + push token архитектура)
7. Админ-панель (полный контроль: проблемы, сценарии, пользователи, audit log)
8. Регионы и города (desktop split layout, drag&drop, fallback позиции)
9. Финальная стабилизация админки
10. **Control Center** — скрытая релизная панель с командой `belpomoshnikControl()` и паролем `x20b01`

Ограничение: окно лимитов ~5 часов. Все 10 не успеть **физически** — каждый промпт это 1–3 дня плотной работы. Цель плана: уложиться в окно с максимальным demo-эффектом для защиты диплома и минимальным риском поломать сайт.

## Принципы прайоритезации

1. **Demo-эффект для защиты**: что максимально удивит комиссию.
2. **Изоляция риска**: то что не ломает существующий UX — раньше.
3. **Зависимости**: AI frontend (4) требует AI backend (3); стабилизация (9) требует 7+8; broadcast в (6) требует Control Center (10).
4. **Security-аргументация**: шифрование (1) — единственный пункт, который реально защищает данные. Сильный аргумент на защите.
5. **Срезаемые "хвосты"**: тесты и docs последними внутри каждого блока — если упрёмся в лимит, скипаем тесты для P1/P2.

## Tier'ы

### P0 — обязательно (ядро для защиты)

| # | Блок | Время | Почему |
|---|------|-------|--------|
| 1 | **P0.1 Шифрование документов (промпт 1)** | ~60–90 мин | Изолировано, не ломает UI, security-аргумент. Crypto-сервис + миграция + переработка scan endpoints + demo seed. Тесты урезаем до минимума. |
| 2 | **P0.2 Control Center backend (промпт 10 backend)** | ~70–90 мин | Без backend часть промпта (broadcast в #6, maintenance в #10) не работает. Делаем: router + unlock + token + system_state + maintenance + broadcast + feature_flags + audit. |
| 3 | **P0.3 Control Center frontend (промпт 10 frontend)** | ~60–80 мин | `belpomoshnikControl()` + unlock screen + status + maintenance/banner/broadcast/feature_flags панели. **Главный wow-фактор демо.** |
| 4 | **P0.4 Backend AI (промпт 3) — урезанная версия** | ~50–70 мин | Без AI backend нельзя сделать новый чат. Минимум: фикс `parents[3]`, провайдер-класс, RAG v2 с корректными route, structured response, chat history (sessions+messages), action create-situation. AI settings и шифрование ключа — урезанная версия (один env-ключ, без user_ai_provider_credentials, если упрёмся). |

### P1 — если останется время

| # | Блок | Время | Почему |
|---|------|-------|--------|
| 5 | **P1.1 Frontend AI помощника citizen (промпт 4)** | ~80–100 мин | ChatGPT-like UI — второй wow-фактор. Сильно зависит от P0.4. Можно урезать sidebar истории на mobile. |
| 6 | **P1.2 Админ-панель: проблемы и сценарии в списке (промпт 7, часть)** | ~50–70 мин | Самый важный пункт промпта 7 — "проблемы и сценарии не видны в админке". Остальные разделы (audit log, bulk actions, roles management) — оставляем как есть. |
| 7 | **P1.3 Уведомления in-app слой (промпт 6, часть)** | ~30–40 мин | Только in-app notification center + dedupe_key + интеграция с broadcast из Control Center. Capacitor local и push token — TODO. |

### P2 — после refresh лимитов

| # | Блок | Время | Почему |
|---|------|-------|--------|
| 8 | **P2.1 Редакторский AI (промпт 5)** | ~50–70 мин | Расширенные режимы + preview-before-apply. Менее срочно, чем citizen AI. |
| 9 | **P2.2 ЖКХ и налоги (промпт 2)** | ~90–120 мин | Большой scope: новый UX, заявки 115, breakdown, demo seed. Безопасно отложить — раздел и сейчас работает. |
| 10 | **P2.3 Регионы UX (промпт 8)** | ~70–90 мин | Pure UX — desktop split + drag&drop. Большая работа, но не критична для демо: на mobile уже ок. |
| 11 | **P2.4 Финальная стабилизация (промпт 9)** | ~30–40 мин | Должна быть последней — это финальная проверка всего. |

## Стратегия «срезаем хвосты при риске лимита»

Если на середине P0 пойму, что не успеваю — срезаю в этом порядке:
1. Pytest-тесты в P0 (оставляю только smoke `python -m pytest -q`).
2. Полная документация в `docs/` — оставляю один абзац в CHANGELOG.
3. AI settings с шифрованием ключа — оставляю server-only Groq key.
4. Bulk actions/inspector drawer в админке — оставляю простой list view.
5. Drag&drop регионов (P2) — отрезаем целиком.

Что **не срезаю никогда**:
- Миграции БД — иначе бэк не стартует.
- RBAC-чеки на admin endpoints — security regression.
- Не ломать существующие endpoints (fallback на старые поля).
- `pnpm -C reactvitemaket run build` должен проходить после каждого блока.

## Tracking-файл

После approval создам в репо `rework project + promts/EXECUTION_PLAN.md` с чекбоксами — буду отмечать `[x]` по ходу, чтобы при следующем входе видеть прогресс.

## Критические файлы (наиболее затрагиваемые)

Backend:
- `src/backend/app.py` — регистрация Control Center router, system_state polling
- `src/backend/api/assistant.py` — большой рефактор, fix `parents[3]`
- `src/backend/api/control_center.py` — НОВЫЙ
- `src/backend/api/admin.py` — добавить problems/scenarios listing
- `src/backend/api/user.py` — переработка document scan upload/download
- `src/backend/models.py` — `ControlCenterSession`, `SystemSetting`, `AIChatSession`, `AIChatMessage`, поля шифрования у `UserDocument`
- `src/backend/migrations/00xx_document_encryption.sql` — НОВЫЙ
- `src/backend/migrations/00xx_ai_assistant.sql` — НОВЫЙ
- `src/backend/migrations/00xx_control_center.sql` — НОВЫЙ
- `src/backend/security/document_crypto.py` — НОВЫЙ
- `src/backend/ai/{provider,groq_provider,rag,prompts,history}.py` — НОВЫЕ
- `src/backend/scripts/seed_demo_personal_data.py` — НОВЫЙ

Frontend:
- `reactvitemaket/src/app/App.tsx` — регистрация `window.belpomoshnikControl`, MaintenanceScreen mount, SystemBanner
- `reactvitemaket/src/app/components/control-center/*.tsx` — НОВЫЕ
- `reactvitemaket/src/app/components/assistant/*.tsx` — НОВЫЕ (вынос из extra-screens)
- `reactvitemaket/src/app/data/store.tsx` — `systemState`, `controlCenter`, AI методы
- `reactvitemaket/src/app/services/api.ts` — методы Control Center, AI sessions, document scan blob

## Verification

После каждого P0-блока:
- `pnpm -C reactvitemaket run build` — должно проходить
- `PYTHONPATH=src .venv/bin/python -m pytest -q` — должно проходить smoke
- Запустить бэк (`uvicorn backend.app:app --port 8060`) и проверить `/api/health`

После P0.3 (Control Center frontend):
- Открыть Vite dev (`pnpm dev`), в браузере консоль → `belpomoshnikControl()` → пароль `x20b01` → должна открыться панель.

После P1.1 (AI чат):
- Citizen логин → открыть чат → "Я потерял паспорт" → должны прийти ссылки на сценарий + action.

## Что НЕ делаю в этой сессии (явно вынесено в TODO)

- Capacitor `@capacitor/local-notifications` и `@capacitor/push-notifications` (промпт 6 уровень 2/3) — требует пересборки APK/IPA, выходит за рамки окна.
- FCM/APNs credentials — пользователь сам должен подключить позже.
- Drag&drop регионов (промпт 8, часть 5) — большая ручная работа без demo-выгоды.
- Полный audit log с before/after diff (промпт 7, часть 11) — слишком долго; оставлю минимум.
- E2E playwright тесты — не успеть.

## Решения пользователя (финал)

1. **Приоритеты:** P0 = security + Control Center + AI backend → P1 = AI frontend + админка + in-app уведомления → P2 = после refresh.
2. **Тесты/docs:** срезаю агрессивно. Smoke `pytest -q` + одна строка в CHANGELOG. Большие тестовые suite из промптов — TODO.
3. **Коммиты:** 3 крупных коммита — после P0 целиком, после P1 целиком, после P2 целиком. Внутри блока не коммичу.

## Execution flow (что буду делать)

После выхода из plan mode:
1. Создаю `rework project + promts/EXECUTION_PLAN.md` с чекбоксами по всем подпунктам P0/P1/P2.
2. **P0.1 Шифрование документов** → файлы: `src/backend/security/document_crypto.py`, `migrations/00xx_document_encryption.sql`, `models.py` (поля _encrypted), `api/user.py` (scan endpoints + secure storage path), `scripts/seed_demo_personal_data.py` (демо PDF). Frontend: `types.ts`, `adapters.ts`, `services/api.ts` (uploadDocumentScan/downloadDocumentScan), `store.tsx`, `DocumentCardModal` в `extra-screens.tsx`.
3. **P0.2 Control Center backend** → `api/control_center.py` (НОВЫЙ), `models.py` (`ControlCenterSession`, `SystemSetting`), `migrations/00xx_control_center.sql`, `app.py` (регистрация router), `api/public.py` (или новый `/api/public/system-state`), helpers `ensure_not_readonly_mode()`.
4. **P0.3 Control Center frontend** → `components/control-center/*.tsx` (ControlCenter, UnlockScreen, StatusPanel, MaintenancePanel, BroadcastPanel, BannerPanel, FeatureFlagsPanel, BrandingPanel, NavigationPanel, AuditLogPanel), `App.tsx` (window.belpomoshnikControl + MaintenanceScreen mount + SystemBanner mount), `services/api.ts` (control методы), `store.tsx` (systemState polling).
5. **P0.4 Backend AI** → fix `parents[3]` в `assistant.py`, новые `ai/{provider,groq_provider,rag,prompts,history}.py`, модели `AIChatSession`/`AIChatMessage`, миграция `00xx_ai_assistant.sql`, endpoints sessions+messages+action create-situation. AI settings шифрование ключа — режу до server-only `GROQ_API_KEY`.
6. **Коммит P0.**
7. **P1.1 AI frontend** → `components/assistant/*.tsx` (AssistantPanel, Sidebar, MessageList, Composer, LinkCard, ActionCard, SettingsModal, EmptyState), интеграция в `App.tsx` (замена openAssistant), `services/api.ts` + `store.tsx`.
8. **P1.2 Админка проблемы/сценарии** → добавить tab/раздел в существующий `admin-window.tsx` или создать `AdminProblems.tsx`/`AdminScenarios.tsx`. Backend: добавить `GET /api/admin/problems` и `/api/admin/scenarios` со всеми статусами.
9. **P1.3 In-app уведомления** → проверить `UserNotification` модель, добавить `dedupe_key` если нет, интегрировать с broadcast endpoint из P0.2. Capacitor local + push — TODO в комментарии.
10. **Коммит P1.**
11. **P2** — после refresh лимитов: редакторский AI, ЖКХ/налоги, регионы, стабилизация.

## Definition of Done для каждого блока

- `pnpm -C reactvitemaket run build` зелёный
- `PYTHONPATH=src .venv/bin/python -m pytest -q` зелёный (smoke)
- Бэк стартует, `GET /api/health` отвечает 200
- Чекбокс отмечен в `EXECUTION_PLAN.md`
