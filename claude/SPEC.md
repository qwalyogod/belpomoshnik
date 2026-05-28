# SPEC — Технические спецификации

## Стек

| Слой | Технологии | Версии |
|------|-----------|--------|
| UI | Python + Flet | 0.85.0 |
| Runtime Python | Python | 3.14 |
| Backend | FastAPI + Uvicorn | 0.116.1 / 0.35.0 |
| ORM | SQLAlchemy | 2.0.41 |
| БД | SQLite (MVP) | — |
| Валидация | Pydantic | 2.11.7 |
| Venv | `.venv/` в корне проекта | — |

## Структура проекта

```
belpomoshnik/
├── claude/             ← рабочие файлы для Claude (этот каталог)
├── assets/             ← статика
├── data/
│   ├── app_state.json          ← локальное состояние пользователя
│   ├── app_state.backup.json   ← автобэкап
│   ├── belpomoshnik.db         ← SQLite база
│   └── private_uploads/        ← сканы документов (gitignored)
├── docs/               ← документация проекта (много .md файлов)
├── src/
│   ├── main.py         ← ГЛАВНЫЙ файл: роутинг + весь стейт + бизнес-логика UI (~2900 строк)
│   ├── backend/
│   │   ├── app.py      ← FastAPI create_app()
│   │   ├── models.py   ← SQLAlchemy-модели
│   │   ├── schemas.py  ← Pydantic-схемы
│   │   ├── service.py  ← сервисный слой
│   │   ├── database.py ← engine, SessionLocal
│   │   ├── enums.py    ← Enum-классы
│   │   ├── config.py   ← настройки
│   │   ├── api/
│   │   │   ├── public.py  ← публичные эндпоинты (/api/...)
│   │   │   └── admin.py   ← admin-эндпоинты (/api/admin/...)
│   │   ├── migrations/
│   │   │   └── 0001_initial.sql
│   │   └── seeds/
│   │       └── mvp_childbirth.py
│   ├── pages/          ← 15 экранов (по одному файлу)
│   │   ├── home_page.py
│   │   ├── problems_page.py
│   │   ├── problem_detail_page.py
│   │   ├── scenarios_page (scenario_templates_page.py)
│   │   ├── scenario_detail_page.py
│   │   ├── situations_page.py
│   │   ├── situation_detail_page.py
│   │   ├── documents_page.py
│   │   ├── notifications_page.py
│   │   ├── profile_page.py
│   │   ├── legal_updates_page.py
│   │   ├── law_detail_page.py
│   │   ├── learning_progress_page.py
│   │   ├── admin_page.py
│   │   ├── login_page.py
│   │   ├── register_page.py
│   │   ├── onboarding_page.py
│   │   └── about_page.py
│   ├── components/
│   │   ├── bottom_nav.py
│   │   ├── layout.py       ← SafeArea-helpers, mobile_page_layout
│   │   ├── cards.py
│   │   ├── buttons.py
│   │   └── app_bar.py
│   ├── data/
│   │   └── mock_data.py    ← все мок-данные (PROBLEMS, SCENARIOS, INSTITUTIONS и др.)
│   ├── services/
│   │   ├── local_store.py  ← load_app_state / save_app_state
│   │   ├── dashboard.py    ← build_dashboard_data, parse_due_date, status_from_progress
│   │   ├── institutions.py ← match_institutions
│   │   ├── public_api.py   ← PublicAPIClient (http к /api/...)
│   │   └── admin_api.py    ← AdminAPIClient (http к /api/admin/...)
│   └── theme/
│       └── app_theme.py    ← APP_COLORS, build_theme()
├── Web app design for Belpomoshch/  ← React/Vite макет (только visual reference!)
├── requirements.txt
├── pyproject.toml
└── .gitignore
```

## Маршруты UI (Flet routes)

| Маршрут | Экран |
|---------|-------|
| `/` | HomePage |
| `/problems` | ProblemsPage |
| `/problem-detail` | ProblemDetailPage |
| `/scenarios` | ScenarioTemplatesPage |
| `/scenario-detail` | ScenarioDetailPage |
| `/situations` | SituationsPage |
| `/situation-detail` | SituationDetailPage |
| `/documents` | DocumentsPage |
| `/notifications` | NotificationsPage |
| `/profile` | ProfilePage |
| `/legal-updates` | LegalUpdatesPage |
| `/law-detail` | LawDetailPage |
| `/learning` | LearningProgressPage |
| `/admin` | AdminPage |
| `/login` | LoginPage |
| `/register` | RegisterPage |
| `/onboarding` | OnboardingPage |
| `/about` | AboutPage |

