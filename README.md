# Белпомощник

Веб-система для помощи гражданам Республики Беларусь в решении бытовых и административных задач. Дипломный проект, первая демо-бета (2026-06).

Пользователь описывает жизненную ситуацию («потерял паспорт», «рождение ребёнка», «не пришла квитанция ЖКХ») — приложение даёт пошаговый план: что делать сейчас, какие документы собрать, в какие сроки уложиться, куда обращаться, каких ошибок избегать. Можно сохранить план, отмечать выполненные шаги, вести свои документы, получать напоминания о сроках и видеть релевантные изменения законодательства.

## Стек

| Слой | Технологии |
|---|---|
| **Frontend** | React 18 + Vite 6 + TypeScript + Tailwind 4 + motion, react-router 7, lucide-react. Mobile + desktop shell в одном дереве. |
| **Backend** | FastAPI 0.116 + SQLAlchemy 2.0 + Pydantic 2.11 + JWT (HS256) + bcrypt. SQLite (MVP), PostgreSQL-ready. |
| **WebView-обёртка** | Flet 0.85 — **только** нативная обёртка для APK/iOS-сборки, без своего UI. |
| **Native** | Capacitor 8 → Android APK, iOS IPA. |
| **Тесты** | pytest 9 (82 теста). Smoke-скрипты: `scripts/check.sh`, `scripts/smoke_demo.sh`. |

> **Важно.** Flet используется исключительно как WebView-обёртка (`src/mobile_webview.py`). Весь продуктовый UI — в `reactvitemaket/`. Старые Flet-файлы (`src/main.py`, `src/pages/`, `src/components/`, `src/theme/`, `src/data/`, `src/services/`) удалены в ветке `cleanup/remove-legacy-flet-ui`.

## Требования к окружению

- **Python 3.12+** с `venv` (есть `.venv/` в репо — готово).
- **Node.js 22** + **pnpm 9** для frontend.
- **JDK 21** для Android-сборки (только если собираете APK).
- **macOS + Xcode** для iOS-сборки.

## Быстрый старт

### 1. Backend

```bash
# Из корня репозитория
cp .env.example .env

# Сгенерируйте 32+ символов для SECRET_KEY:
python -c "import secrets; print('BELPOMOSHNIK_SECRET_KEY=' + secrets.token_hex(32))" >> .env

# Установите зависимости (если ещё не установлены)
.venv/bin/pip install -r requirements.txt

# Инициализация БД (идемпотентно)
PYTHONPATH=src .venv/bin/python -m backend.bootstrap
PYTHONPATH=src .venv/bin/python -m backend.scripts.seed_db   # опционально, MVP-контент

# Запуск
PYTHONPATH=src .venv/bin/uvicorn backend.app:app --host 127.0.0.1 --port 8060
```

API: <http://127.0.0.1:8060/api/health> — healthcheck.
OpenAPI: <http://127.0.0.1:8060/docs>.

### 2. Frontend

```bash
cd reactvitemaket
pnpm install
pnpm dev                 # http://127.0.0.1:8560
# Или для мобильного WebView по LAN:
pnpm dev:lan             # биндит на 0.0.0.0:8560
```

CORS backend'а уже настроен на `:8560` и `:8550` (см. `src/backend/app.py`).

### 3. Mobile WebView (APK)

```bash
# Только когда поднят `pnpm dev:lan`:
.venv/bin/flet run --android src/mobile_webview.py        # iPhone: --ios
```

В нативной обёртке появится экран ввода URL фронта (`http://<ваш LAN-IP>:8560`) и бэка (`:8060`). После первого ввода URL'ы запоминаются.

## Тесты

```bash
# Все backend-тесты (82 шт., ~30 сек)
PYTHONPATH=src .venv/bin/python -m pytest -q

# Конкретный файл / тест
PYTHONPATH=src .venv/bin/python -m pytest tests/test_security_fixes.py -v
PYTHONPATH=src .venv/bin/python -m pytest "tests/test_auth.py::TestLogin::test_login_success" -s

# End-to-end smoke
PYTHONPATH=src .venv/bin/python scripts/smoke_backend.py

# Сводная проверка MVP (тесты + smoke + секреты + миграции)
bash scripts/check.sh

# 5-минутный защитный сценарий (требует запущенного backend на :8060)
bash scripts/smoke_demo.sh
```

