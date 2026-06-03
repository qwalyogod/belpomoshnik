# Codex brief — «Белпомощник», Sprint 2

> Передай этому файлу + `docs/TZ_USER_ORIENTED_PROJECT_REPORT.md` + полный текст ТЗ (22 раздела). Этого достаточно, чтобы понять контекст и задачи.

## Что за проект

«Белпомощник» — кроссплатформенное приложение (Flet/Python desktop + web) для информационной поддержки граждан РБ. Backend: FastAPI + SQLAlchemy, БД PostgreSQL (через Docker), SMTP через MailHog.

- Клиент: `src/main.py` (~5800 строк, монолит с вложенными handlers), страницы `src/pages/*.py`, компоненты `src/components/*.py`.
- Тема/цвета: единый источник `src/theme/app_theme.py` (`APP_COLORS`, `ts()` для масштаба шрифта, `CENTER = ft.Alignment(0,0)`).
- Backend: `src/backend/` (api/auth.py, api/admin.py, api/user.py, api/situations.py, api/trackers.py, models.py, bootstrap.py, миграции `migrations/*.sql`).
- Клиентские API: `src/services/auth_api.py`, `user_api.py`, `admin_api.py`, `public_api.py`, `user_sync.py` (маппинг Flet↔backend), `role_guard.py`.
- Тесты: `tests/` — 98 pytest + `scripts/integration_client.py` (23 live-проверки на PG).

## Что УЖЕ сделано (НЕ трогай без причины)

**Backend полностью построен и протестирован** (98 pytest на SQLite и PostgreSQL, 23 integration на реальном PG):
- Auth: bcrypt напрямую (passlib выкинут — несовместим с bcrypt 5.x), JWT+jti, refresh rotation, rate-limit, RBAC (`citizen < content_editor < platform_admin`).
- User-data API: profile/settings/documents/situations/tasks/notifications/utility/taxes — всё owner-isolated.
- `user_sync.py` — pull/push с маппингом имён полей Flet↔API (документы: `document_type`↔`doc_type` и т.д.).
- PostgreSQL-ready (`backend/bootstrap.py`), SMTP проверен через MailHog.

**Sprint 1 (только что завершён) — гостевой режим, роли, header:**
- `services/role_guard.py`: `require_auth`, `require_role`, `is_guest`, `current_role` (citizen<editor<admin).
- Гостевой режим: незалогиненный видит весь интерфейс read-only; мутирующие handlers обёрнуты `require_user(...)` → открывают `components/guest_modal.py`.
- `components/forbidden_page.py` — 403 для `/admin` без прав; роут `/admin*` защищён `require_role("content_editor")`.
- RBAC-UI: `components/sidebar.py` `_service_items_for(role)` — admin-пункт только админу.
- Тестовые аккаунты: миграция `0006_test_accounts.sql` (`User.is_test_account`), `bootstrap.seed_test_accounts()`, endpoint `GET /api/auth/test-accounts`. Аккаунты: `citizen@test.local` / `editor@test.local` / `admin@test.local`, пароль `Test12345!`.
- Header (`components/layout.py:build_desktop_header`): гость → кнопки «Регистрация»+«Войти»; залогинен → `components/user_menu.py` (аватар+имя, anchored dropdown через `page.overlay`): Профиль / Настройки / «Сменить пользователя» (список тест-аккаунтов с email и галкой) / Добавить пользователя / email / Выйти. Admin-кнопка в header только для нужной роли.
- `/settings` — отдельная страница `pages/settings_page.py` (настройки убраны из profile).
- Sticky footer на desktop.
- Login race-fix: `_login_in_progress` флаг (НЕ персистится), loading-state кнопки, backend-only (без local fallback при живом backend).
- Все UI-упоминания «демо» удалены.

**Важные технические факты Flet 0.85 (НЕ повторяй ошибки):**
- НЕТ `ft.alignment.center` — используй `CENTER` из `theme.app_theme`.
- НЕТ `page.open`/`page.close` — используй `components/dialog_util.py` (`open_dialog`/`close_dialog`, fallback на `show_dialog`/`pop_dialog`) или `page.overlay` напрямую.
- Транзиентные флаги в `auth_state` НЕ должны персиститься True (см. `_login_in_progress` баг).

## Что делать СЕЙЧАС (Sprint 2) — по приоритету

Каждый пункт — отдельный коммит. После каждого: `.venv/bin/python -m pytest -q` (98 должны проходить), компиляция `py_compile`, запуск Flet и ручная проверка на desktop. НЕ ломай существующее.

### 1. AI-помощник: intent → раздел (ТЗ §2, §3)
- Новый сервис `src/services/ai_helper.py`:
  - `SYSTEM_PROMPT` (текст из ТЗ §3.2).
  - `SECTION_REGISTRY` — словарь разделов {id, route, title, description, keywords, requires_auth}.
  - `detect_intent(query, role, is_guest) -> IntentResult{section, response_text, requires_auth_warning}`.
  - Локальная keyword/fuzzy логика СЕЙЧАС; архитектурно подготовь метод-заглушку под реальный LLM (`_resolve_via_llm`, пока no-op).
- Переработай `components/ai_chat.py`: на каждое сообщение → `detect_intent` → ответ + **мини-карточка перехода** (новый `components/ai_section_card.py`: название раздела, описание, кнопка «Перейти →» → `go_to(route)`). НЕ текстовая ссылка — оформленная карточка.
- Кнопка AI на главной (ТЗ §2): сейчас в sidebar «Спросить агента». Сделай floating-кнопку (desktop bottom-right, не перекрывая footer; mobile — компактный pill), мягкий hover/press. Гость может спрашивать, но для действий, требующих аккаунт — предупреждение.