## API эндпоинты (backend)

```
GET  /api/health
GET  /api/problems
GET  /api/problems/{id}
GET  /api/scenarios
GET  /api/scenarios/{slug}
GET  /api/admin/problems
POST /api/admin/problems
GET  /api/admin/scenarios
POST /api/admin/scenarios
GET  /api/admin/scenarios/{id}
GET  /api/admin/scenarios/{id}/stages
GET  /api/admin/stages/{id}/steps
POST /api/admin/stages
POST /api/admin/steps
PATCH /api/admin/problems/{id}/publish
PATCH /api/admin/problems/{id}/draft
PATCH /api/admin/scenarios/{id}/publish
PATCH /api/admin/scenarios/{id}/draft
```

## Команды запуска

```bash
# Desktop
.venv/bin/flet run src/main.py

# Браузер (web preview)
.venv/bin/flet run -w src/main.py --host 127.0.0.1 -p 8550

# iOS (если устройство настроено)
.venv/bin/flet run --ios src/main.py

# Backend API
PYTHONPATH=src uvicorn backend.app:app --host 127.0.0.1 --port 8060

# Инициализация БД
PYTHONPATH=src python -m backend.scripts.init_db
PYTHONPATH=src python -m backend.scripts.seed_db

# Синтаксическая проверка
.venv/bin/python -m compileall src
```

Демо-аккаунт: `ivan@example.by` / `123456`

## Состояние приложения (app_state.json)

Ключевые ключи:
- `users` — словарь {email: {password, profile}}
- `auth_state` — {logged_in, email, remember}
- `app_user` — профиль текущего пользователя
- `app_settings` — {large_text, high_contrast, learning_mode, email_notifications, onboarding_completed}
- `personal_documents` — список документов пользователя
- `privacy_settings` — {hide_sensitive_documents}
- `uploaded_files` — метаданные загруженных сканов
- `institutions` — справочник госучреждений
- `situations` — список ситуаций пользователя
- `situation_tasks` — задачи по всем ситуациям
- `notifications` — уведомления
- `law_updates` — закон-апдейты (для редактора)
- `official_sources` — справочник официальных источников
- `admin_roles` / `admin_users` / `admin_audit_logs` — для adminки
- `saved_problem_ids` / `saved_law_ids` / `favorite_scenario_ids` — сохранённые объекты

## Цветовая система (APP_COLORS)

Определена в `src/theme/app_theme.py`. Основные:
- `primary` — синий
- `success` / `warning` / `danger`
- `background` — `#F6F8FB`
- `surface` — белый
- `text` / `muted` / `border`

## Шаблоны сценариев (mock_data.py → SCENARIO_TEMPLATES)

Доступные шаблоны:
1. Рождение ребёнка (`childbirth`)
2. Потеря паспорта (`lost-passport`)
3. Расторжение брака (`divorce`)
4. Открытие ИП (`open-ip`)
5. Переезд и регистрация (`relocation`)

Каждый шаблон содержит: `stages[]` (этапы) и `tasks[]` (задачи с `depends_on`, `institution_types`, `documents`).

## Роли (демо)

- `citizen` — Гражданин (только просмотр)
- `content_editor` — Редактор контента (CRUD закон-апдейтов, источников)
- `platform_admin` — Админ площадки (полный доступ)

## Новые ключи стейта (будут добавлены по ТЗ)

По мере выполнения плана в `default_state` будут добавлены:

- `utility_payments` — трекер ЖКХ (адрес, лицевой счёт, показания, платежи)
- `tax_obligations` — трекер налогов (обязательство, срок, сумма, статус)
- `user_activity_log` — журнал действий пользователя
- `document_reminders_settings` — настройки напоминаний по документам (дни: 7, 30, 60, 120)

Расширение `app_user`:
- `district` — район
- `address` — адрес
- `employment_status` — наёмный / ИП / студент / пенсионер / безработный
- `has_children` — bool
- `has_car` — bool
- `is_homeowner` — bool
- `is_renter` — bool

## Новые маршруты (будут добавлены)

- `/utility` — трекер ЖКХ
- `/taxes` — трекер налогов

## Известные ограничения

- Авторизация без JWT/RBAC (локальный MVP)
- Backend подключён только для сценария «Рождение ребёнка» через public API
- Личные документы без шифрования
- Android-адаптация не выполнялась
- Нет drag-and-drop в конструкторе сценариев
