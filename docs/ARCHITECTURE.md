# Архитектура проекта

## Текущая архитектура

Проект состоит из двух частей:

- mobile_app на Flet/Python;
- backend foundation на FastAPI + SQLAlchemy + SQLite (MVP-уровень для админ-панели и сценариев).

```text
belpomoshnik/
├── assets/
├── src/
│   ├── main.py
│   ├── backend/
│   │   ├── app.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── api/
│   │   ├── migrations/
│   │   ├── scripts/
│   │   └── seeds/
│   ├── pages/
│   ├── components/
│   ├── data/
│   ├── services/
│   └── theme/
├── requirements.txt
├── pyproject.toml
├── README.md
└── docs/
```

## Назначение папок

- `src/main.py` - точка входа приложения.
- `src/backend/app.py` - вход API (FastAPI).
- `src/backend/models.py` - ORM-модели базы данных сценариев.
- `src/backend/schemas.py` - валидация и DTO-схемы API.
- `src/backend/api` - public/admin endpoints.
- `src/backend/migrations` - SQL-миграции структуры БД.
- `src/backend/scripts` - команды инициализации/seed.
- `src/backend/seeds` - начальное наполнение MVP-сценариями.
- `src/pages` - экраны приложения.
- `src/components` - переиспользуемые UI-компоненты.
- `src/data` - моковые данные.
- `src/services` - локальные сервисы расчётов и подбора данных, например dashboard и подбор учреждений.
- `src/theme` - цвета, стили и константы.
- `assets` - изображения и иконки.
- `docs` - документация проекта и правила для AI-агентов.

## Текущие ограничения

- Авторизации пока нет.
- RBAC (user/editor/admin) пока не применен на уровне API.
- Мобильный клиент пока в основном работает на моковых данных.
- SQLite используется как MVP-хранилище для сценариев; PostgreSQL планируется позже.

## Будущая архитектура

Планируется следующая архитектура production-уровня:

- `mobile_app` на Flet/Python.
- Backend на Node.js Express (или развитие текущего Python backend по решению команды).
- PostgreSQL.
- REST API.
- JWT auth.
- Роли: `user`, `editor`, `admin`.

Текущий backend-слой сделан как расширяемая учебная основа: модели и API уже разделены по сущностям, поэтому миграция на PostgreSQL и полноценную авторизацию не потребует переписывания мобильного интерфейса.
