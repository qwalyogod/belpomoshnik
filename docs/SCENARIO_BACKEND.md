# Backend сценариев (MVP)

## Назначение

Backend-слой нужен для админ-управления жизненными сценариями и выдачи структурированных данных мобильному приложению.

Текущая реализация: `FastAPI + SQLAlchemy + SQLite (MVP)`.

## Где находится

- `src/backend/models.py` — ORM-модели и связи.
- `src/backend/schemas.py` — валидация и DTO.
- `src/backend/service.py` — сервисная логика.
- `src/backend/api/public.py` — публичные API endpoints.
- `src/backend/api/admin.py` — admin API endpoints.
- `src/backend/migrations/0001_initial.sql` — миграция схемы.
- `src/backend/seeds/mvp_childbirth.py` — seed сценария «Рождение ребёнка».

## Ключевые сущности

- `Problem`
- `Scenario`
- `ScenarioStage`
- `ScenarioStep`
- `Document`
- `Authority`
- `Deadline`
- `NotificationRule`
- `ScenarioDependency`
- `RelatedScenario`
- `SourceReference`
- `LawUpdate`

## Основные связи

- `Problem 1 -> N Scenario`
- `Scenario 1 -> N ScenarioStage`
- `ScenarioStage 1 -> N ScenarioStep`
- `ScenarioStep N <-> N Document` (через `scenario_step_documents`)
- `ScenarioStep N -> 1 Authority` (опционально)
- `ScenarioStep N -> 1 Deadline` (опционально)
- `ScenarioStep 1 -> N NotificationRule`
- `Scenario 1 -> N ScenarioDependency`
- `Scenario 1 -> N RelatedScenario`
- `Scenario/Stage/Step -> N SourceReference` (polymorphic via `sourceable_type/sourceable_id`)
- `Scenario/Step -> N LawUpdate`

## Инициализация

```bash
PYTHONPATH=src python -m backend.scripts.init_db
PYTHONPATH=src python -m backend.scripts.seed_db
```

## Запуск API

```bash
PYTHONPATH=src uvicorn backend.app:app --host 127.0.0.1 --port 8060
```

## Public API

- `GET /api/problems`
- `GET /api/problems/{slug}`
- `GET /api/scenarios/{slug}`
- `GET /api/scenarios/{slug}/steps`
- `GET /api/documents`
- `GET /api/authorities`

## Admin API (MVP)

- Проблемы: `GET/POST/PUT /api/admin/problems...`
- Сценарии: `GET/POST/PUT /api/admin/scenarios...`
- Этапы/шаги: `POST /api/admin/scenarios/{id}/stages`, `POST /api/admin/stages/{id}/steps`, `PUT /api/admin/stages/{id}`, `PUT /api/admin/steps/{id}`
- Документы: `GET/POST/PUT /api/admin/documents...`
- Привязка документов к шагам: `POST/DELETE /api/admin/steps/{step_id}/documents/{document_id}`
- Организации: `GET/POST/PUT /api/admin/authorities...`
- Сроки: `GET/POST/PUT /api/admin/deadlines...`
- Уведомления: `POST/PUT /api/admin/notification-rules...`
- Зависимости: `POST /api/admin/dependencies`
- Связанные сценарии: `POST /api/admin/related-scenarios`
- Источники: `POST /api/admin/source-references`
- Обновления законодательства: `GET/POST/PUT /api/admin/law-updates...`

## Источники данных

Для seed и сценариев используются только официальные открытые источники РБ (ссылки):

- `https://pravo.by`
- `https://www.portal.gov.by`
- `https://www.mintrud.gov.by`
- `https://minjust.gov.by`

Полные тексты нормативных документов в базу не копируются; хранятся структурированные поля и ссылки.

