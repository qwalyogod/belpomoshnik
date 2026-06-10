# Правила 
1. Оспаривай мои решения. Если подход плохой - скажи прямо. Не соглашайся просто потому что я попросил.
2. Каждый ответ структурируй: что сделано, что нужно от меня, какой следующий шаг.
3. После каждоый задачи предлагай что улучшить и/или автоматизировать.
4. Все что можешь делать ты - делай ты. Твоя задача освободить мое время.

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Что это

«Белпомощник» — кроссплатформенный мобильный помощник для граждан Беларуси (жизненные сценарии: рождение ребёнка, ЖКХ/налоги, потеря паспорта и т.д.). Дипломный проект. Первая демо-бета, React/Vite основной UI, Flet остался только как тонкая нативная WebView-обёртка для APK/iOS-сборки.

## Границы стека (жёстко)

- **Frontend** — только в `reactvitemaket/` (Vite + React 18 + TS + Tailwind 4 + shadcn-style + motion). Mobile и desktop рендерятся в одном дереве через `isMobile` контекст в `src/app/App.tsx`.
- **Backend** — только в `src/backend/` (FastAPI + SQLAlchemy 2 + SQLite MVP). Разделение `models / schemas / api / service / migrations / seeds` сохранять. Без отдельной задачи не ломать API-контракты.
- **`src/mobile_webview.py`** — единственный Flet-файл. Тонкая нативная WebView-оболочка, грузит React-сайт по URL. Своего UI нет, не наращивать. `flet-web` НЕ нужен (WebView не работает в Flutter Web).
- **Удалено и не возвращать**: `src/main.py`, `src/pages/`, `src/components/`, `src/theme/`, `src/data/`, `src/services/` (старый Flet-UI) и тесты `test_dashboard/test_security/test_user_sync`.
- Язык интерфейса: **только русский**. Дизайн — premium Apple-grade (см. `.claude/projects/.../feedback_design_taste.md`).
- Локальный Flet-`main.py` ушёл — все правки UI идут в React.

## Команды

### Запуск dev-окружения (3 процесса)

```bash
# 1) Backend (FastAPI, :8060)
PYTHONPATH=src .venv/bin/uvicorn backend.app:app --host 127.0.0.1 --port 8060

# 2) React frontend (Vite, :8560) — порт зашит в vite.config.ts, CORS allow-list бэка
cd reactvitemaket && pnpm dev

# 2a) То же, но в LAN (для мобильного WebView по Wi-Fi)
cd reactvitemaket && pnpm dev:lan

# 3) Нативный WebView на телефоне (APK-сборка) — только когда (2a) поднят
.venv/bin/flet run --android src/mobile_webview.py        # iPhone: --ios
```

### Инициализация и сброс БД

```bash
PYTHONPATH=src .venv/bin/python -m backend.bootstrap            # схема + роли + тест-аккаунты (идемпотентно)
PYTHONPATH=src .venv/bin/python -m backend.scripts.seed_db      # MVP-сценарий «Рождение ребёнка»
```

Тестовые аккаунты (создаёт `backend.bootstrap`): `citizen@test.local`, `editor@test.local`, `admin@test.local` — пароль `Test12345!`.

### Тесты

```bash
.venv/bin/python -m pytest                                      # все ~60 backend-тестов
.venv/bin/python -m pytest tests/test_auth.py -v                # один файл
.venv/bin/python -m pytest "tests/test_auth.py::TestLogin::test_login_success" -s   # один тест
.venv/bin/python -m pytest -q                                   # короткий режим
.venv/bin/python scripts/smoke_backend.py                       # end-to-end smoke через TestClient (изолированная sqlite)
```

### Сборка native

```bash
cd reactvitemaket && pnpm build                                 # Vite-бандл
cd reactvitemaket && npx cap sync android                       # Capacitor sync перед APK
cd reactvitemaket/android && ./gradlew assembleDebug            # APK
```

