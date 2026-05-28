# GEMINI.md - Проект «Белпомощник»

## Обзор проекта
«Белпомощник» — это кроссплатформенное мобильное приложение на **Flet/Python**, предназначенное для информационной поддержки граждан Республики Беларусь. Оно предоставляет пошаговые планы действий в различных жизненных ситуациях (рождение ребенка, потеря паспорта и др.).

### Технологический стек
- **Frontend:** Flet (Python-фреймворк для UI).
- **Backend:** FastAPI (основа API для админ-панели и сценариев).
- **Database:** SQLAlchemy + SQLite (MVP-хранилище).
- **Validation:** Pydantic.
- **Documentation:** Markdown (папка `docs/`).

## Архитектура
Проект разделен на мобильное приложение и backend-основу:
- `src/main.py`: Точка входа и управление состоянием Flet-приложения.
- `src/pages/`: Экраны приложения (Home, Problems, Situations, etc.).
- `src/components/`: Переиспользуемые UI-компоненты (Layout, Cards, Buttons).
- `src/backend/`: Код сервера (API, модели данных, миграции).
- `src/data/`: Моковые данные (`mock_data.py`) и локальное состояние (`app_state.json`).
- `src/theme/`: Глобальная тема приложения (`app_theme.py`).

## Команды запуска и разработки

### Подготовка окружения
```bash
# Активация окружения (macOS/Linux)
source .venv/bin/activate

# Активация окружения (Windows)
.venv\Scripts\activate

# Установка зависимостей
pip install -r requirements.txt
```

### Запуск приложения (Flet)
```bash
# Обычный запуск
flet run src/main.py

# Web-превью
flet run --web src/main.py
```

### Backend (FastAPI)
```bash
# Инициализация и заполнение БД
PYTHONPATH=src python -m backend.scripts.init_db
PYTHONPATH=src python -m backend.scripts.seed_db

# Запуск API
PYTHONPATH=src uvicorn backend.app:app --host 127.0.0.1 --port 8060
```

## Конвенции разработки

### Общие правила (см. AGENTS.md)
- **Язык интерфейса:** Только русский.
- **Стиль кода:** Придерживаться функционального стиля для билдеров страниц (`build_..._page`).
- **UI:** Использовать компоненты из `src/components` и цвета из `src/theme/app_theme.py`.
- **Данные:** Для новых функций сначала использовать моковые данные в `src/data/mock_data.py`, затем интегрировать с API.

### Документирование
- Все архитектурные решения фиксируются в `docs/DECISIONS.md`.
- Крупные изменения вносятся в `docs/CHANGELOG.md`.
- Текущие задачи отслеживаются в `docs/TASKS.md` и `docs/PROJECT_STATUS.md`.

### Работа с Flet
- Использовать `SafeArea` для мобильной адаптации (особенно для iPhone).
- Состояние приложения (state) в `src/main.py` передается через замыкания или хранится в `page.session` (хотя в текущем MVP много глобальных словарей внутри `main`).

## Важные файлы
- `AGENTS.md`: Ключевые инструкции для AI-агентов.
- `docs/ARCHITECTURE.md`: Описание текущей и будущей структуры.
- `src/main.py`: Основной файл с логикой навигации и состоянием.
- `data/app_state.json`: Локальное хранилище данных пользователя в MVP.
