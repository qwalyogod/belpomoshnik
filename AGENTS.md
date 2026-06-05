# AGENTS.md

Главные правила для AI-агентов, работающих с проектом «Белпомощник».

## Перед началом работы

- Всегда читать этот файл перед изменениями.
- Перед изменениями проверять `docs/PROJECT_STATUS.md` и `docs/TASKS.md`.
- Перед крупными задачами по закрытию ТЗ читать `docs/TZ_COMPLETION_ROADMAP.md`.
- Перед задачами по переносу интерфейса на React/Vite читать `docs/REACT_MIGRATION_PLAN.md` и `docs/REACT_MIGRATION_AUDIT.md`.
- Если задача крупная, сначала кратко зафиксировать план действий.
- Не делать огромные изменения за один раз без необходимости.

## Границы проекта

- Продукт = React/Vite frontend (`reactvitemaket/`) + FastAPI backend (`src/backend/`).
- Нативный Flet-UI удалён (ветка `cleanup/remove-legacy-flet-ui`). `src/main.py`,
  `src/pages/`, `src/components/`, `src/theme/`, `src/data/`, `src/services/` больше не существуют.
- `src/mobile_webview.py` — единственный оставшийся Flet-файл: тонкая нативная
  WebView-оболочка, которая открывает тот же React-сайт. Это «обманка» для демонстрации
  кроссплатформенного приложения (APK/iOS). Своего UI у неё нет — не наращивать.
- Frontend трогать только в `reactvitemaket/` (Vite/React/TypeScript).
- Backend трогать только в `src/backend/` (FastAPI + SQLAlchemy + SQLite MVP),
  разделение `models / schemas / api / service / migrations / seeds` сохранять.
- Запуск frontend:           `cd reactvitemaket && pnpm dev`
- Запуск backend:            `PYTHONPATH=src uvicorn backend.app:app --host 127.0.0.1 --port 8060`
- WebView-обманка на телефоне: `.venv/bin/flet run --android src/mobile_webview.py`
  (поднять React по LAN: `cd reactvitemaket && pnpm dev:lan`).
- Без отдельной задачи не переписывать backend-стек и не ломать API-контракты.
- `docs/TZ_COMPLETION_ROADMAP.md` является рабочим планом развития после First Beta.
- `docs/REACT_MIGRATION_PLAN.md` описывает завершённый переход UI на React/Vite.

## Поведение AI-агента

- Не придумывать несуществующие функции.
- Не писать, что функция реализована, если она только планируется.
- Если информации не хватает, помечать как `TODO`, а не выдумывать.
- Не менять архитектуру без причины.
- Не удалять файлы без явной необходимости.
- Не смешивать UI, моковые данные и будущую бизнес-логику.
- Для backend-изменений поддерживать разделение: `models` / `schemas` / `api` / `service` / `migrations` / `seeds`.
- После крупных изменений обновлять `docs/PROJECT_STATUS.md`.
- После изменений документации или кода обновлять `docs/CHANGELOG.md`.
- Если принято архитектурное решение, записывать его в `docs/DECISIONS.md`.

## Интерфейс

- Русский язык интерфейса обязателен.
- Интерфейс должен быть простым, современным и понятным.
- Дизайн переносить максимально близко к Figma, когда макеты будут доступны.
- Использовать светлую тему, карточки, крупный читаемый текст и нижнюю навигацию.
- Не добавлять сложный дизайн, который не подтвержден требованиями или Figma.