### 2. Глобальный поиск: Google-suggestions (ТЗ §6)
- `pages/search_page.py` сейчас submit-фильтр. Добавь dropdown-подсказки во время ввода (8–10 вариантов) из problems/scenarios/documents/laws/institutions + базовый словарь популярных запросов.
- Новый `src/services/search_suggestions.py`: prefix-match + scoring, топ 8–10, архитектурно готов под аналитику частоты.
- Клик по подсказке → подставляет в поле + запускает поиск.

### 3. Фильтры каталога + «Рядом со мной» (ТЗ §13, §14)
- §13: проверь фильтры в `pages/search_page.py` (`_filter_chips`, `_quick_filters`) и `pages/home_page.py` (категории `CATEGORIES[1:7]`). По жалобе — search/topbar-фильтры могут быть некликабельны. Сделай: visual states (selected/hover/disabled), кнопку «Сбросить», mobile bottom-sheet.
- §14: `services/institutions.py` `match_institutions` уже учитывает весь профиль, НО проверь `components/location_picker.py` — не теряются ли адреса (использовать ВСЕ адреса списком, валидировать каждый, union результатов, dedup; ошибки: пустой/не найден/нет рядом).

### 4. Документы (ТЗ §18)
- `pages/documents_page.py` + handlers в `main.py` (~`_collect_document_payload`, `add_document_from_dialog`, дата-поле, file picker):
  - §18.3 Дата: убрать ручной ввод, поставить `ft.DatePicker` (адаптивный, под стиль). Хранить ISO, показывать DD.MM.YYYY.
  - §18.4 File picker: `_pick_document_scan` уже использует `ft.FilePicker` — проверь что реально работает на web/desktop, покажи имя файла. Файлы шифруются (`services/file_crypto.py`).
  - §18.2 Цвет на документ: новое поле `UserDocument.color` (миграция 0007, VARCHAR(7) hex), палитра 12 спокойных цветов (`color_picker` компонент), карточка применяет акцент, читаемость текста, light/dark.
  - §18.1 Кнопка «Отсканировать новый документ»: освежить стиль под тему.

### 5. Локализация RU/EN/BE (ТЗ §17) — БОЛЬШАЯ задача, отдельный sprint-кусок
- Новый пакет `src/services/i18n/` (`__init__.py` с `t(key)`/`set_locale`, `ru.json`/`en.json`/`be.json`).
- Вынести UI-строки («слова сайта»: кнопки/меню/заголовки/ошибки/пустые состояния) в ключи. НЕ переводить пользовательские данные (имена, документы, заметки). Контент БД — заложи структуру `title_ru/en/be` если нужно, без автоперевода.
- Селектор языка на `/settings`. Скрипт `scripts/extract_i18n_keys.py` для полуавтоматического выноса.

### 6. Персонализация плана (ТЗ §10)
- Новый `src/services/personalization.py`: rule-engine {condition: profile.has_children==True → include/exclude/adjust task}. Применять в `_create_situation_from_template` (main.py) после копирования шаблона. Региональные сроки/комментарии/налоги-ЖКХ-привязки.

### 7. Цветовая палитра (ТЗ §19.2) — визуальная, делать ОСТОРОЖНО
- Пересмотреть `app_theme.LIGHT/DARK`: спокойная графит + сине-стальной + мягкий акцент. НЕ хардкодить цвета по проекту — только через `APP_COLORS`. После — QA всех страниц на 3 breakpoint.

### 8. Адаптивность QA (ТЗ §19–20)
- Пройти desktop/tablet/mobile: состояния hover/active/disabled/loading/error, нет наложений/обрезаний, контраст, пустые состояния. Mobile: фильтры через bottom-sheet, mini-chat закрывается.

## Команды запуска / проверки

```bash
docker start belposluga-postgres belposluga-mailhog

# Backend (PostgreSQL + MailHog)
cd src && \
BELPOMOSHNIK_DATABASE_URL="postgresql+psycopg://belposluga:belposluga@127.0.0.1:5432/belpomoshnik" \
BELPOMOSHNIK_SECRET_KEY="belpomoshnik-dev-secret-key-256bit-ok" \
SMTP_HOST=127.0.0.1 SMTP_PORT=1025 SMTP_TLS=false \
../.venv/bin/python -m uvicorn backend.app:app --port 8060 --reload &

# Flet
cd src && ../.venv/bin/python main.py

# Тесты (должны проходить ДО и ПОСЛЕ твоих правок)
.venv/bin/python -m pytest -q                       # 98 passed
BELPOMOSHNIK_DATABASE_URL="postgresql+psycopg://belposluga:belposluga@127.0.0.1:5432/belpomoshnik" \
  .venv/bin/python scripts/integration_client.py    # 23 passed

# Первый запуск БД
BELPOMOSHNIK_DATABASE_URL="postgresql+psycopg://belposluga:belposluga@127.0.0.1:5432/belpomoshnik" \
  PYTHONPATH=src .venv/bin/python -m backend.bootstrap   # схема + роли + тест-аккаунты
```

Тестовые аккаунты: `citizen@test.local` / `editor@test.local` / `admin@test.local`, пароль `Test12345!`.

## Правила
- Не ломай рабочее. Не меняй архитектуру радикально. Не оставляй заглушки где нужна рабочая функция. Не хардкодь цвета/тексты. Не показывай admin-функции не-админу. После каждого блока — pytest + ручная проверка desktop/tablet/mobile.
- Коммиты атомарные, осмысленные. Заканчивай тело PR/коммита строкой `Co-Authored-By` если требуется политикой репо.