CI: `.github/workflows/build-apk.yml` (Node 22, JDK 21) и `build-ipa.yml` — повторяют эти шаги.

## Архитектура

### Frontend (`reactvitemaket/src/app/`)

- **`App.tsx`** — `RootLayout`, `MobileShell`, `DesktopShell`, `MobileHome`, `DesktopHome`, `HeaderUserMenu`, `MobileUserSwitcher` и `AdminWindowMount`. Определяет ShellContext (`isMobile`, `dark`, `openAssistant`, `openAdmin`). Анимации через `motion/react` (`AnimatePresence mode="wait"` при смене маршрута).
- **`routes.tsx`** — `createBrowserRouter`, ~20 маршрутов. `ResponsivePage` свапает mobile/desktop-компонент по `isMobile`. `AdminPageWrapper` / `EditorPageWrapper` гейтят доступ по `role`. Глобальный `Outlet context` (`protectedGuard`, `onAddDoc`, `openScenario`, `openMySituation`) пробрасывается в каждую страницу.
- **`pages.tsx`** — реэкспорт экранов (Catalog, Situations, Documents, Legal, Profile, Login, Register, Onboarding, Finance, News, Sources, ProblemDetail, LawDetail, Notifications, About, Settings, Learning).
- **`components/`** — `belp-ui.tsx` (Logo/Pill/Card/PrimaryButton/GhostButton — базовые примитивы), `extra-screens.tsx` (ScenarioDetail, MySituationDetail, SearchOverlay, DocumentEditModal, GuestGuardModal, AssistantPanel, SettingsPage, LearningPage), `admin-window.tsx`, `content-editor.tsx`, `authorities-editor.tsx`, `law-editor.tsx`, `regions-editor.tsx`, `desktop.tsx`, `screens.tsx`.
- **`data/`** — `store.tsx` (Zustand-подобный стор с `useStore`: `currentUser`, `role`, `quickAccounts`, `signInAs`, `signOut`, `resetSession`, `situations`, `scenarios`, `documents`, `situationProgress`, `loadScenarioDetail`), `mock.ts` (мок-данные + `CATEGORIES`), `types.ts`, `adapters.ts`, `geo.ts`, `geo-regions.json`.
- **`services/`** — `api.ts` (HTTP к бэку, `institutions.ts`, `reminders.ts` (дашборд-дедлайны), `search.ts` (⌘K-оверлей).
- **Tailwind 4** через `@tailwindcss/vite`. Глобальные стили и shadcn-токены — `default_shadcn_theme.css`. Бренд-цвет `#0056FF`, тёмный фон `#07080C`, светлый `#F6F7FB`. `useColorMode` (light/dark) хранится в ShellContext.

### Backend (`src/backend/`)

- **`app.py`** — `create_app()` собирает FastAPI: CORS для `:8560/:8550`, lifespan стартует `scheduler` (фоновые задачи), роутеры `public / admin / auth / user / situations / trackers / articles / assistant`, `/uploads` StaticFiles, `GET /api/health`.
- **`auth.py`** — bcrypt-хэши, JWT (`create_access_token`/`create_refresh_token`, `OAuth2PasswordBearer`), `oauth2_scheme` dependency, `_ROLE_RANK` для RBAC-чеков. Refresh-таблица `RefreshToken`.
- **`database.py`** — engine из `BELPOMOSHNIK_DATABASE_URL` (SQLite или PostgreSQL), `SessionLocal`, `get_db` dep. Pydantic-конфиг в `config.py`.
- **`models.py`** — `Base`, `User`, `Role`, `RefreshToken`, scenario/step/document/region/authority/article/article_view/problem и т.д. — единая схема.
- **`schemas.py`** — Pydantic v2 DTO.
- **`api/`** — 8 роутеров: `auth`, `user`, `admin`, `situations`, `trackers`, `articles`, `assistant`, `public`. Каждый — `APIRouter` с префиксом `/api/...`.
- **`migrations/`** — нумерованные `.sql` (`0001_*.sql`…`0011_problem_detail.sql`), гонит `backend/scripts/migrate.py`.
- **`seeds/`** — `mvp_childbirth.py` (готовый сценарий «Рождение ребёнка»), `full_content.py`.
- **`service.py`**, **`email_service.py`**, **`scheduler.py`**, **`rate_limit.py`** — сквозные сервисы (e-mail, фоновые задачи, лимиты логина).
- **`bootstrap.py`** — `bootstrap_database()`: `Base.metadata.create_all` + роли + тест-аккаунты + опциональный админ из env (`BELPOMOSHNIK_ADMIN_EMAIL` / `BELPOMOSHNIK_ADMIN_PASSWORD`).
- **DB-диалект** — один и тот же код работает на SQLite (dev) и PostgreSQL (prod через `psycopg[binary]`). DDL генерится `Base.metadata.create_all` под диалект автоматически.

### WebView-обёртка (`src/mobile_webview.py`)

Перед `flet run` поднимается `pnpm dev:lan` — URL печатается в терминале (`Network: http://192.168.x.x:8560`), вводится в поле WebView-обёртки. `_PROBE_JS` рисует диагностическую панель прямо на странице (iOS WKWebView не пробрасывает console). Pre-flight `_vite_reachable()` ловит «серый экран» до загрузки.

## Правила для агентов (наследуются из AGENTS.md)

- Перед началом работы читай `AGENTS.md`, `docs/PROJECT_STATUS.md` (баннер актуален, разделы ниже — историческая Flet-справка) и `docs/TASKS.md`.
- Крупные ТЗ-задачи → сначала `docs/TZ_COMPLETION_ROADMAP.md`; задачи по React-UI → `docs/REACT_MIGRATION_PLAN.md` и `docs/REACT_MIGRATION_AUDIT.md`.
- Не выдумывать несуществующее. Планируемое помечать `TODO`. Не ломать API-контракты и архитектуру без причины.
- После крупных изменений обновить `docs/PROJECT_STATUS.md` и `docs/CHANGELOG.md`. Архитектурные решения — в `docs/DECISIONS.md`.
- Backend-разделение `models / schemas / api / service / migrations / seeds` держать.
- Не смешивать UI, моковые данные и бизнес-логику: моки пока живут в `reactvitemaket/src/app/data/mock.ts`, бэкенд-данные приходят через `services/api.ts`.
- Дизайн премиум: чистая типографика, radius ~16, плавные анимации (motion spring 320/32), hover-микроанимации, desktop split-screen, mobile SafeArea.

## Полезные пути

- Активный план после First Beta: `docs/TZ_COMPLETION_ROADMAP.md`
- Спринтовые брифы и старые задачи: `docs/CODEX_SPRINT2_BRIEF.md`, `docs/CODEX_WORKFLOW.md`
- Дизайн-система и iPhone-layout: `docs/DESIGN_SYSTEM.md`, `docs/IOS_LAYOUT_CHECKLIST.md`
- API-контракты: `docs/API_CONTRACTS.md`, `docs/SCENARIO_BACKEND.md`
- Editor-видение: `docs/EDITOR_PANEL_VISION.md`
- Шаблон мок-данных: `docs/MOCK_DATA_SPEC.md`

## Переменные окружения

Секреты в `.env` (gitignored). `mobile_webview.py` читает `REACT_APP_URL` (default — LAN-IP). Backend читает `BELPOMOSHNIK_DATABASE_URL`, `BELPOMOSHNIK_SECRET_KEY`, `BELPOMOSHNIK_ADMIN_EMAIL/PASSWORD` (bootstrap), `SMTP_*` (email_service), `GROQ_API_KEY` (если используется AI-помощник в `api/assistant.py`).
