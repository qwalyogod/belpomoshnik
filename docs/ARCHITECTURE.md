# Архитектура «Белпомощник»

Версия: 2026-06-11 (финализация MVP).

## Состав

```text
belpomoshnik/
├── src/
│   ├── backend/                 # FastAPI + SQLAlchemy + Pydantic
│   │   ├── app.py               # create_app(), CORS, lifespan, static mounts
│   │   ├── auth.py              # JWT (HS256), bcrypt, fail-fast SECRET_KEY
│   │   ├── config.py            # env-driven (BELPOMOSHNIK_*)
│   │   ├── database.py          # engine, SessionLocal, get_db
│   │   ├── models.py            # 20+ ORM-моделей
│   │   ├── schemas.py           # Pydantic v2 DTO
│   │   ├── enums.py
│   │   ├── service.py           # бизнес-логика
│   │   ├── rate_limit.py        # in-memory limiter
│   │   ├── scheduler.py         # email-sender 60s + token-cleanup 1h
│   │   ├── email_service.py     # SMTP-очередь
│   │   ├── bootstrap.py         # create_all + роли + тест-аккаунты
│   │   ├── api/                 # 8 роутеров (см. ниже)
│   │   ├── migrations/          # 0001..0018 (0007 — noop)
│   │   ├── seeds/               # mvp_childbirth.py, full_content.py
│   │   └── scripts/             # init_db, migrate, seed_db
│   └── mobile_webview.py        # Flet 0.85: только WebView-обёртка (нет своего UI)
│
├── reactvitemaket/
│   ├── src/app/
│   │   ├── App.tsx              # RootLayout, MobileShell, DesktopShell, ShellContext
│   │   ├── routes.tsx           # createBrowserRouter, ~20 routes
│   │   ├── pages.tsx            # 18+ страниц (re-export)
│   │   ├── components/
│   │   │   ├── belp-ui.tsx      # Pill/Card/PrimaryButton/GhostButton/Logo/DataModeBadge
│   │   │   ├── extra-screens.tsx # ScenarioDetail, MySituationDetail, GuestGuard…
│   │   │   ├── admin-window.tsx, content-editor.tsx, law-editor.tsx,
│   │   │   │   authorities-editor.tsx, regions-editor.tsx, desktop.tsx
│   │   │   ├── ConnectionBanner.tsx, GuestGuardBridge.tsx
│   │   │   └── ui/              # shadcn-набор (47 файлов)
│   │   ├── data/
│   │   │   ├── store.tsx        # глобальный стор (React Context)
│   │   │   ├── adapters.ts      # API ↔ store mapping
│   │   │   ├── mock.ts          # fallback-данные
│   │   │   ├── types.ts         # типы
│   │   │   ├── geo.ts, geo-regions.json
│   │   ├── services/
│   │   │   ├── api.ts           # fetch-клиент + JWT refresh (JSON)
│   │   │   ├── connection.ts    # heartbeat
│   │   │   ├── a11y.ts          # крупный шрифт, контраст, push
│   │   │   ├── institutions.ts, reminders.ts, search.ts, storage.ts
│   ├── android/, ios/           # Capacitor 8 (APK/IPA)
│   ├── package.json
│   └── pnpm-lock.yaml
│
├── docs/                        # 39+ markdown
├── tests/                       # 7 файлов, 82 теста
├── scripts/
│   ├── check.sh                 # единая точка проверки MVP
│   ├── smoke_backend.py         # end-to-end smoke через TestClient
│   ├── smoke_demo.sh            # 5-минутный защитный сценарий (curl)
│   ├── backup.sh
│   ├── validate_content_batch.py, normalize_content_batch.py, import_content_batches.py
│   └── build_diploma_docx.py
├── data/                        # runtime: belpomoshnik.db, uploads/, exports/
├── .env.example                 # шаблон env
├── pytest.ini
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Backend (`src/backend/`)

### Стек
- **FastAPI 0.116** — REST + авто-доки OpenAPI.
- **SQLAlchemy 2.0** — ORM, новый стиль (`mapped_column`).
- **Pydantic 2.11** — DTO v2.
- **bcrypt 4+** (без passlib, намеренно — passlib 1.7.4 не поддерживает bcrypt 5.x).
- **python-jose** — JWT (HS256, access=30 мин / refresh=7 дней, rotation).
- **SQLite (dev)** / **PostgreSQL (prod-ready)** — общий код под оба диалекта.

### Auth & RBAC
- `auth.py:23` — `SECRET_KEY` fail-fast: `RuntimeError` если env не задан или < 32 символов.
- `auth.py:87-101` — `require_role("citizen"|"content_editor"|"platform_admin")`, иерархия: 0 < 1 < 2.
- Login — `OAuth2PasswordRequestForm` (form-data). Refresh/logout — `RefreshRequest` (JSON).
- `/api/auth/test-accounts` — выключен по дефолту, включается `BELPOMOSHNIK_ENABLE_TEST_SWITCHER=true`.

### Роутеры (`src/backend/api/`)
- `public.py` (9) — `/api/problems`, `/api/scenarios`, `/api/documents`, `/api/authorities`, `/api/law-updates`, `/api/extremist-entries`. Защита: только `bootstrap/problems` через `require_role("content_editor")`.
- `auth.py` (8) — register/login/refresh/logout/me/test-accounts/verify.
- `user.py` (16) — profile, avatar, settings (allow-list!), documents (CRUD + scan upload/download), notes, + `GET /api/user/documents/{id}/scan` (защищённый owner-check).
- `situations.py` (~13, prefix `/api/user`) — ситуации, задачи, уведомления.
- `trackers.py` (10, prefix `/api/user`) — utility-accounts, payments, taxes.
- `articles.py` (9) — публикации, UGC-модерация. `body_html` санитизируется.
- `admin.py` (~50, prefix `/api/admin`) — full CRUD для контента, пользователей, audit-log, email-log.
- `assistant.py` (1) — GROQ AI + canned-fallback.
- `extremist.py` (3, prefix `/api`) — публичный read-only.

### Схема БД (`models.py`, 20+ таблиц)
- **Контент:** `Problem`, `Scenario`, `ScenarioStage`, `ScenarioStep`, `Authority`, `Deadline`, `Document`, `NotificationRule`, `ScenarioDependency`, `RelatedScenario`, `SourceReference`, `LawUpdate`.
- **Auth/users:** `Role`, `User`, `RefreshToken` (хэш токена, TODO SHA-256 для production), `UserNote`, `UserDocument`, `UserSituation`, `UserSituationTask`, `UserNotification`, `UtilityAccount`, `UtilityPayment`, `TaxObligation`.
- **UGC/журналы:** `Article`, `BlockedSubmitter`, `ArticleViewDaily`, `ExtremistEntry`, `EmailNotification`, `AuditLog`.

### Scheduler (`scheduler.py`)
- `start_background_tasks()` запускается в FastAPI lifespan.
- `_email_sender_loop` (60 с) — отправка pending email.
- `_token_cleanup_loop` (3600 с) — удаление expired/revoked refresh-токенов.

## Frontend (`reactvitemaket/src/app/`)

### Стек
- **React 18.3** + **Vite 6.3** + **TypeScript 5.x**.
- **Tailwind 4** + shadcn-style components (47 файлов в `components/ui/`).
- **motion 12.23** (Framer Motion successor) — анимации.
- **react-router 7** — `createBrowserRouter`.
- **lucide-react 0.487** — иконки.
- **Capacitor 8** — Android/iOS-сборка.
- **Без axios** (используется `fetch` + обёртка в `services/api.ts`).
- **Без Zustand/Redux** — собственный `AppStoreProvider` поверх `useState` + `useCallback`.

### Архитектура стора
- `data/store.tsx` — единственный `Store` через `React.createContext`.
- Метод `reconcileApiFirst(mock, api)` — backend имеет приоритет, mock как fallback.
- `publicContentStatus: "loading" | "api" | "fallback"` — отображается через `<DataModeBadge>`.

### Маршрутизация
- `routes.tsx` — `createBrowserRouter` с ~20 маршрутами.
- `ResponsivePage` свапает mobile/desktop по `isMobile` из `ShellContext`.
- `AdminPageWrapper` / `EditorPageWrapper` — гейт по роли.
- `Outlet context` — `{ protectedGuard, onAddDoc, openScenario, openMySituation }`.

### Auth flow
- `api.ts:131-159` — refresh через JSON (`Content-Type: application/json`).
- `api.ts:656-672` — logout через JSON.
- `authSession` хранится в `belpomoshnik.authTokens` localStorage.
- **Пароли НЕ хранятся** в localStorage (`stripSensitiveFields`).

### A11y
- `services/a11y.ts` — крупный шрифт, высокий контраст, Notification API.
- `SettingsPage` (`extra-screens.tsx`) — переключатели + push permission.

### Mobile / native
- `src/mobile_webview.py` (567 строк) — Flet 0.85 WebView, грузит URL из `BELPOMOSHNIK_APP_URL`/`REACT_APP_URL`. PostMessage из React переключает обёртку.
- `reactvitemaket/ServerPicker.tsx` — экран ввода dev-адресов фронта/бэка.
- `reactvitemaket/android/`, `ios/` — Capacitor 8.
- CI: `.github/workflows/build-apk.yml` (ubuntu, Node 22, JDK 21), `build-ipa.yml` (macos, xcodebuild).

## Поток данных

```
┌──────────────┐   JWT    ┌──────────────┐   SQL    ┌──────────────┐
│ React UI     │  Bearer  │  FastAPI     │  Alchemy │   SQLite     │
│ (Vite dev    │──────────│  /api/...    │─────────>│  belp.db     │
│  127.0.0.1:  │          │              │          │              │
│   8560)      │          │  CORS: 8560/ │          │  PostgreSQL- │
│              │          │  8550 + LAN  │          │  ready       │
└──────────────┘          └──────────────┘          └──────────────┘
       │                          │
       │   localStorage:          │ lifespan:
       │   - authTokens           │ - scheduler.start
       │   - quickAccounts        │ - email-loop 60s
       │   - perUser data         │ - token-cleanup 1h
       │   - themeMode            │
       │   - rules                │
       └───────── Capacitor 8 ──────────> APK / IPA
```

## Что в production-TODO (см. PROJECT_STATUS.md «Перспективы»)

- SHA-256 хэширование refresh-токенов.
- Redis для rate-limiter и token blacklist.
- Strict CORS (без LAN-regex).
- Полная HTML-санитизация (bleach / DOMPurify).
- Audit log для update-операций (сейчас только create/delete).
- Document scan: убрать static mount `/uploads/documents` после переключения UI.
- Расширенный allow-list для `PATCH /settings`.
- Реальный push (FCM/APNs).
- Рефакторинг legacy-компонентов в `App.tsx` (MobileHome/DesktopHome не используются).
