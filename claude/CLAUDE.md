# CLAUDE.md — Инструкции для Claude

Этот файл читать в начале каждой сессии. Здесь правила работы с проектом.

## Как экономить токены

1. **Не читать весь main.py целиком.** Файл ~2900 строк. Читать только нужный offset+limit.
   - Первые ~200 строк: импорты и инициализация состояния
   - 200–800: функции работы с файлами, диалогами, навигацией
   - 800–1200: логика сценариев, проблем, ситуаций
   - 1200–1900: CRUD документов, задач, ситуаций
   - 1900–2500: профиль, adminка, закон-апдейты
   - 2500–2918: route_change (рендер страниц по маршруту)

2. **Не читать `docs/PROJECT_STATUS.md` полностью** — там ~350 строк changelog. Читать только секции «Сейчас в работе» и «Что нужно сделать следующим».

3. **Не читать mock_data.py полностью** — там большие структуры данных. Grep нужный символ, потом читать конкретный фрагмент.

4. **React/Vite папка** (`Web app design for Belpomoshch/`) — только visual reference. Никогда не трогать её код, не запускать npm.

5. **Перед правкой любого файла** — сначала grep или read нужной части, не читать файл целиком если он > 200 строк.

6. **Читать `claude/PLAN.md`** — там полный план работ с текущим этапом. Не нужно перечитывать ТЗ каждый раз.

## Правила работы с кодом

### Обязательные
- Язык интерфейса — только **русский**
- Стек UI — только **Flet** (никакого React, HTML, CSS, JS в production)
- Python — `.venv/bin/python` или `source .venv/bin/activate`, не системный python
- Не углублять визуал без необходимости — фокус на внутренней логике и соответствии ТЗ
- Все новые сущности — сначала mock/local state, потом backend
- Проверять синтаксис: `.venv/bin/python -m compileall src`
- Основной режим проверки до закрытия ТЗ: **web** (`flet run -w`)

### После крупных изменений обновлять
- `docs/PROJECT_STATUS.md`
- `docs/TASKS.md`
- `docs/CHANGELOG.md`
- `claude/PLAN.md` (отмечать выполненное)
- При необходимости `docs/DECISIONS.md`

### Запрещено без отдельной задачи
- Начинать PostgreSQL/JWT/RBAC пока локальная логика не стабильна (этапы A–F)
- Переписывать backend-стек (FastAPI + SQLAlchemy + SQLite)
- Трогать папку `Web app design for Belpomoshch/`
- Менять структуру `app_state.json` без обратной совместимости

### Стиль кода
- Комментарии не добавлять (только если логика неочевидна)
- Следовать существующему стилю Flet-компонентов в pages/
- Цвета — только через `APP_COLORS["..."]` из `theme/app_theme.py`
- Новые цвета в APP_COLORS не добавлять без необходимости

## Архитектурные паттерны проекта

### Стейт-менеджмент
Весь стейт живёт в `main.py` как словари Python (замыкания). Пример:
```python
situations_state = stored_state["situations"]  # список dict
current_situation = {"id": "childbirth"}       # текущий выбранный объект
```
Изменение стейта → `save_current_state()` → `route_change()` для ре-рендера.

### Навигация
```python
page.run_task(page.push_route, "/situations")  # переход на маршрут
```
Весь рендер — в функции `route_change()` в конце main.py (строки ~2500–2918).

### Диалоги
Использовать `_form_dialog()` и `_open_control()` из main.py. Не использовать `page.dialog` напрямую.

### Сохранение состояния
После любого изменения данных: `save_current_state()`. Функция делает backup и сохраняет в `data/app_state.json`.

### Добавление нового экрана
1. Создать `src/pages/new_page.py` с функцией `build_new_page(...)`
2. Импортировать в `main.py`
3. Добавить маршрут в `NAV_ROUTES` (если нужно в навигации)
4. Добавить case в `route_change()`

### Добавление новых данных
Новые мок-данные → `src/data/mock_data.py`.
Новые ключи в стейте → добавить в `default_state` в `main.py` + загрузку из `stored_state`.

## Что делать в начале новой задачи

1. Прочитать этот файл (уже сделано)
2. Прочитать `claude/PLAN.md` — найти текущий этап и задачу
3. Grep нужные символы/файлы — НЕ читать всё подряд
4. Сделать изменения
5. Запустить `.venv/bin/python -m compileall src` для проверки
6. Обновить документацию если изменения значительные
7. Отметить выполненное в `claude/PLAN.md`

## Быстрый grep-справочник

```bash
# Найти где рендерится конкретный маршрут
grep -n '"/situations"' src/main.py

# Найти функцию в main.py
grep -n "def open_situation" src/main.py

# Найти использование цвета
grep -rn 'APP_COLORS\["danger"\]' src/

# Найти данные в mock_data
grep -n "SCENARIO_TEMPLATES\|SITUATIONS\|PROBLEMS" src/data/mock_data.py

# Найти импорты в main.py
grep -n "^from\|^import" src/main.py

# Найти ключи стейта
grep -n "default_state\[" src/main.py
```

## FAQ / типичные проблемы

**Q: Почему `flet` не найден?**
A: Использовать `.venv/bin/flet`, не глобальный `flet`.

**Q: Откуда берётся конкретный экран при переходе на маршрут?**
A: Искать в `route_change()` в конце `main.py` (~строка 2500+).

**Q: Как найти где хранится конкретный кусок стейта?**
A: Grep по ключу в `default_state` (начало main.py, ~строка 102).

**Q: Backend работает?**
A: Только если запущен отдельно: `PYTHONPATH=src uvicorn backend.app:app --host 127.0.0.1 --port 8060`. UI gracefully fallback-ит на мок-данные при недоступном API.

**Q: Что такое `Web app design for Belpomoshch/`?**
A: React/Vite прототип только для визуальной референции. Не трогать, не запускать.

**Q: В каком порядке делать задачи?**
A: Строго по `claude/PLAN.md`. Сначала локальная логика (A–F), потом backend (G–H), потом документация (K).

## Команды проверки

```bash
# Синтаксическая проверка
.venv/bin/python -m compileall src

# Web-проверка (основной режим)
.venv/bin/flet run -w src/main.py --host 127.0.0.1 -p 8550

# Desktop
.venv/bin/flet run src/main.py

# Backend API
PYTHONPATH=src .venv/bin/uvicorn backend.app:app --host 127.0.0.1 --port 8060
```
