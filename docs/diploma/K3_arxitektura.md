# K3. Архитектура системы

## 3.1 Общая архитектура

«Белпомощник» построен по двухзвенной архитектуре: Flet-клиент (frontend + UI-логика) + FastAPI backend (REST API + база данных). В MVP клиент работает автономно с локальным состоянием, а backend предоставляет альтернативный источник данных.

```
┌─────────────────────────────────────────────────────┐
│                    Flet Client                      │
│  ┌────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │  Pages     │  │  Components  │  │  Theme      │ │
│  │ (18 файлов)│  │ (buttons,    │  │ app_theme   │ │
│  │            │  │  cards,      │  │ light/dark  │ │
│  │            │  │  layout)     │  │             │ │
│  └────────────┘  └──────────────┘  └─────────────┘ │
│  ┌─────────────────────────────────────────────────┐│
│  │               main.py (~4500 строк)             ││
│  │  State Manager | Navigation | Event Handlers    ││
│  └─────────────────────────────────────────────────┘│
│  ┌────────────────────┐  ┌──────────────────────────┐│
│  │  data/mock_data.py │  │ data/app_state.json       ││
│  │  (контент-сидинг)  │  │ (локальный персист)       ││
│  └────────────────────┘  └──────────────────────────┘│
└───────────────────────┬─────────────────────────────┘
                        │ HTTP / REST
                        ▼
┌─────────────────────────────────────────────────────┐
│                 FastAPI Backend                      │
│  ┌────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │ api/public │  │ api/admin    │  │ api/auth    │ │
│  │ api/user   │  │              │  │ api/user    │ │
│  └────────────┘  └──────────────┘  └─────────────┘ │
│  ┌─────────────────────────────────────────────────┐│
│  │         SQLAlchemy ORM + Pydantic schemas       ││
│  └─────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────┐│
│  │              SQLite (MVP) / PostgreSQL           ││
│  └─────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────┘
```

## 3.2 Технологический стек

| Уровень | Технология | Версия | Назначение |
|---------|-----------|--------|-----------|
| UI-фреймворк | Flet | 0.85 | Кросс-платформенный Flutter+Python |
| Язык | Python | 3.14 | Весь проект |
| Backend | FastAPI | 0.115+ | REST API |
| ORM | SQLAlchemy | 2.0+ | Модели и запросы |
| Валидация | Pydantic | 2.x | Схемы API |
| СУБД MVP | SQLite | 3.x | Локальная база |
| Аутентификация | python-jose + passlib | — | JWT + bcrypt |
| ASGI-сервер | uvicorn | 0.x | Запуск FastAPI |

## 3.3 Структура исходного кода

```
belpomoshnik/
├── src/
│   ├── main.py                  # Точка входа, state, навигация
│   ├── theme/
│   │   └── app_theme.py         # Цвета, шрифты, build_theme()
│   ├── components/
│   │   ├── buttons.py           # primary_button, ghost_button
│   │   ├── cards.py             # app_card, icon_circle, hint_card
│   │   └── layout.py            # desktop_content
│   ├── pages/                   # 18 страниц-модулей
│   │   ├── home_page.py
│   │   ├── problems_page.py
│   │   ├── problem_detail_page.py
│   │   ├── scenario_detail_page.py
│   │   ├── scenarios.py         # Каталог сценариев
│   │   ├── situations_page.py
│   │   ├── situation_detail_page.py
│   │   ├── documents_page.py
│   │   ├── profile_page.py
│   │   ├── notifications_page.py
│   │   ├── legal_updates_page.py
│   │   ├── law_detail_page.py
│   │   ├── email_preview_page.py
│   │   ├── login_page.py
│   │   ├── register_page.py
│   │   ├── onboarding_page.py
│   │   ├── about_page.py
│   │   ├── learning_progress_page.py
│   │   ├── search_page.py
│   │   ├── utility_tracker_page.py
│   │   ├── tax_tracker_page.py
│   │   └── admin_page.py        # Полная admin CMS
│   ├── data/
│   │   ├── mock_data.py         # Контентный сидинг (9 сценариев, 14 проблем)
│   │   └── app_state.json       # Персистентный локальный стейт
│   └── backend/
│       ├── app.py               # FastAPI application
│       ├── models.py            # SQLAlchemy ORM модели
│       ├── schemas.py           # Pydantic schemas
│       ├── database.py          # Engine, get_db()
│       ├── security.py          # JWT, hashing
│       ├── email_service.py     # Email queue + SMTP
│       ├── api/
│       │   ├── public.py        # GET /api/problems, /api/scenarios, /api/law-updates
│       │   ├── admin.py         # CRUD /api/admin/*
│       │   ├── auth.py          # POST /api/auth/register, /login, /refresh
│       │   └── user.py          # /api/me, /api/me/documents, notifications
│       └── migrations/
│           ├── 0001_initial.sql
│           └── 0002_auth.sql
├── data/
│   └── private_uploads/         # Загруженные файлы документов
├── docs/
│   ├── SOURCES.md
│   ├── diploma/                 # Дипломная документация (K1–K12)
│   └── redesign-progress/       # Скриншоты редизайна
└── claude/
    ├── PLAN.md                  # Рабочий план
    └── SPEC.md                  # Техническое задание
```

## 3.4 Архитектурные паттерны

### State management
Весь клиентский стейт хранится как Python-словари внутри функции `main()` (closure). Изменение стейта → `save_current_state()` → `route_change()` для ре-рендера. Стейт персистируется в `data/app_state.json`.

```python
# Пример: обновление ситуации
situation["status"] = "completed"
save_current_state()
route_change()
```

### Навигация
Route-based: каждый экран — отдельный URL-путь. Функция `route_change()` в конце `main.py` принимает `page.route` и выбирает нужный билдер страницы.

```
/           → home_page
/problems   → problems_page
/scenarios  → scenario_detail_page
/situations → situations_page
/documents  → documents_page
/profile    → profile_page
/search     → search_page
/utility    → utility_tracker_page
/taxes      → tax_tracker_page
/legal-updates → legal_updates_page
/admin      → admin_page
```

### Desktop vs Mobile layout
Страницы адаптируются через `page.window.width > 900` (desktop breakpoint). На desktop — двухколоночный layout с `desktop_content(width=960)`, на mobile — полная ширина с нижней навигацией.

### Fallback на mock-данные
Если backend недоступен, клиент использует данные из `mock_data.py` и локального `app_state.json`. Ошибки API перехватываются на каждом экране с отображением предупреждения.

## 3.5 Безопасность

- Пароли: bcrypt-хеширование через passlib (H4).
- Аутентификация: JWT access token (15 мин) + refresh token (7 дней) (H3).
- RBAC: роли `user` / `editor` / `admin` проверяются на уровне FastAPI Depends (H5–H6).
- Персональные файлы хранятся в `data/private_uploads/` вне публичного webroot (H7).
- Политика персональных данных задокументирована в `docs/SECURITY_POLICY.md` (H8).
- Audit trail: каждое действие редактора пишется в `admin_audit_logs` (H9).

## 3.6 Email и уведомления

```
Trigg event (doc expiry, tax deadline)
        │
        ▼
  enqueue_email(db, ...)  ← email_service.py
        │
        ▼
  email_notifications table (status=pending)
        │
        ▼
  Scheduler / cron: send_pending_emails(db)
        │
        ▼
  SMTP → реальная отправка (production)
  Preview screen → только UI (MVP)
```