## Сборка production

```bash
cd reactvitemaket
pnpm build                            # Vite production-bundle в dist/
npx cap sync android                  # Capacitor sync
cd android && ./gradlew assembleDebug # APK
```

CI: `.github/workflows/build-apk.yml` и `build-ipa.yml` повторяют эти шаги на push в main.

## Демо-аккаунты

`backend.bootstrap` создаёт трёх тест-пользователей (только если `BELPOMOSHNIK_ENABLE_TEST_SWITCHER=true`):

| Email | Роль | Пароль |
|---|---|---|
| `citizen@test.local` | citizen | `Test12345!` |
| `editor@test.local` | content_editor | `Test12345!` |
| `admin@test.local` | platform_admin | `Test12345!` |

> ⚠️ **Демо-пароль — только для локальной демонстрации.** В production `BELPOMOSHNIK_ENABLE_TEST_SWITCHER=false`, тест-аккаунты не создаются.

## Демо-режим: важные ограничения

Проект сознательно работает в «демо-режиме» — это **не production-готовый** продукт:

- **Документы.** Сканы хранятся в `data/uploads/documents/` в открытом виде, **не шифруются**. Загрузка реальных паспортных данных в демо запрещена.
- **Refresh-токены.** Хранятся в `refresh_tokens.token` как есть (для SQLite-MVP допустимо). Production TODO: SHA-256.
- **Login rate-limit.** In-memory (`collections.deque`), сбрасывается при рестарте, не шарится между воркерами. Production TODO: Redis.
- **CORS.** `allow_origin_regex` открывает любой LAN IP (намеренно для iPhone WebView). Production TODO: strict allow-list.
- **HTML-санитизация.** Regex-based, режет `<script>`/`<iframe>`/on*-attrs. Production TODO: bleach/DOMPurify.
- **Settings.** `PATCH /api/user/settings` фильтрует payload по allow-list. Не примет `role`, `is_admin`, `password`.
- **Audit log.** Пишет create/delete админ-операций. Update — TODO.

Полный список в `docs/PROJECT_STATUS.md` → «Сознательно отложено в Перспективы».

## Структура репозитория

```
src/
├── backend/             # FastAPI + SQLAlchemy + миграции + seeds
│   ├── api/             # 8 роутеров
│   ├── migrations/      # 0001..0018 (0007 — noop)
│   └── seeds/           # mvp_childbirth.py, full_content.py
└── mobile_webview.py    # Flet WebView-обёртка

reactvitemaket/
├── src/app/
│   ├── App.tsx          # ShellContext, MobileShell, DesktopShell
│   ├── routes.tsx       # ~20 маршрутов
│   ├── pages.tsx        # 18+ страниц
│   ├── components/      # belp-ui, admin/editor, shadcn-набор
│   ├── data/            # store, mock, types, adapters
│   └── services/        # api, a11y, reminders, search
├── android/, ios/       # Capacitor 8
└── pnpm-lock.yaml

docs/                    # PROJECT_STATUS, DEMO_SCRIPT, ARCHITECTURE, API_CONTRACTS…
tests/                   # 7 файлов, 82 теста
scripts/                 # check.sh, smoke_demo.sh, smoke_backend.py, content-pipeline
data/                    # runtime: belp.db, uploads/, exports/
```

## Демо-сценарий на защите

См. `docs/DEMO_SCRIPT.md` — 5–7-минутный план. Ключевые точки:

1. **Гость → проблема** — `/welcome`, индикатор «Backend», карточка «Потерял паспорт».
2. **Регистрация** — переход на `/login?reason=create-plan`.
3. **Моя ситуация** — отметка шагов, прогресс-бар.
4. **Уведомления** — клик навигирует.
5. **Документы** — добавление, demo-предупреждение.
6. **Лента** — фильтры, источник, verified-бэйдж.
7. **Редактор** — создание закон-апдейта + audit-log.
8. **Архитектура** — стек, MVP-готовность.

## Лицензия / Авторы

Дипломный проект. Использует open-source библиотеки (FastAPI, React, Tailwind, motion, …).
