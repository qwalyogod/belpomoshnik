# Журнал изменений

## 2026-06-04 (React/Vite — backend bridge ситуаций и задач)

### Что изменено

- `reactvitemaket/src/app/services/api.ts` — добавлены методы `/api/user/situations` и `/api/user/tasks` для списка, создания, обновления и удаления пользовательских ситуаций/задач.
- `reactvitemaket/src/app/data/types.ts` — пользовательская ситуация получила карту `backendTaskIds`, связывающую задачу сценария с backend-задачей.
- `reactvitemaket/src/app/data/adapters.ts` — добавлен адаптер пользовательской ситуации из backend DTO в React-модель с сопоставлением задач по этапу и названию.
- `reactvitemaket/src/app/data/store.tsx` — ситуации догружаются из backend после JWT-входа; создание ситуации из сценария, отметка задачи и удаление backend-ситуации синхронизируются с API при сохранении локального fallback.
- `docs/PROJECT_STATUS.md`, `docs/REACT_MIGRATION_PLAN.md`, `docs/TASKS.md` — обновлены под фактический статус переноса пользовательских ситуаций и задач.

### Результат проверки

- `.venv/bin/python -m compileall src` — ✅ без ошибок.
- `pnpm build` в `reactvitemaket/` — ✅ без ошибок.
- Backend smoke через `curl --noproxy '*'`: `/api/auth/login` → `/api/user/situations` → `/api/user/tasks/{id}` → delete situation — ✅ создание, отметка задачи и удаление работают.
- Browser check `/situations` на `http://127.0.0.1:8550` — ✅ страница открывается, прогресс задач отображается, console errors нет.

---

## 2026-06-04 (React/Vite — backend bridge личных документов)

### Что изменено

- `reactvitemaket/src/app/services/api.ts` — добавлены методы JWT login/register, profile endpoints и CRUD личных документов `/api/user/documents`.
- `reactvitemaket/src/app/data/adapters.ts` — адаптер личного документа теперь понимает backend-поля `doc_type`, `issued_date`, `expiry_date` и считает статус по сроку действия.
- `reactvitemaket/src/app/data/store.tsx` — добавлен мягкий backend auth bridge для аккаунтов React/Vite; личные документы догружаются из API и синхронизируются при создании, редактировании и удалении backend-документов.
- `docs/PROJECT_STATUS.md`, `docs/REACT_MIGRATION_PLAN.md`, `docs/TASKS.md` — обновлены под фактический статус переноса пользовательских данных к API.

### Результат проверки

- `PYTHONPATH=src .venv/bin/python -m backend.bootstrap` — ✅ тестовые backend-аккаунты созданы/проверены.
- `.venv/bin/python -m compileall src` — ✅ без ошибок.
- `pnpm build` в `reactvitemaket/` — ✅ без ошибок.
- Backend smoke `/api/auth/login` + `/api/user/documents` — ✅ JWT вход и создание/list документа работают.
- Browser check `/documents` под тестовым гражданином — ✅ документ из backend отображается в React-интерфейсе.

---

## 2026-06-04 (React/Vite — пользовательское состояние по аккаунтам)

### Что изменено

- `reactvitemaket/src/app/data/store.tsx` — добавлено локальное per-user хранение ситуаций, документов, избранного, уведомлений, профиля и настроек.
- `reactvitemaket/src/app/data/store.tsx` — гостевой режим получает пустую личную область; мутации личных данных для гостя заблокированы на уровне store.
- `reactvitemaket/src/app/components/extra-screens.tsx` — создание ситуации из сценария теперь безопасно обрабатывает отказ protected action; форма документа синхронизирует поля при открытии/смене документа.
- `docs/PROJECT_STATUS.md`, `docs/REACT_MIGRATION_PLAN.md`, `docs/TASKS.md` — обновлены под фактический статус переноса пользовательских данных.

### Результат проверки

- `.venv/bin/python -m compileall src` — ✅ без ошибок.
- `pnpm build` в `reactvitemaket/` — ✅ без ошибок.
- Browser check `/documents` под гражданином — ✅ добавленный документ сохраняется после перезагрузки страницы.
- Browser check `/documents` под гостем — ✅ личные документы не наследуются, добавление документа открывает окно входа/регистрации.

---

## 2026-06-04 (React/Vite — роли, гость и protected actions)

### Что изменено

- `reactvitemaket/src/app/data/types.ts` — добавлена модель локального пользователя `AppUser`.
- `reactvitemaket/src/app/data/store.tsx` — добавлены текущий пользователь, гостевой режим, быстрые аккаунты, локальная регистрация, вход по email/паролю, выход в гостевой режим и сброс быстрого списка.
- `reactvitemaket/src/app/App.tsx` — добавлен desktop dropdown быстрого входа, корректный показ роли пользователя, условная ссылка на админ-панель и protected guard для desktop/mobile.
- `reactvitemaket/src/app/pages.tsx` — страницы входа и регистрации переведены на локальную auth-логику; кнопка добавления документа подключена к общему защищённому действию.
- `reactvitemaket/src/app/components/extra-screens.tsx` — окно гостевого ограничения теперь ведёт на вход или регистрацию.
- `reactvitemaket/src/app/routes.tsx` — детальная страница сценария защищена от отсутствующего guard-контекста.
- `docs/PROJECT_STATUS.md`, `docs/REACT_MIGRATION_PLAN.md`, `docs/TASKS.md` — обновлены под фактический статус миграции.

### Результат проверки

- `.venv/bin/python -m compileall src` — ✅ без ошибок.
- `pnpm build` в `reactvitemaket/` — ✅ без ошибок.
- Browser check `http://127.0.0.1:8560/` — ✅ приложение открывается.
- Browser check быстрого входа — ✅ видны тестовые роли и выход в гостевой режим.
- Browser check `/admin` — ✅ после выбора администратора админ-панель доступна.
- Browser check `/documents` в гостевом режиме — ✅ protected action открывает окно входа/регистрации.
- Browser check `/login` — ✅ вход тестовым гражданином проходит с первого клика.

---

## 2026-06-04 (React/Vite — счётчики сценариев из backend API)

### Что изменено

- `src/backend/schemas.py` — `ScenarioPublicSummary` расширен полями `stage_count` и `task_count`.
- `src/backend/service.py` — публичные списки сценариев загружают этапы и шаги через `selectinload`, чтобы summary-счётчики считались без дополнительных запросов из UI.
- `src/backend/api/public.py` — summary-сценарии теперь отдают категорию, количество этапов и количество задач.
- `reactvitemaket/src/app/data/types.ts` — модель `Scenario` получила поля `stageCount` и `taskCount`.
- `reactvitemaket/src/app/data/adapters.ts` — adapter переносит `stage_count` / `task_count` из backend DTO во frontend-модель.
- `reactvitemaket/src/app/data/store.tsx` — защищённые старые mock-id сохраняются для локальных ситуаций, но scalar-поля API теперь всё равно обновляют карточку.
- `reactvitemaket/src/app/pages.tsx` — каталог сценариев показывает количество задач из API, если оно доступно.
- `docs/PROJECT_STATUS.md`, `docs/REACT_MIGRATION_PLAN.md`, `docs/TASKS.md` — обновлены под фактический статус миграции.

### Результат проверки

- Backend TestClient: `/api/scenarios` — ✅ `rozhdenie-rebenka` отдаёт `stage_count: 6`, `task_count: 7`.
- `.venv/bin/python -m compileall src` — ✅ без ошибок.
- `pnpm build` в `reactvitemaket/` — ✅ без ошибок.
- Browser check `http://127.0.0.1:8560/scenarios` — ✅ «Рождение ребёнка» отображается один раз, показывает backend-срок и `Задач: 7`.

---

## 2026-06-04 (React/Vite — API-first публичный контент)

### Что изменено

- `reactvitemaket/src/app/data/store.tsx` — добавлена нормализация публичного контента по названию и категории, чтобы одноимённые mock/backend карточки не дублировались.
- `reactvitemaket/src/app/data/store.tsx` — добавлена стратегия `API-first`: backend-элементы получают приоритет, mock остаётся fallback.
- `reactvitemaket/src/app/data/store.tsx` — добавлено сохранение богатых mock-массивов для preview, если backend summary DTO пока не отдаёт этапы, документы, учреждения или источники.
- `reactvitemaket/src/app/data/store.tsx` — избранные сценарии переназначаются со старого mock-id на backend-id при совпадении публичной карточки.
- `docs/PROJECT_STATUS.md`, `docs/REACT_MIGRATION_PLAN.md`, `docs/TASKS.md`, `docs/DECISIONS.md` — обновлены под новую политику источников данных.

### Результат проверки

- `.venv/bin/python -m compileall src` — ✅ без ошибок.
- `pnpm build` в `reactvitemaket/` — ✅ без ошибок.
- Browser check `http://127.0.0.1:8560/scenarios` — ✅ «Рождение ребёнка» отображается один раз, использует backend-срок и не показывает `Задач: 0`.
- Browser check `http://127.0.0.1:8560/situations` — ✅ локальные ситуации «Потеря паспорта» и «Открытие ИП» не потерялись.
- Browser check `http://127.0.0.1:8560/scenarios/rozhdenie-rebenka` — ✅ полный backend-сценарий догружается с этапами, задачами и источниками; console errors нет.

---

## 2026-06-04 (React/Vite — документы, учреждения и закон-апдейты из API)

### Что изменено

- `src/backend/seeds/mvp_childbirth.py` — seed-закон-апдейт переведён в статус `applied`, чтобы он попадал в публичный endpoint `/api/law-updates`.
- `reactvitemaket/src/app/services/api.ts` — добавлен метод `getLawUpdates`.
- `reactvitemaket/src/app/data/adapters.ts` — экспортированы адаптеры справочных документов и учреждений; закон-апдейт теперь определяет категорию по тексту, если отдельное поле категории отсутствует.
- `reactvitemaket/src/app/data/store.tsx` — подключена загрузка `/api/documents`, `/api/authorities`, `/api/law-updates` с сохранением mock fallback.
- `reactvitemaket/src/app/components/extra-screens.tsx` — глобальный поиск теперь ищет по справочным документам и учреждениям, пришедшим из backend API.
- `docs/PROJECT_STATUS.md`, `docs/REACT_MIGRATION_PLAN.md`, `docs/TASKS.md` — обновлены под фактический статус миграции.

### Результат проверки

- `PYTHONPATH=src .venv/bin/python -m backend.scripts.seed_db` — ✅ seed применён.
- Backend TestClient: `/api/documents`, `/api/authorities`, `/api/law-updates` — ✅ 200 OK.
- `.venv/bin/python -m compileall src` — ✅ без ошибок.
- `pnpm build` в `reactvitemaket/` — ✅ без ошибок.
- Browser check `http://127.0.0.1:8560/legal` — ✅ backend закон-апдейт отображается, console errors нет.
- Browser check глобального поиска — ✅ запросы `ЗАГС` и `Заявление` находят учреждение и документ из backend API.

---

## 2026-06-03 (React/Vite — публичный API content bridge)

### Что изменено

- `src/backend/api/public.py` — добавлен публичный endpoint `GET /api/scenarios`.
- `src/backend/service.py` — добавлена выборка опубликованных сценариев и категория в полной схеме сценария.
- `src/backend/schemas.py` — добавлены поля `category` для summary/full DTO сценария.
- `src/backend/app.py` — добавлен CORS для локальных React/Flet dev-серверов.
- `reactvitemaket/src/app/data/store.tsx` — подключена загрузка `/api/problems`, `/api/scenarios` и lazy-загрузка `/api/scenarios/{slug}` с mock fallback.
- `reactvitemaket/src/app/data/adapters.ts` — расширен адаптер backend DTO для сценариев, этапов, шагов, документов, учреждений, источников и зависимостей.
- `reactvitemaket/.env.example` — добавлен пример `VITE_API_BASE_URL`.
- `docs/PROJECT_STATUS.md`, `docs/REACT_MIGRATION_PLAN.md`, `docs/TASKS.md` — обновлены под фактический статус миграции.

### Результат проверки

- `PYTHONPATH=src .venv/bin/python -m backend.scripts.migrate` — ✅ применены миграции `0003`-`0006`.
- `PYTHONPATH=src .venv/bin/python -m backend.scripts.seed_db` — ✅ добавлены MVP-данные сценария «Рождение ребёнка».
- `.venv/bin/python -m compileall src` — ✅ без ошибок.
- `pnpm build` в `reactvitemaket/` — ✅ без ошибок.
- Backend TestClient: `/api/problems`, `/api/scenarios`, `/api/scenarios/rozhdenie-rebenka` — ✅ 200 OK.
- Browser check `http://127.0.0.1:8560/scenarios` → `/scenarios/rozhdenie-rebenka` — ✅ full detail подгрузил этапы, задачу и источники; console errors нет.

---

## 2026-06-03 (React/Vite — маршруты и API-слой)

### Что изменено

- `reactvitemaket/src/app/routes.tsx` — добавлены маршруты `/scenarios` и `/admin`; для `/admin` добавлен role guard с отказом доступа для не-администратора.
- `reactvitemaket/src/app/pages.tsx` — приведены ключевые поля категорий, документов, уведомлений и закон-апдейтов к текущей модели `types.ts`.
- `reactvitemaket/src/app/services/api.ts` — создан начальный API-клиент для публичных endpoints backend.
- `reactvitemaket/src/app/data/adapters.ts` — создан слой адаптеров между backend DTO и frontend-моделью React-приложения.
- `docs/REACT_MIGRATION_PLAN.md`, `docs/TASKS.md`, `docs/PROJECT_STATUS.md` — обновлены под фактический статус миграции.

### Результат проверки

- `pnpm build` в `reactvitemaket/` — ✅ без ошибок.
- React/Vite dev-сервер `http://127.0.0.1:8560/` — ✅ открыт во встроенном браузере.
- Проверены маршруты `/`, `/scenarios`, `/admin` — ✅ без console error; `/admin` показывает ограничение доступа для гостя.

---

## 2026-06-03 (старт React/Vite migration)

### Что изменено

- `docs/REACT_MIGRATION_AUDIT.md` — создан аудит React/Vite-макета: структура, сильные стороны, проблемы типов/маршрутов, риски и рекомендации.
- `docs/REACT_MIGRATION_PLAN.md` — создан поэтапный план переноса UI на Vite/React/TypeScript с сохранением Flet baseline до parity.
- `reactvitemaket/package.json` — удалены неиспользуемые зависимости Radix/MUI/Recharts/DnD и оставлен минимальный набор для текущего reachable React bundle.
- `reactvitemaket/pnpm-lock.yaml` — создан lock-файл зависимостей.
- `.gitignore` — добавлены `node_modules/` и `**/node_modules/`.
- `AGENTS.md` — добавлено правило читать migration-документы перед задачами по React/Vite.
- `docs/TASKS.md` — добавлен этап 21 «Переход на React/Vite frontend».
- `docs/DECISIONS.md` — зафиксировано архитектурное решение о постепенной миграции UI.
- `docs/PROJECT_STATUS.md` — зафиксирован новый текущий курс UI.

### Результат проверки

- Markdown-документы созданы.
- `pnpm install` в `reactvitemaket/` — ✅ выполнено после сокращения зависимостей.
- `pnpm build` в `reactvitemaket/` — ✅ без ошибок.
- React/Vite dev-сервер `http://127.0.0.1:8560/` — ✅ главная страница открылась во встроенном браузере.
- Flet/Python-код приложения не изменялся.

---

## 2026-06-03 (Sprint 2 — документы)

### Что изменено

- `src/theme/app_theme.py` — добавлена токенизированная палитра из 12 спокойных цветов для карточек документов.
- `src/pages/documents_page.py` — большая карточка документа теперь использует выбранный цвет; список документов и selected-state подстраиваются под цвет документа.
- `src/pages/documents_page.py` — добавлены явные действия для выбранного документа: открыть скан, редактировать, удалить.
- `src/pages/documents_page.py` — текст про защиту документов приведён к фактической локальной модели хранения без обещания биометрии.
- `src/main.py` — форма добавления/редактирования документа получила календарный выбор даты выдачи и срока действия вместо ручного ввода.
- `src/main.py` — добавлен выбор цвета карточки документа и сохранение цвета в локальное состояние.
- `src/main.py` — импортированный PDF получает цвет документа по умолчанию.
- `docs/PROJECT_STATUS.md`, `docs/TASKS.md` — обновлён статус Sprint 2.

### Результат проверки

- `.venv/bin/python -m compileall src` — ✅ без ошибок.
- `PYTHONPATH=src .venv/bin/python` со сборкой `build_documents_page(...)` для desktop/mobile — ✅ без ошибок.
- `.venv/bin/python -m pytest -q` — ✅ 98 passed.
- `.venv/bin/flet run -w src/main.py --host 127.0.0.1 -p 8550` — ✅ web-сервер запущен.
- В web-версии `/documents` проверены пустое состояние, открытие диалога добавления документа и календарь без ручного режима ввода — ✅ без traceback.

---

## 2026-06-03 (Sprint 2 — фильтры поиска и «Рядом со мной»)

### Что изменено

- `src/services/institutions.py` — подбор учреждений теперь учитывает все адреса профиля, выбирает лучшее совпадение и дедуплицирует результаты.
- `src/pages/search_page.py` — добавлен отдельный фильтр «Рядом», рабочий быстрый фильтр «Рядом со мной», активные состояния фильтров и кнопка сброса.
- `src/pages/search_page.py` — исправлен серый web-плейсхолдер пустого блока поиска: пустые контролы больше не добавляются в layout.
- `src/main.py` — глобальный поиск получает профиль пользователя и общий обработчик сброса запроса/фильтра.
- `docs/PROJECT_STATUS.md`, `docs/TASKS.md` — обновлён статус Sprint 2.

### Результат проверки

- `.venv/bin/python -m compileall src` — ✅ без ошибок.
- `.venv/bin/python -m pytest -q` — ✅ 98 passed.
- `PYTHONPATH=src .venv/bin/python` с проверкой `match_nearby_institutions(...)` и сборкой `build_search_page(...)` — ✅ без ошибок.
- `.venv/bin/flet run -w src/main.py --host 127.0.0.1 -p 8550` — ✅ web-сервер запущен.
- В web-версии `/search` проверены пустой поиск, фильтр «Рядом» и список учреждений рядом — ✅ без traceback и серого плейсхолдера.

---

## 2026-06-03 (Sprint 2 — гостевой режим и быстрый вход)

### Что изменено

- `src/components/user_menu.py` — выпадающее меню пользователя теперь содержит гостевой вход, быстрый вход по ролям, добавление пользователя, выход в гостевой режим и выход со всех аккаунтов.
- `src/components/layout.py` — desktop-header показывает меню гостя и передаёт callbacks для настроек, входа, добавления пользователя и очистки быстрых аккаунтов.
- `src/main.py` — добавлены локальные тестовые аккаунты ролей, `quick_accounts`, режим добавления пользователя через `/register`, гостевой выход, очистка добавленных быстрых пользователей и быстрый выбор локально добавленного аккаунта.
- `src/data/mock_data.py` — убраны пользовательские формулировки, обозначающие сценарии и аудит как демонстрационные.
- `docs/PROJECT_STATUS.md`, `docs/TASKS.md` — зафиксирован новый сценарий показа: гость → роли → добавленный пользователь → выход.

### Результат проверки

- `.venv/bin/python -m compileall src` — ✅ без ошибок.
- `PYTHONPATH=src .venv/bin/python` со сборкой `build_desktop_header(...)` для гостя, гражданина и администратора — ✅ без ошибок.
- `curl -I http://127.0.0.1:8550/`, `/settings`, `/register`, `/admin` — ✅ `HTTP/1.1 200 OK`.

---

## 2026-06-03 (Sprint 2 — ИИ-помощник с переходами)

### Что изменено

- `src/services/ai_helper.py` — добавлен локальный intent-router встроенного ИИ-помощника с картой реальных разделов приложения.
- `src/components/ai_section_card.py` — добавлена компактная карточка-переход к рекомендованному разделу.
- `src/components/ai_chat.py` — мини-чат теперь отвечает по намерению пользователя и показывает карточку раздела под ответом.
- `src/main.py` — ИИ-помощник подключён к текущей роли, гостевому режиму и маршрутизации; на desktop-версии главной добавлена плавающая кнопка.
- `src/components/sidebar.py` — подпись кнопки помощника стала нейтральной и не обещает круглосуточный сервис.
- `src/services/search_suggestions.py` — добавлен локальный сервис подсказок глобального поиска.
- `src/pages/search_page.py` — поле глобального поиска теперь показывает кликабельные подсказки во время ввода.
- `docs/PROJECT_STATUS.md`, `docs/TASKS.md` — зафиксировано начало Sprint 2 и следующие задачи.

### Результат проверки

- `.venv/bin/python -m compileall src` — ✅ без ошибок.
- `PYTHONPATH=src .venv/bin/python` со сборкой AI-controls, карточки перехода и search-controls — ✅ без ошибок.
- `.venv/bin/flet run -w src/main.py --host 127.0.0.1 -p 8550` — ✅ web-сервер запущен.
- `curl -I http://127.0.0.1:8550/` и `curl -I http://127.0.0.1:8550/search` — ✅ `HTTP/1.1 200 OK`.

---

## 2026-06-02 (Админ-панель — связи закон-апдейтов с проблемами)

### Что изменено

- `src/pages/admin_page.py` — форма создания закон-апдейта получила поле «Связанные проблемы».
- `src/pages/admin_page.py` — список закон-апдейтов теперь показывает связанные проблемы рядом со связанными сценариями.
- `src/main.py` — создание закон-апдейта сохраняет `related_problems` в локальное состояние и нормализует ID без дублей.
- `docs/PROJECT_STATUS.md`, `docs/TASKS.md` — обновлён статус админ-панели и этапа закон-апдейтов.

### Результат проверки

- `.venv/bin/python -m compileall src` — ✅ без ошибок.

---

## 2026-06-02 (Главная — ЖКХ и налоги)

### Что изменено

- `src/services/dashboard.py` — дашборд теперь собирает ближайшие и просроченные события из локальных ЖКХ-платежей и налоговых обязательств.
- `src/pages/home_page.py` — добавлена карточка «ЖКХ и налоги» с просроченными и ближайшими сроками, суммой и быстрыми переходами в трекеры.
- `src/pages/home_page.py` — быстрые действия и статистика на главной теперь учитывают ЖКХ/налоги.
- `src/main.py` — главная страница получает `utility_payments`, `tax_obligations` и пользовательские сроки напоминаний.
- `docs/PROJECT_STATUS.md`, `docs/TASKS.md` — обновлён статус работ по приоритету 1 ТЗ.

### Результат проверки

- `.venv/bin/python -m compileall src` — ✅ без ошибок.
- `PYTHONPATH=src .venv/bin/python` со сборкой `build_dashboard_data(...)` и `build_home_page(...)` — ✅ без ошибок.
- `.venv/bin/flet run -w src/main.py --host 127.0.0.1 -p 8550` — ✅ web-сервер запущен, `/`, `/utility`, `/taxes` отвечают `200`.

---

## 2026-06-02 (Приоритет 1 ТЗ — настройки напоминаний)

### Что изменено

- `src/main.py` — локальное состояние расширено отдельными настройками напоминаний для задач, документов, ЖКХ, налогов и закон-апдейтов.
- `src/main.py` — генератор уведомлений теперь учитывает пользовательские переключатели и отдельные сроки напоминаний вместо одного общего правила.
- `src/pages/profile_page.py` — добавлена карточка «Напоминания» с настройками каналов и горизонтов уведомлений.
- `src/theme/app_theme.py` — настройки `Крупный шрифт` и `Высокий контраст` начали применяться на уровне темы Flet.
- `docs/PROJECT_STATUS.md`, `docs/TASKS.md` — обновлён статус реализации по приоритету 1 после отчёта по ТЗ.

### Результат проверки

- `.venv/bin/python -m compileall src` — ✅ без ошибок.
- `PYTHONPATH=src .venv/bin/python` с импортом `build_profile_page(...)` — ✅ новая карточка профиля собирается.
- `.venv/bin/flet run -w src/main.py --host 127.0.0.1 -p 8550` — ✅ web-сервер запущен без traceback.

---

## 2026-06-02 (Отчёт по ТЗ с пользовательской перспективой)

### Что изменено

- `docs/TZ_USER_ORIENTED_PROJECT_REPORT.md` — создан подробный отчёт о соответствии проекта ТЗ с позиции разработчика и пользователя приложения.
- В отчёте учтены требования из `ТЗ Абрамович.docx`, текущая структура Flet/Python-приложения, локальное хранение, сценарии, документы, уведомления, профиль, обучение, ЖКХ/налоги, закон-апдейты и админ-панель.
- Отдельно зафиксировано, что реализовано полностью, что сделано частично и какие production-функции остаются на следующие этапы.

### Результат проверки

- Markdown-файл создан.
- Код приложения не изменялся.

---

## 2026-06-02 (UI polish — документы и профиль)

### Что изменено

- `src/components/layout.py` — выровнен desktop-блок профиля в верхней навигации.
- `src/pages/documents_page.py` — упрощена большая карточка документа: убраны лишние декоративные круги, использован градиентный токен темы, выровнены action-кнопки.
- `src/pages/profile_page.py` — пустой блок «Избранные сценарии» приведён к единому размеру и стилю профильных карточек.
- `src/main.py` — форма добавления/редактирования личного документа разбита на аккуратные секции; кнопки диалогов приведены к единому стилю.
- `src/main.py` — добавлен рабочий экспорт PDF-отчёта документов в `data/exports` и импорт PDF как личного документа через локальное хранилище.
- `.gitignore` — добавлена папка `data/exports/`.

### Результат проверки

- `.venv/bin/python -m compileall src` — ✅ без ошибок.
- Web-сервер `http://127.0.0.1:8550/` — ✅ отвечает `200 OK`.

---

## 2026-06-01 (Диплом — структура пояснительной записки)

### Что изменено

- `docs/DIPLOMA_STRUCTURE_PLAN.md` — создан отдельный план структуры дипломного проекта по методическим указаниям.
- Зафиксированы ориентировочные страницы разделов, состав пояснительной записки, требования к оформлению, графическая часть и состав электронного проекта.
- Добавлено примечание, что `documents/~$тодические указания ДП наше.doc` является временным lock-файлом Word, а рабочий источник — `documents/Методические указания ДП наше.doc`.

### Результат проверки

- Markdown-файл создан.
- Код приложения не изменялся.

---

## 2026-05-26 (Redesign — Шаг 14: Закон-апдейты)

### Что изменено

- `src/pages/legal_updates_page.py` — экран «Закон-апдейты» перестроен под новый визуал: PageHeader, SearchBox, FilterChips, сортировка «Новые / По приоритету», StatsRow и лента карточек.
- `src/pages/legal_updates_page.py` — добавлены карточки законапдейтов с иконкой категории, бейджами категории/приоритета/новизны, мета-информацией, срочной красной обводкой и действием «Подробнее».
- `src/pages/legal_updates_page.py` — desktop получил правую колонку «Для меня», фильтры и подсказку «Как читать апдейт»; mobile получил компактный layout шириной 343 px.
- `src/main.py` — добавлено локальное состояние сортировки закон-апдейтов без изменения данных и маршрутов.
- `docs/redesign-progress/14-*.png` — сохранены скриншоты в light/dark, desktop/mobile.
- `PLAN-REDESIGN.md`, `claude/PLAN.md` — отмечен завершённый шаг 14.

### Результат проверки

- `.venv/bin/python -m compileall src` — ✅ без ошибок.
- `.venv/bin/flet run -w src/main.py --host 127.0.0.1 -p 8550` — ✅ запущен и проверен в light/dark, desktop/mobile.

---

## 2026-05-26 (Redesign — Шаг 13: Уведомления)

### Что изменено

- `src/pages/notifications_page.py` — экран «Уведомления» перестроен под новый визуал: PageHeader, SearchBox, FilterChips, StatsRow, группировка «Сегодня / На этой неделе / Раньше» и карточки с типом события.
- `src/pages/notifications_page.py` — добавлены визуальные состояния непрочитанных и срочных уведомлений, кнопка действия «Перейти», read-action без изменения существующих callback-ов.
- `src/pages/notifications_page.py` — desktop получил правую колонку с типами уведомлений, быстрыми действиями и настройками; mobile получил компактный layout шириной 343 px без горизонтального overflow.
- `docs/redesign-progress/13-*.png` — сохранены скриншоты в light/dark, desktop/mobile.
- `PLAN-REDESIGN.md`, `claude/PLAN.md` — отмечен завершённый шаг 13.

### Результат проверки

- `.venv/bin/python -m compileall src` — ✅ без ошибок.
- `.venv/bin/flet run -w src/main.py --host 127.0.0.1 -p 8550` — ✅ запущен и проверен в light/dark, desktop/mobile.

---

## 2026-05-26 (Redesign — Шаг 12: Профиль)

### Что изменено

- `src/pages/profile_page.py` — экран «Профиль» перестроен под новый визуал: hero-карточка пользователя, StatsRow, карточки личных данных, интересов, персонализации, настроек, достижений и разделов профиля.
- `src/pages/profile_page.py` — добавлены compact mobile-layout шириной 343 px, аккуратные status chips, избранные сценарии, достижения, журнал активности и стабильные action-кнопки без горизонтального overflow.
- `src/main.py`, `src/data/mock_data.py` — добавлено сохранение и демо-значение даты рождения пользователя.
- `src/theme/app_theme.py` — добавлен токен `on_accent` для текста на акцентных элементах.
- `docs/redesign-progress/12-*.png` — сохранены скриншоты в light/dark, desktop/mobile.
- `PLAN-REDESIGN.md`, `claude/PLAN.md` — отмечен завершённый шаг 12.

### Результат проверки

- `.venv/bin/python -m compileall src` — ✅ без ошибок.
- `.venv/bin/flet run -w src/main.py --host 127.0.0.1 -p 8550` — ✅ запущен и проверен в light/dark, desktop/mobile.

---

## 2026-05-26 (Redesign — Шаг 11: Документы)

### Что изменено

- `src/pages/documents_page.py` — экран «Документы» перестроен под новый визуал: PageHeader, SearchBox, FilterChips, StatsRow и CTA «Добавить документ».
- `src/pages/documents_page.py` — добавлены карточки личных документов со скан-плейсхолдером, маскированным номером, статусом срока, датой выдачи, сроком действия, организацией и действиями редактирования/удаления.
- `src/pages/documents_page.py` — добавлены desktop-блоки «Защита данных», предупреждение перед просмотром скана и форма документа без изменения callback-логики.
- `src/pages/documents_page.py` — mobile получил компактные статистические карточки и отдельный layout шириной 340 px без горизонтального overflow.
- `docs/redesign-progress/11-*.png` — сохранены скриншоты в light/dark, desktop/mobile.
- `PLAN-REDESIGN.md`, `claude/PLAN.md` — отмечен завершённый шаг 11.

### Результат проверки

- `.venv/bin/python -m compileall src` — ✅ без ошибок.
- `.venv/bin/flet run -w src/main.py --host 127.0.0.1 -p 8550` — ✅ запущен и проверен в light/dark, desktop/mobile.

---

## 2026-05-26 (Redesign — Шаг 10: Детальная страница ситуации)

### Что изменено

- `src/pages/situation_detail_page.py` — детальная страница ситуации перестроена под новый визуал: breadcrumb, hero-карточка, статусные бейджи, общий прогресс, действия ситуации и карточка следующего шага.
- `src/pages/situation_detail_page.py` — добавлены StatsRow, фильтры задач, группировка задач по этапам, визуальные состояния выполнено/доступно/заблокировано/просрочено и блокировки зависимых шагов.
- `src/pages/situation_detail_page.py` — desktop получил правую колонку со сводкой, ближайшими сроками, документами, учреждениями и быстрыми действиями.
- `src/pages/situation_detail_page.py` — mobile получил отдельный компактный layout шириной 340 px без горизонтального overflow.
- `docs/redesign-progress/10-*.png` — сохранены скриншоты в light/dark, desktop/mobile.
- `PLAN-REDESIGN.md`, `claude/PLAN.md` — отмечен завершённый шаг 10.

### Результат проверки

- `.venv/bin/python -m compileall src` — ✅ без ошибок.
- `.venv/bin/flet run -w src/main.py --host 127.0.0.1 -p 8550` — ✅ запущен и проверен в light/dark, desktop/mobile.

---

## 2026-05-25 (Redesign — Шаг 09: Мои ситуации)

### Что изменено

- `src/pages/situations_page.py` — экран «Мои ситуации» перестроен под новый визуал: PageHeader, поисковая строка, фильтры, StatsRow и карточки ситуаций с категорией, статусом, текущим этапом, сроком и прогрессом.
- `src/pages/situations_page.py` — добавлена визуальная обработка просроченных ситуаций и фильтр «Просрочено» без изменения бизнес-логики хранения.
- `src/pages/situations_page.py` — desktop получил правую колонку с ближайшими задачами, документами к подготовке и подсказкой.
- `src/pages/situations_page.py` — mobile получил отдельный компактный layout с CTA, фильтрами, статистикой, карточками ситуаций, ближайшими задачами и документами.
- `docs/redesign-progress/09-*.png` — сохранены скриншоты в light/dark, desktop/mobile.
- `PLAN-REDESIGN.md`, `claude/PLAN.md` — отмечен завершённый шаг 09.

### Результат проверки

- `.venv/bin/python -m compileall src` — ✅ без ошибок.
- `.venv/bin/flet run -w src/main.py --host 127.0.0.1 -p 8550` — ✅ запущен и проверен в light/dark, desktop/mobile.

---

## 2026-05-25 (Redesign — Шаг 08: Детальная страница сценария)

### Что изменено

- `src/pages/scenario_detail_page.py` — детальная страница сценария перестроена под новый визуал: breadcrumb, hero с PhotoPlaceholder, бейджи категории/сложности/срока и CTA «Создать мою ситуацию».
- `src/pages/scenario_detail_page.py` — добавлены StatsRow, вертикальный timeline этапов с задачами, документами, сроками, учреждениями и зависимостями.
- `src/pages/scenario_detail_page.py` — desktop получил правую helper-колонку со сводкой сценария, документами, учреждениями и связанными сценариями.
- `src/pages/scenario_detail_page.py` — mobile получил отдельный компактный layout шириной 340 px с теми же смысловыми блоками.
- `docs/redesign-progress/08-*.png` — сохранены скриншоты в light/dark, desktop/mobile.
- `PLAN-REDESIGN.md`, `claude/PLAN.md` — отмечен завершённый шаг 08.

### Результат проверки

- `.venv/bin/python -m compileall src` — ✅ без ошибок.
- `.venv/bin/flet run -w src/main.py --host 127.0.0.1 -p 8550` — ✅ запущен и проверен в light/dark, desktop/mobile.

---

## 2026-05-25 (Redesign — Шаг 07: Жизненные сценарии)

### Что изменено

- `src/pages/scenario_templates_page.py` — каталог жизненных сценариев перестроен под новый визуал: PageHeader, SearchBox, чипы категорий, PhotoPlaceholder-карточки сценариев, мета этапов/шагов/срока/сложности и избранное.
- `src/pages/scenario_templates_page.py` — desktop получил правую колонку с быстрым стартом, популярными сценариями и блоком «Что будет внутри».
- `src/pages/scenario_templates_page.py` — mobile получил отдельный компактный layout шириной 340 px и горизонтальные фильтры.
- `docs/redesign-progress/07-*.png` — сохранены скриншоты в light/dark, desktop/mobile.
- `PLAN-REDESIGN.md`, `claude/PLAN.md` — отмечен завершённый шаг 07.

### Результат проверки

- `.venv/bin/python -m compileall src` — ✅ без ошибок.
- `.venv/bin/flet run -w src/main.py --host 127.0.0.1 -p 8550` — ✅ запущен и проверен в light/dark, desktop/mobile.

---

## 2026-05-25 (Redesign — Шаг 06: Карточка проблемы)

### Что изменено

- `src/pages/problem_detail_page.py` — карточка проблемы перестроена под новый визуал: breadcrumb, бейджи, hero-блок, срочные действия, интерактивный пошаговый план, документы с PhotoPlaceholder, сроки/стоимость, контакты, ошибки и официальные источники.
- `src/pages/problem_detail_page.py` — desktop получил правую колонку с содержанием, кратким планом, документами, контактами и связанными проблемами.
- `src/pages/problem_detail_page.py` — mobile получил отдельный компактный layout шириной 340 px без горизонтального overflow.
- `docs/redesign-progress/06-*.png` — сохранены скриншоты карточки проблемы в light/dark, desktop/mobile.
- `PLAN-REDESIGN.md`, `claude/PLAN.md` — отмечен завершённый шаг 06.

### Результат проверки

- `.venv/bin/python -m compileall src` — ✅ без ошибок.
- `.venv/bin/flet run -w src/main.py --host 127.0.0.1 -p 8550` — ✅ запущен и проверен в light/dark, desktop/mobile.

---

## 2026-05-25 (Redesign — Шаг 05: Каталог проблем)

### Что изменено

- `src/pages/problems_page.py` — каталог проблем перестроен под новый визуал: PageHeader, SearchBox, чипы категорий, быстрые категории, карточки проблем с бейджами, сроком и сложностью.
- `src/pages/problems_page.py` — для desktop добавлена правая колонка с фильтрами каталога, популярными проблемами, недавно решёнными проблемами и составом карточки.
- `src/main.py` — `/problems` в нижней навигации теперь подсвечивает пункт «Поиск», как в редизайн-макете.
- `src/main.py` — точечная compatibility-правка `padding_symmetric` вместо устаревшего `ft.padding.symmetric`, чтобы web-preview запускался на Flet 0.85.
- `docs/redesign-progress/05-*.png` — сохранены скриншоты каталога проблем в light/dark, desktop/mobile.
- `PLAN-REDESIGN.md`, `claude/PLAN.md` — отмечен завершённый шаг 05.

### Результат проверки

- `.venv/bin/python -m compileall src` — ✅ без ошибок.
- `.venv/bin/flet run -w src/main.py --host 127.0.0.1 -p 8550` — ✅ запущен и проверен в light/dark, desktop/mobile.

---

## 2026-05-25 (Workspace-редактор контента — Фаза 1)

### Что добавлено

- `src/pages/admin_workspace_page.py` — новый рабочий интерфейс контент-редактора в стиле VS Code: двухпанельный layout, дерево всего контента в правой sidebar, основная область редактирования слева.
- Маршрут `/admin/workspace` (параллельно со старой `/admin`, которая остаётся как fallback).
- `admin_workspace_state` в `main.py` — состояние выбранного элемента, раскрытых разделов/сценариев/этапов.
- Хендлеры `admin_workspace_select`, `admin_workspace_toggle_section/scenario/stage`, `admin_workspace_save`, `admin_workspace_open_legacy`, `admin_workspace_back_to_tree`.
- Баннер на старой `/admin` с кнопкой «Открыть workspace» для перехода к новому редактору.
- Mobile-режим: master-detail с кнопкой «К дереву контента» назад к sidebar.

### Что меняется

- Phase 1 — только каркас и навигация по дереву (просмотр выбранного элемента в режиме preview).
- Inline-редактирование сценариев/этапов/шагов и остальных типов запланировано на Фазы 2–3.
- Старые модальные диалоги редактирования (`admin_edit_scenario`, `admin_edit_stage`, `admin_edit_step` и т.д.) пока работают параллельно — они будут заменены на inline-формы в Фазе 2.

### Известные ограничения

- Раскрыть можно только один сценарий за раз (детали грузятся по одному, ограничение backend `get_admin_scenario`).
- Кнопка «Сохранить» в topbar пока возвращает заглушку — реальная логика появится в Фазе 2.
- Поиск в sidebar — поле есть, фильтрация будет в Фазе 4.

---

## 2026-05-24 (Этап K: Дипломная документация)

### Что добавлено

- `docs/diploma/README.md` — индекс документации K1–K12.
- `docs/diploma/K1_postanovka_zadachi.md` — постановка задачи, цели, аудитория, границы.
- `docs/diploma/K2_predmetnaya_oblast.md` — предметная область, понятия, нормативная база, роли.
- `docs/diploma/K3_arxitektura.md` — архитектура системы, стек, структура кода, паттерны, безопасность.
- `docs/diploma/K4_model_dannykh.md` — ER-диаграмма, все 20+ таблиц с полями, индексы, локальный стейт.
- `docs/diploma/K5_polzovatelskie_scenarii.md` — 22 экрана, 7 UX-flows, навигация, персонализация, контентный каталог.
- `docs/diploma/K6_admin_panel.md` — все функции CMS (A1–A12), ролевая модель, API-эндпоинты.
- `docs/diploma/K7_ogranicheniya_mvp.md` — 10 задокументированных ограничений с путями к снятию.
- `docs/diploma/K8_screenshoty_web.md` — инструкция и перечень 20 скриншотов web-версии.
- `docs/diploma/K9_screenshoty_mobile.md` — инструкция и перечень 12 скриншотов mobile-layout.
- `docs/diploma/K10_instrukciya_zapuska.md` — пошаговая инструкция установки с troubleshooting.
- `docs/diploma/K11_instrukciya_demonstracii.md` — 8 блоков демо на 10–15 мин + FAQ для комиссии.
- `docs/diploma/K12_sootvetstvie_tz.md` — отчёт соответствия ТЗ: все 10 критериев выполнены.
- `claude/PLAN.md` — все задачи K1–K12 отмечены ✅, статус «Этап K завершён».

### Итог

Все этапы A–K выполнены. ТЗ закрыто на уровне дипломного MVP.

---

## 2026-05-24 (Redesign — Шаг 04: Глобальный поиск)

### Что изменено

- `src/pages/search_page.py` (новый) — добавлен экран глобального поиска с SearchBox, фильтрами, недавними запросами, популярными запросами, быстрыми фильтрами и секциями результатов: проблемы, сценарии, ситуации, документы, закон-апдейты и учреждения.
- `src/main.py` — добавлен маршрут `/search`, состояние запроса/фильтра, debounce 250 мс для ввода, обработчики поиска и подключение главного поиска к глобальному поиску.
- `src/components/bottom_nav.py` — мобильная навигация обновлена под редизайн поиска: Главная / Поиск / Ситуации / Док-ты / Профиль.
- `src/components/layout.py` — desktop top-nav получил пункт «Поиск».
- `docs/redesign-progress/04-*.png` — сохранены скриншоты поиска в light/dark, desktop/mobile.
- `PLAN-REDESIGN.md`, `claude/PLAN.md` — отмечен завершённый шаг 04.

### Результат проверки

- `.venv/bin/python -m compileall src` — ✅ без ошибок.
- `.venv/bin/flet run -w src/main.py --host 127.0.0.1 -p 8550` — ✅ запущен и проверен в light/dark, desktop/mobile.

---

## 2026-05-24 (Redesign — Шаг 03: Главная)

### Что изменено

- `src/pages/home_page.py` — главная перестроена под новый dashboard-визуал: hero-поиск, быстрые действия, статистика, активные ситуации, ближайшие задачи, категории, популярные проблемы, документы, напоминания и закон-апдейты.
- `src/components/bottom_nav.py` — мобильная нижняя навигация адаптирована под web/mobile preview: пять пунктов помещаются в ширину 340 px без обрезки.
- `src/pages/profile_page.py`, `src/pages/documents_page.py`, `src/pages/email_preview_page.py`, `src/pages/utility_tracker_page.py`, `src/pages/admin_page.py`, `src/main.py` — минимальные compatibility-правки под Flet 0.85 (`border_all`, `padding_symmetric`) без изменения бизнес-логики.
- `docs/redesign-progress/03-*.png` — сохранены скриншоты главной в light/dark, desktop/mobile.
- `PLAN-REDESIGN.md`, `claude/PLAN.md` — отмечен завершённый шаг 03.

### Результат проверки

- `.venv/bin/python -m compileall src` — ✅ без ошибок.
- `.venv/bin/flet run -w src/main.py --host 127.0.0.1 -p 8550` — ✅ запущен и проверен в light/dark, desktop/mobile.

---

## 2026-05-24 (Этап J — Финальный контент и проверка источников)

### Что изменено

- **J1/J3** `src/data/mock_data.py` — все 9 записей `OFFICIAL_SOURCES` получили `last_checked_at: "2026-05-24"` и `status: "checked"`. Добавлены 4 новых источника (ОГиМ МВД, ГАИ МВД, Верховный суд, Реестр недвижимости). Все сценарии получили поле `last_checked: "2026-05-24"`.
- **J2** `src/data/mock_data.py` — устранены плейсхолдеры: «Сайты местных исполнительных комитетов» → «Исполнительные комитеты (портал)»; тексты контактов используют конкретные ведомства вместо общих описаний.
- **J4** `src/data/mock_data.py` — в `LAW_DETAIL` убрана формулировка «обратитесь за консультацией» → «обратитесь за разъяснениями»; исправлены неточные глаголы на нейтральные («уточните», «проверьте на сайте»).
- **J5** `src/data/mock_data.py` — добавлена константа `CONTENT_DISCLAIMER` (единый текст предупреждения о справочном характере). Подключена в `about_page.py`, `scenario_detail_page.py`, `problem_detail_page.py`.
- **J6** `src/data/mock_data.py` — добавлены 3 новых проблемы: алименты, покупка жилья, государственные пособия. Добавлены 4 новых сценария с полными задачами, этапами, документами, учреждениями, источниками: `auto-registration`, `alimony`, `buy-housing`, `benefits`. Итого: 14 проблем, 9 сценариев.
- **J7** `docs/SOURCES.md` (новый) — список использованных ресурсов для диплома: 8 официальных госпорталов, 9 технологий, 7 нормативных актов с указанием статей, 5 методических источников.

### Какие файлы затронуты

- `src/data/mock_data.py`
- `src/pages/about_page.py`
- `src/pages/scenario_detail_page.py`
- `src/pages/problem_detail_page.py`
- `docs/SOURCES.md` (новый)
- `claude/PLAN.md`

### Результат проверки

- `compileall src -q` — ✅ без ошибок
- SCENARIO_TEMPLATES: 9 (было 5), PROBLEMS: 14 (было 11)
- CONTENT_DISCLAIMER импортируется из mock_data ✅
- Все источники имеют `last_checked_at: "2026-05-24"` ✅

---

## 2026-05-24 (Этап I — Email и push)

### Что изменено

- **I1** `src/pages/email_preview_page.py` (новый) — Flet-экран предпросмотра email: шапка письма (от/кому/тема), тело с разметкой, MVP-баннер, кнопки «Отправить (demo)» и «Закрыть». Функция `build_doc_expiry_email_data()` используется и в UI, и в backend.
- **I1** `src/pages/notifications_page.py` — уведомление типа `email_demo` при клике открывает `/email-preview` через новый callback `on_open_email_preview`. Добавлена подсказка «Нажмите, чтобы открыть предпросмотр →».
- **I1** `src/main.py` — импорт `build_email_preview_page`, состояние `email_preview_data`, функция `open_email_preview()`, маршрут `/email-preview` в `route_change`.
- **I2** `src/backend/models.py` — модель `EmailNotification` (status: pending/sent/failed/skipped_limit, user_id, recipient_email, subject, body, scheduled_at, sent_at, delivery log).
- **I2** `src/backend/migrations/0002_auth.sql` — таблица `email_notifications` с индексами.
- **I2** `src/backend/schemas.py` — схема `EmailNotificationOut`.
- **I3** `src/backend/email_service.py` — SMTP-настройки через env (SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM, SMTP_TLS). Функция `_send_smtp()`, HTML-шаблон `_html_template()`, `build_doc_expiry_body()`.
- **I4** `src/backend/email_service.py` — `enqueue_email()` — ставит письмо в очередь (status=pending). `send_pending_emails()` — обрабатывает очередь (batch_size=50), вызывается из admin endpoint или планировщика.
- **I5** `src/backend/email_service.py` — `_daily_limit_exceeded()`, `MAX_EMAILS_PER_USER_PER_DAY=5`. `list_email_log()` для журнала доставки.
- **I5** `src/backend/api/admin.py` — endpoint `GET /api/admin/email-log` и `POST /api/admin/email-queue/flush`.
- **I6** `docs/PUSH_NOTIFICATIONS.md` (новый) — архитектурный план push-уведомлений (FCM/APNs/Web Push), схема таблицы `push_subscriptions`, план реализации.

### Какие файлы затронуты

- `src/pages/email_preview_page.py` (новый)
- `src/pages/notifications_page.py`
- `src/main.py`
- `src/backend/models.py`
- `src/backend/schemas.py`
- `src/backend/email_service.py` (новый)
- `src/backend/api/admin.py`
- `src/backend/migrations/0002_auth.sql`
- `docs/PUSH_NOTIFICATIONS.md` (новый)
- `claude/PLAN.md`

### Результат проверки

- `compileall src -q` — ✅ без ошибок
- email routes: `/api/admin/email-log`, `/api/admin/email-queue/flush`
- `EmailNotification`, `build_email_preview_page`, `enqueue_email` — ✅ импортируются

---

## 2026-05-24 (Этап H — PostgreSQL, авторизация, безопасность)

### Что изменено

- **H1** `src/backend/migrations/0002_auth.sql` — полная SQL-схема: roles, users, refresh_tokens, user_documents, user_situations, user_notifications, audit_logs.
- **H2/H3/H4** `src/backend/auth.py` — bcrypt-хэширование паролей, JWT access/refresh-токены (HS256).
- **H2/H3/H6** `src/backend/api/auth.py` — эндпоинты register/login/refresh/logout/me, зависимость `get_current_user_email`, RBAC `require_role()` с проверкой по БД.
- **H5** `src/backend/models.py` — SQLAlchemy-модели `Role`, `User`, `RefreshToken`, `UserDocument`.
- **H6** `src/backend/api/admin.py` — все `/api/admin/*` защищены `Depends(require_role("content_editor"))` на уровне роутера.
- **H7** `src/backend/api/user.py` — `GET /api/user/documents/{doc_id}/file` требует JWT, описана production-политика хранения файлов.
- **H8** `docs/SECURITY_POLICY.md` — политика безопасности: PII, шифрование, JWT, ограничения MVP.
- **H9** `src/backend/service.py` — `log_audit_event()`, `list_audit_logs()`. Аудит пишется на create/delete сценариев, проблем, закон-апдейтов. Endpoint `GET /api/admin/audit-logs`.
- **H10** `scripts/backup.sh` — резервное копирование SQLite + user_docs с ротацией.
- `src/backend/app.py` — зарегистрированы auth_router и user_router.
- Установлены зависимости: `passlib[bcrypt]`, `python-jose`, `pydantic[email]`, `python-multipart`.

### Какие файлы затронуты

- `src/backend/models.py`
- `src/backend/auth.py`
- `src/backend/api/auth.py`
- `src/backend/api/admin.py`
- `src/backend/api/user.py`
- `src/backend/api/public.py`
- `src/backend/service.py`
- `src/backend/app.py`
- `src/backend/migrations/0002_auth.sql`
- `docs/SECURITY_POLICY.md` (новый)
- `scripts/backup.sh` (новый)
- `claude/PLAN.md`

### Результат проверки

- `compileall src -q` — ✅ без ошибок
- `python -c "from backend.app import app"` — ✅ все маршруты загружены
- auth routes: register, login, refresh, logout, me
- admin audit route: `/api/admin/audit-logs`
- user doc route: `/api/user/documents/{doc_id}/file`

---

## 2026-05-24 (Redesign: вход и регистрация)

### Что изменено

- Выполнен шаг 02 редизайна: экраны входа и регистрации приведены к единой auth-системе.
- Добавлен общий компонент `auth_forms` с логотипом, переключателем «Вход / Регистрация», токенизированными полями и helper-логикой ошибок.
- `LoginPage` получил центрированную карточку, демо-доступ, remember checkbox и локальную проверку email/пароля.
- `RegisterPage` получил единую карточку регистрации, поля имени, email, региона, города, пароля и локальную проверку формы.
- Исправлена runtime-совместимость `app_card(animate=True)` с Flet 0.85 через `ft.Animation`.

### Какие файлы затронуты

- `PLAN-REDESIGN.md`
- `src/components/auth_forms.py`
- `src/components/cards.py`
- `src/pages/login_page.py`
- `src/pages/register_page.py`
- `claude/PLAN.md`
- `docs/redesign-progress/02-desktop-light.png`
- `docs/redesign-progress/02-desktop-dark.png`
- `docs/redesign-progress/02-mobile-light.png`
- `docs/redesign-progress/02-mobile-dark.png`
- `docs/redesign-progress/02-register-desktop-light.png`
- `docs/redesign-progress/02-register-desktop-dark.png`
- `docs/redesign-progress/02-register-mobile-light.png`
- `docs/redesign-progress/02-register-mobile-dark.png`

### Результат проверки

- Выполнено: `.venv/bin/python -m compileall src`.
- Выполнено: `.venv/bin/flet run -w src/main.py --host 127.0.0.1 -p 8550`.
- Сняты скриншоты входа и регистрации для desktop/mobile и light/dark.

## 2026-05-24 (Redesign: onboarding)

### Что изменено

- Выполнен шаг 01 редизайна: экран onboarding заменён на цельный hero-экран.
- Добавлены PhotoPlaceholder, крупный заголовок, поисковый preview, slide/dots-индикатор из 4 шагов и две CTA-кнопки.
- Для desktop используется центрированная карточка около 560 px.
- Для mobile задана отдельная вертикальная компоновка без горизонтального overflow.
- `ghost_button` приведён к токенизированному вторичному виду, чтобы не появлялась чёрная системная кнопка в light-теме.

### Какие файлы затронуты

- `PLAN-REDESIGN.md`
- `src/pages/onboarding_page.py`
- `src/components/buttons.py`
- `claude/PLAN.md`
- `docs/redesign-progress/01-desktop-light.png`
- `docs/redesign-progress/01-desktop-dark.png`
- `docs/redesign-progress/01-mobile-light.png`
- `docs/redesign-progress/01-mobile-dark.png`

### Результат проверки

- Выполнено: `.venv/bin/python -m compileall src`.
- Выполнено: `.venv/bin/flet run -w src/main.py --host 127.0.0.1 -p 8550`.
- Сняты 4 скриншота для desktop/mobile и light/dark.

## 2026-05-24 (Redesign: дизайн-система)

### Что изменено

- Выполнен шаг 0 редизайна: добавлены токены light/dark, палитры бейджей, радиусы, отступы и тени.
- `APP_COLORS` сохранён как совместимый прокси для старых ключей, чтобы legacy-страницы не ломались во время поэтапного редизайна.
- Добавлены базовые компоненты редизайна: `PhotoPlaceholder`, `Sidebar`, `MobileTopBar`, `StageStepCard`.
- В профиль добавлен переключатель тёмной темы, значение сохраняется в локальном состоянии.

### Какие файлы затронуты

- `PLAN-REDESIGN.md`
- `src/theme/app_theme.py`
- `src/components/cards.py`
- `src/components/buttons.py`
- `src/components/bottom_nav.py`
- `src/components/layout.py`
- `src/components/app_bar.py`
- `src/components/placeholders.py`
- `src/components/sidebar.py`
- `src/components/mobile_topbar.py`
- `src/components/timeline.py`
- `src/pages/profile_page.py`
- `src/main.py`
- `claude/PLAN.md`
- `docs/redesign-progress/0-desktop-light.png`
- `docs/redesign-progress/0-desktop-dark.png`
- `docs/redesign-progress/0-mobile-light.png`
- `docs/redesign-progress/0-mobile-dark.png`

### Результат проверки

- Выполнено: `.venv/bin/python -m compileall src`.
- Выполнено: `.venv/bin/flet run -w src/main.py --host 127.0.0.1 -p 8550`.
- Сняты 4 скриншота для desktop/mobile и light/dark.

## 2026-05-23 (обновлённый план добивки ТЗ)

### Что изменено

- Создан отдельный актуальный план добивки ТЗ с учётом First Beta и уже выполненных спринтов.
- В плане разделены: что закрыто, что закрыто частично, что ещё не реализовано.
- Зафиксирован новый порядок работ: админка, персонализация, документы/уведомления, ЖКХ/налоги, аудит, backend, безопасность и дипломная документация.
- Подтверждено правило: до полного закрытия ТЗ основной режим проверки — web-версия.

### Какие файлы затронуты

- `docs/TZ_FINAL_COMPLETION_PLAN.md`
- `docs/CHANGELOG.md`

### Результат проверки

- Markdown-файл создан.
- Код приложения не изменялся.

## 2026-05-23 (CRUD официальных источников)

### Что изменено

- Продолжен спринт 4 roadmap: админка и редактор контента.
- Локальное состояние расширено справочником `official_sources`.
- В моковые данные добавлены официальные источники: `pravo.by`, `portal.gov.by`, `mintrud.gov.by`, `nalog.gov.by`, `minjust.gov.by`.
- В админ-панели добавлена форма создания официального источника.
- В админ-панели добавлен список источников со статусом проверки, типом, датой проверки и описанием.
- Редактор может создать, отредактировать, удалить источник и переключить статус `active` / `requires_check`.
- Добавлена базовая проверка URL: источник должен быть `pravo.by` или доменом `.gov.by`.
- Действия с источниками записываются в демонстрационный аудит.

### Какие файлы затронуты

- `src/main.py`
- `src/data/mock_data.py`
- `src/pages/admin_page.py`
- `README.md`
- `docs/TZ_COMPLETION_ROADMAP.md`
- `docs/PROJECT_STATUS.md`
- `docs/TASKS.md`
- `docs/APP_SCREENS.md`
- `docs/CHANGELOG.md`

### Результат проверки

- Выполнено: `.venv/bin/python -m compileall src`.
- Выполнен smoke-check `AdminPage` с блоком официальных источников.
- Выполнен web-перезапуск: `.venv/bin/flet run -w src/main.py --host 127.0.0.1 -p 8550`.
- Проверено: `curl -I http://127.0.0.1:8550` вернул `HTTP/1.1 200 OK`.

## 2026-05-23 (редактирование закон-апдейтов и персональная лента)

### Что изменено

- Продолжен спринт 4 roadmap: админка, роли и редакторский модуль закон-апдейтов.
- В форму создания закон-апдейта добавлены поля «Что сделать пользователю» и «Связанные сценарии».
- В список закон-апдейтов редактора добавлена кнопка редактирования.
- Через UI редактора теперь можно изменить категорию, статус, приоритет, аудиторию, дату, описание, действие для пользователя, источник, подробности и связанные сценарии.
- Детальная страница закон-апдейта показывает блоки «Что сделать пользователю», «Связанные сценарии» и «Официальный источник».
- Лента «Изменения законодательства» получила блок «Важное для вас» на основе интересов профиля, активных ситуаций, избранных сценариев и высокого приоритета записи.
- Моковые закон-апдейты дополнены приоритетом, действиями для пользователя, статусом и связанными сценариями.

### Какие файлы затронуты

- `src/main.py`
- `src/data/mock_data.py`
- `src/pages/admin_page.py`
- `src/pages/legal_updates_page.py`
- `src/pages/law_detail_page.py`
- `docs/PROJECT_STATUS.md`
- `docs/TASKS.md`
- `docs/APP_SCREENS.md`
- `docs/CHANGELOG.md`

### Результат проверки

- Выполнено: `.venv/bin/python -m compileall src`.
- Выполнен smoke-check `AdminPage`, `LegalUpdatesPage`, `LawDetailPage`.
- Выполнен web-перезапуск: `.venv/bin/flet run -w src/main.py --host 127.0.0.1 -p 8550`.
- Проверено: `curl -I http://127.0.0.1:8550` вернул `HTTP/1.1 200 OK`.

## 2026-05-23 (CRUD закон-апдейтов в админке)

### Что изменено

- Продолжен спринт 4 roadmap: админка и роли.
- Локальное состояние расширено ключами `law_updates` и `law_detail`.
- Лента «Изменения законодательства» теперь показывает опубликованные записи из локального состояния.
- Детальная страница закон-апдейта теперь принимает локальный список записей и подробностей.
- В админ-панель добавлена форма создания закон-апдейта.
- В админ-панель добавлен список закон-апдейтов редактора со статусом, приоритетом и удалением.
- Редактор может создать запись, перевести её в `published`/`draft` и удалить демо-запись.
- Действия с закон-апдейтами записываются в демонстрационный аудит.

### Какие файлы затронуты

- `src/main.py`
- `src/pages/admin_page.py`
- `src/pages/law_detail_page.py`
- `README.md`
- `docs/TZ_COMPLETION_ROADMAP.md`
- `docs/PROJECT_STATUS.md`
- `docs/TASKS.md`
- `docs/APP_SCREENS.md`
- `docs/CHANGELOG.md`
- `docs/DECISIONS.md`

### Результат проверки

- Выполнено: `.venv/bin/python -m compileall src`.
- Выполнен smoke-check `AdminPage`, `LegalUpdatesPage`, `LawDetailPage`.

## 2026-05-23 (роли и админ-панель)

### Что изменено

- Начат спринт 4 roadmap: роли и админ-панель.
- Добавлены демо-роли: `Гражданин`, `Редактор контента`, `Админ площадки`.
- Локальное состояние расширено ключами `admin_roles`, `admin_users`, `admin_audit_logs`, `current_admin_role`.
- В админ-панель добавлен блок «Роли и доступ».
- Админ-панель показывает права и доступные разделы выбранной роли.
- Для роли «Гражданин» админ-действия скрываются как недоступные.
- Для роли «Админ площадки» показываются демо-пользователи и последние действия аудита.

### Какие файлы затронуты

- `src/main.py`
- `src/data/mock_data.py`
- `src/pages/admin_page.py`
- `README.md`
- `docs/TZ_COMPLETION_ROADMAP.md`
- `docs/PROJECT_STATUS.md`
- `docs/TASKS.md`
- `docs/APP_SCREENS.md`
- `docs/CHANGELOG.md`
- `docs/DECISIONS.md`

### Результат проверки

- Выполнено: `.venv/bin/python -m compileall src`.
- Выполнен smoke-check сборки `AdminPage` для ролей `citizen`, `content_editor`, `platform_admin`.

## 2026-05-23 (web-проверка)

### Что изменено

- Исправлена совместимость выбора файла документа с Flet 0.85 в web-режиме.
- `FilePicker` переведён на актуальный async API `pick_files()`.
- `FilePicker` перенесён из `page.overlay` в `page.services`, чтобы web-версия не показывала ошибку `Unknown control: FilePicker`.
- Для web-режима добавлено сохранение выбранного файла по байтам, когда браузер не отдаёт локальный путь.

### Какие файлы затронуты

- `src/main.py`
- `docs/CHANGELOG.md`

### Результат проверки

- Выполнено: `.venv/bin/python -m compileall src`.
- Запускается web-версия: `.venv/bin/flet run -w src/main.py --host 127.0.0.1 -p 8550`.

## 2026-05-20 (госучреждения)

### Что изменено

- Выполнен локальный MVP спринта «Госучреждения».
- Добавлены типы учреждений и локальный справочник учреждений.
- Добавлен сервис подбора учреждений по типу, региону и городу пользователя.
- Локальное состояние расширено ключом `institutions`.
- Задачи сценариев связаны с типами учреждений через `institution_types`.
- При создании ситуации типы учреждений переносятся в локальные задачи.
- Детальная ситуация показывает блок «Куда обращаться» с подобранными учреждениями, адресом, телефоном и сайтом.
- Детальная страница сценария показывает типы учреждений для шагов.

### Какие файлы затронуты

- `src/main.py`
- `src/data/mock_data.py`
- `src/services/institutions.py`
- `src/pages/situation_detail_page.py`
- `src/pages/scenario_detail_page.py`
- `README.md`
- `docs/TZ_COMPLETION_ROADMAP.md`
- `docs/PROJECT_STATUS.md`
- `docs/TASKS.md`
- `docs/APP_SCREENS.md`
- `docs/ARCHITECTURE.md`
- `docs/CHANGELOG.md`
- `docs/DECISIONS.md`

### Результат проверки

- Выполнено: `.venv/bin/python -m compileall src`.
- Выполнен smoke-check сервиса подбора учреждений.
- Выполнен smoke-check `SituationDetailPage` с блоком учреждения.
- Выполнено: `.venv/bin/flet run src/main.py` (старт без traceback, процесс остановлен вручную).

## 2026-05-20 (зависимости шагов)

### Что изменено

- Начат и выполнен локальный MVP спринта «Зависимости шагов».
- В шаблоны сценариев добавлено поле `depends_on` для зависимых задач.
- При создании пользовательской ситуации зависимости переводятся из ID шаблонных задач в ID локальных задач.
- Для уже созданных ситуаций из шаблонов зависимости нормализуются при запуске.
- В детальной ситуации заблокированные задачи показывают причину блокировки.
- Заблокированную задачу нельзя отметить выполненной до завершения предыдущих задач.
- Задачи в детальной ситуации сгруппированы по этапам.
- Добавлены фильтры задач: все, доступные, заблокированные, выполненные, просроченные.
- В детальной странице сценария показывается текст «Зависит от...» для задач с зависимостями.

### Какие файлы затронуты

- `src/main.py`
- `src/data/mock_data.py`
- `src/pages/situation_detail_page.py`
- `src/pages/scenario_detail_page.py`
- `README.md`
- `docs/TZ_COMPLETION_ROADMAP.md`
- `docs/PROJECT_STATUS.md`
- `docs/TASKS.md`
- `docs/APP_SCREENS.md`
- `docs/CHANGELOG.md`

### Результат проверки

- Выполнено: `.venv/bin/python -m compileall src`.
- Выполнен smoke-check `SituationDetailPage` с заблокированной задачей.
- Выполнено: `.venv/bin/flet run src/main.py` (старт без traceback, процесс остановлен вручную).

## 2026-05-20 (roadmap ТЗ и личные документы)

### Что изменено

- Зафиксирована дорожная карта полного закрытия ТЗ после первой беты.
- В правила AI-агента добавлено требование читать `docs/TZ_COMPLETION_ROADMAP.md` перед крупными задачами по ТЗ.
- В `docs/TASKS.md` добавлены этапы дальнейшего развития: личные документы, зависимости шагов, госучреждения, роли/админка, персонализация, закон-апдейты, уведомления/email, ЖКХ/налоги, backend/PostgreSQL.
- Начат первый спринт roadmap: личные документы и демонстрационная безопасность.
- Раздел «Мои документы» расширен полями личного документа, автоматическим статусом по сроку действия, маскированием номера, переключателем приватности и предупреждением перед просмотром скана.
- В форму личного документа добавлен FilePicker для выбора файла скана.
- Выбранный файл копируется в `data/private_uploads/`, если Flet отдаёт локальный путь.
- Метаданные выбранных файлов сохраняются в `uploaded_files`.
- Локальное состояние расширено ключами `personal_documents`, `privacy_settings`, `uploaded_files`.
- Добавлена локальная папка `data/private_uploads/` и исключение локальных пользовательских данных из Git.
- Обновлена документация по локальному демо-хранению и production-ограничениям безопасности.

### Какие файлы затронуты

- `AGENTS.md`
- `.gitignore`
- `README.md`
- `src/main.py`
- `src/data/mock_data.py`
- `src/pages/documents_page.py`
- `docs/TZ_COMPLETION_ROADMAP.md`
- `docs/PROJECT_STATUS.md`
- `docs/TASKS.md`
- `docs/APP_SCREENS.md`
- `docs/CHANGELOG.md`
- `docs/DECISIONS.md`

### Результат проверки

- Выполнено: `.venv/bin/python -m compileall src`.
- Выполнен smoke-check сборки `DocumentsPage`.
- Выполнено: `.venv/bin/flet run src/main.py` (старт без traceback, процесс остановлен вручную).

## 2026-05-19 (отчёт по соответствию ТЗ)

### Что изменено

- Создан подробный отчёт о реализации проекта по техническому заданию.
- Создан краткий gap-анализ по разделам ТЗ.
- Код приложения не изменялся.

### Какие файлы затронуты

- `docs/TZ_IMPLEMENTATION_REPORT.md`
- `docs/TZ_GAP_ANALYSIS.md`
- `docs/CHANGELOG.md`

### Результат проверки

- Проверено наличие созданных Markdown-файлов.

## 2026-05-19 (фикс диалогов редактирования)

### Что изменено

- Исправлено закрытие модальных окон через актуальный механизм Flet `pop_dialog()`.
- Окна добавления и редактирования документов, ситуаций, задач и интересов приведены к единому виду.
- Диалог «Редактировать ситуацию» получил стабильную ширину, аккуратные отступы, ограничение по высоте и выровненные кнопки действий для web/desktop и iPhone.

### Какие файлы затронуты

- `src/main.py`
- `docs/CHANGELOG.md`

### Результат проверки

- Выполнено: `.venv/bin/python -m compileall src`.
- Выполнено: `.venv/bin/flet run src/main.py` (старт без traceback, процесс остановлен вручную).

## 2026-05-19 (полировка первой беты)

### Что изменено

- Добавлен экран `/about` с описанием приложения, статусом `0.1 beta`, реализованными функциями, планами и справочным предупреждением.
- Добавлен onboarding первого запуска: выбор сценария, пошаговый план, выполнение задач и прогресс.
- Состояние onboarding сохраняется в `data/app_state.json`.
- Добавлены избранные сценарии с локальным сохранением.
- В профиле добавлен блок «Избранные сценарии» и переход на экран «О приложении».
- Улучшены пустые состояния в документах, уведомлениях, ситуациях и dashboard-блоках.
- Добавлены демо-подсказки на главной, в детальной странице сценария и в детальной ситуации.
- Улучшен блок официальных источников в сценарии: название, сайт, описание и статус проверки.
- Увеличена высота мобильных карточек категорий и уменьшены мобильные отступы настроек профиля, чтобы экран выглядел цельнее на iPhone.
- Созданы `docs/DEMO_SCRIPT.md` и `docs/BETA_CHECKLIST.md`.

### Какие файлы затронуты

- `src/main.py`
- `src/components/cards.py`
- `src/components/layout.py`
- `src/pages/about_page.py`
- `src/pages/onboarding_page.py`
- `src/pages/home_page.py`
- `src/pages/scenario_templates_page.py`
- `src/pages/scenario_detail_page.py`
- `src/pages/situation_detail_page.py`
- `src/pages/documents_page.py`
- `src/pages/notifications_page.py`
- `src/pages/profile_page.py`
- `README.md`
- `docs/PROJECT_STATUS.md`
- `docs/TASKS.md`
- `docs/APP_SCREENS.md`
- `docs/CHANGELOG.md`
- `docs/DEMO_SCRIPT.md`
- `docs/BETA_CHECKLIST.md`

### Результат проверки

- Выполнено: `.venv/bin/python -m compileall src`.
- Выполнен smoke-check новых экранов `/about`, `/onboarding`, избранных сценариев, пустых состояний и основных страниц.
- Выполнено: `.venv/bin/flet run src/main.py` (старт без traceback, процесс остановлен вручную).

## 2026-05-19 (первая демонстрационная бета)

### Что изменено

- Проект доведён до цельного First Beta MVP для показа научному руководителю.
- Основной сценарий «Рождение ребёнка» расширен до 7 этапов и более полного набора задач.
- Детальная страница сценария показывает краткое описание, этапы, задачи, документы, организации, источники с пояснениями и связанные сценарии.
- При повторном создании активной ситуации из того же шаблона появляется предупреждение: открыть существующую или создать ещё одну.
- В разделе «Мои ситуации» добавлены фильтры «Все», «Активные», «Завершённые» и количество выполненных задач.
- В профиле добавлен блок «Демо-режим» со сбросом локальных демо-данных.
- Добавлены документы для показа руководителю: `BETA_DEMO_GUIDE.md` и `BETA_ACCEPTANCE_CHECKLIST.md`.

### Какие файлы затронуты

- `src/main.py`
- `src/data/mock_data.py`
- `src/pages/scenario_detail_page.py`
- `src/pages/situations_page.py`
- `src/pages/profile_page.py`
- `README.md`
- `docs/PROJECT_STATUS.md`
- `docs/TASKS.md`
- `docs/APP_SCREENS.md`
- `docs/CHANGELOG.md`
- `docs/DECISIONS.md`
- `docs/MVP_SCOPE.md`
- `docs/LEARNING_MODULE.md`
- `docs/IOS_LAYOUT_CHECKLIST.md`
- `docs/BETA_DEMO_GUIDE.md`
- `docs/BETA_ACCEPTANCE_CHECKLIST.md`

### Результат проверки

- Выполнено: `.venv/bin/python -m compileall src`.
- Выполнен smoke-check ключевых страниц первой беты.
- Выполнено: `.venv/bin/flet run src/main.py` (старт без traceback, процесс остановлен вручную).
- Выполнено: `.venv/bin/flet run --web src/main.py` (web-preview поднялся на локальном адресе, процесс остановлен вручную).

## 2026-05-19 (динамические уведомления по задачам)

### Что изменено

- Добавлена синхронизация уведомлений с задачами пользователя.
- Для задач с датой срока на ближайшие 7 дней создаются локальные уведомления.
- Для просроченных невыполненных задач создаются локальные уведомления с пометкой «Просрочено».
- Уведомления по задачам сохраняют статус прочтения.
- После выполнения или удаления задачи связанное уведомление исчезает.
- Главная страница теперь показывает текущие уведомления приложения в блоке «Напоминания».

### Какие файлы затронуты

- `src/main.py`
- `src/pages/home_page.py`
- `README.md`
- `docs/PROJECT_STATUS.md`
- `docs/TASKS.md`
- `docs/APP_SCREENS.md`
- `docs/CHANGELOG.md`

### Результат проверки

- Выполнено: `.venv/bin/python -m compileall src`.
- Выполнен smoke-check `HomePage` и `NotificationsPage` с динамическим уведомлением задачи.

## 2026-05-19 (документы в ручных задачах)

### Что изменено

- В диалог добавления задачи добавлено поле «Документы для задачи».
- В диалог редактирования задачи добавлено поле «Документы для задачи».
- Документы можно вводить новой строкой, через точку с запятой или через запятую.
- Пометка `необязательно` или `при необходимости` делает документ дополнительным.
- Документы ручных задач сохраняются в `data/app_state.json`.
- Детальная ситуация показывает документы ручных задач в общем блоке «Документы к подготовке».
- Главная страница учитывает документы ручных задач в dashboard-блоке подготовки документов.

### Какие файлы затронуты

- `src/main.py`
- `README.md`
- `docs/PROJECT_STATUS.md`
- `docs/TASKS.md`
- `docs/APP_SCREENS.md`
- `docs/CHANGELOG.md`

### Результат проверки

- Выполнено: `.venv/bin/python -m compileall src`.
- Выполнен smoke-check `SituationDetailPage` с ручной задачей и документами.
- Выполнен smoke-check `build_dashboard_data`: документы ручной задачи попадают в список подготовки.

## 2026-05-19 (даты сроков для ручных задач)

### Что изменено

- В диалог добавления задачи добавлено поле «Дата срока».
- В диалог редактирования задачи добавлено поле «Дата срока».
- Поле принимает даты в форматах `YYYY-MM-DD` и `DD.MM.YYYY`.
- При некорректном формате показывается предупреждение, а задача не сохраняется.
- Ручные задачи сохраняют `due_date`, поэтому отображаются на главной в ближайших или просроченных задачах.
- В детальной странице ситуации дата срока отображается рядом с текстовым сроком задачи.

### Какие файлы затронуты

- `src/main.py`
- `src/pages/situation_detail_page.py`
- `README.md`
- `docs/PROJECT_STATUS.md`
- `docs/TASKS.md`
- `docs/APP_SCREENS.md`
- `docs/CHANGELOG.md`

### Результат проверки

- Выполнено: `.venv/bin/python -m compileall src`.
- Выполнен smoke-check `SituationDetailPage` с задачей, у которой есть `due_date`.
- Выполнен smoke-check `build_dashboard_data`: ручная задача с датой попадает в ближайшие задачи.

## 2026-05-19 (полировка сценариев и детальной ситуации)

### Что изменено

- В разделе «Жизненные сценарии» добавлены поиск и фильтрация по категориям.
- Добавлено пустое состояние для списка сценариев, если ничего не найдено.
- В детальной странице ситуации добавлен блок «Документы к подготовке».
- Документы в детальной ситуации собираются автоматически из задач и не повторяются.
- В карточке прогресса ситуации теперь показывается количество выполненных задач.
- Убрана устаревшая заглушка «Документы и заметки будут подключены позже».

### Какие файлы затронуты

- `src/main.py`
- `src/pages/scenario_templates_page.py`
- `src/pages/situation_detail_page.py`
- `README.md`
- `docs/PROJECT_STATUS.md`
- `docs/TASKS.md`
- `docs/APP_SCREENS.md`
- `docs/CHANGELOG.md`

### Результат проверки

- Выполнено: `.venv/bin/python -m compileall src`.
- Выполнен smoke-check `ScenarioTemplatesPage` с поиском/фильтрами и пустым состоянием.
- Выполнен smoke-check `SituationDetailPage` для существующих ситуаций и блока документов.

## 2026-05-19 (расширение шаблонов жизненных сценариев)

### Что изменено

- Расширен локальный каталог готовых сценариев в `SCENARIO_TEMPLATES`.
- Добавлены сценарии:
  - «Потеря паспорта»;
  - «Расторжение брака»;
  - «Открытие ИП»;
  - «Переезд и регистрация».
- Для каждого сценария добавлены этапы, задачи, документы, организации и официальные источники.
- Существующие экраны `/scenarios` и `/scenario-detail` используют новые данные без изменения бизнес-логики.
- Создание пользовательской ситуации из шаблона продолжает работать через существующий механизм.

### Какие файлы затронуты

- `src/data/mock_data.py`
- `README.md`
- `docs/PROJECT_STATUS.md`
- `docs/TASKS.md`
- `docs/APP_SCREENS.md`
- `docs/CHANGELOG.md`

### Результат проверки

- Выполнено: `.venv/bin/python -m compileall src`.
- Выполнен smoke-check структуры `SCENARIO_TEMPLATES`: проверены id, этапы, задачи, документы, организации, источники и привязка задач к этапам.
- Выполнен smoke-check страниц сценариев: `ScenarioTemplatesPage` и `ScenarioDetailPage`.
- Выполнено: `.venv/bin/flet run src/main.py` (старт без traceback, процесс остановлен вручную).

## 2026-05-19 (фикс открытия сообщений и диалогов на iPhone)

### Что изменено

- Исправлено падение при входе на iPhone: `Page` в текущем Flet runtime не имеет метода `open`.
- Добавлен совместимый helper `_open_control`, который открывает snackbar и диалоги через `page.open(...)`, если метод доступен, через `page.show_dialog(...)` в Flet 0.85, либо через `page.overlay` как последний fallback.
- Закрытие диалогов также переведено на совместимую схему с fallback без `page.close(...)`; для Flet 0.85 используется `_dialogs`.
- Все локальные диалоги документов, ситуаций, задач и интересов теперь открываются через общий helper.

### Какие файлы затронуты

- `src/main.py`
- `docs/CHANGELOG.md`

### Результат проверки

- Выполнено: `.venv/bin/python -m compileall src`.
- Выполнено: `.venv/bin/flet run src/main.py` (старт без traceback).
- Выполнено: `.venv/bin/flet run --ios src/main.py -p 8567` (QR-код появился, старт без traceback; процесс остановлен вручную).
- После проверки редактирования ситуации helper дополнен поддержкой `page.show_dialog(...)`, чтобы кнопки «Отмена» и «Сохранить» в `AlertDialog` отрабатывали на iPhone.

## 2026-05-18 (iPhone SafeArea layout)

### Что изменено

- Добавлены iPhone layout-константы для ширин 375/393/430 px.
- Добавлены общие helpers layout: `app_safe_area`, `mobile_page_layout`, `scrollable_mobile_page`, `iphone_page_container`, `bottom_nav_safe_area`.
- Мобильные экраны теперь строятся через общий SafeArea-wrapper.
- Верхний safe area получил fallback-отступ для iPhone с notch/Dynamic Island.
- Нижняя навигация вынесена в отдельную safe area и защищена от home indicator.
- Нижняя навигация приведена к актуальным разделам: Главная, Сценарии, Ситуации, Уведомления, Профиль.
- Диалоги добавления/редактирования документов, ситуаций, задач и интересов получили адаптивную ширину.
- Исправлены мобильные overflow-риски в заголовках уведомлений, ситуаций, деталей ситуации и админ-панели.
- Исправлен параметр `Dropdown(on_change=...)` в админке на `on_select`, совместимый с Flet 0.85.
- Создан `docs/IOS_LAYOUT_CHECKLIST.md`.

### Какие файлы затронуты

- `src/theme/app_theme.py`
- `src/components/layout.py`
- `src/components/bottom_nav.py`
- `src/components/app_bar.py`
- `src/main.py`
- `src/pages/notifications_page.py`
- `src/pages/situations_page.py`
- `src/pages/problem_detail_page.py`
- `src/pages/situation_detail_page.py`
- `src/pages/admin_page.py`
- `README.md`
- `docs/PROJECT_STATUS.md`
- `docs/TASKS.md`
- `docs/APP_SCREENS.md`
- `docs/CHANGELOG.md`
- `docs/DECISIONS.md`
- `docs/IOS_LAYOUT_CHECKLIST.md`

### Результат проверки

- Выполнено: `.venv/bin/python -m compileall src`.
- Выполнен smoke-check ключевых мобильных страниц и layout-компонентов.
- Выполнено: `.venv/bin/flet run src/main.py` (старт без traceback, процесс остановлен вручную).
- Выполнено: `.venv/bin/flet run --web src/main.py` (старт без traceback, процесс остановлен вручную).

## 2026-05-18 (главный экран / дашборд)

### Что изменено

- Главная страница доработана в пользовательский дашборд.
- Добавлены блоки:
  - активные ситуации;
  - завершённые ситуации;
  - общий прогресс по активным ситуациям;
  - 2-3 активные ситуации с количеством задач;
  - ближайшие задачи;
  - просроченные задачи;
  - уникальные документы к подготовке.
- Добавлены быстрые переходы к разделам «Жизненные сценарии» и «Мои ситуации».
- Добавлен сервис `src/services/dashboard.py` для расчёта dashboard-данных.
- В моковые и шаблонные задачи добавлена поддержка `due_date`.
- При создании ситуации из шаблона задачи получают срок выполнения автоматически.
- Автоматическое обновление статуса ситуации приведено к схеме: `Не начата`, `В процессе`, `Завершена`.

### Какие файлы затронуты

- `src/main.py`
- `src/data/mock_data.py`
- `src/pages/home_page.py`
- `src/pages/situations_page.py`
- `src/services/dashboard.py`
- `README.md`
- `docs/PROJECT_STATUS.md`
- `docs/TASKS.md`
- `docs/APP_SCREENS.md`
- `docs/CHANGELOG.md`
- `docs/DECISIONS.md`

### Результат проверки

- Выполнено: `.venv/bin/python -m compileall src`.
- Выполнен smoke-check `HomePage` и `dashboard.py`.
- Выполнено: `.venv/bin/flet run src/main.py` (старт без traceback).

## 2026-05-18 (шаблоны жизненных сценариев)

### Что изменено

- Добавлена сущность шаблона сценария `SCENARIO_TEMPLATES` в моковые данные.
- Добавлен MVP-шаблон «Рождение ребёнка»:
  - этапы;
  - задачи;
  - документы;
  - организации;
  - официальные источники.
- Добавлен экран `/scenarios` со списком готовых жизненных сценариев.
- Добавлен экран `/scenario-detail` с детальным просмотром выбранного шаблона.
- В `SituationsPage` добавлена кнопка выбора готового сценария.
- Добавлена кнопка «Создать мою ситуацию»: она создает локальную ситуацию и задачи из шаблона.
- Задачи из шаблона получают привязку к конкретной ситуации и список нужных документов.
- Прогресс ситуации теперь пересчитывается автоматически по выполненным задачам.
- Локальное хранилище усилено backup-файлом `data/app_state.backup.json` и fallback-восстановлением.

### Какие файлы затронуты

- `.gitignore`
- `src/services/local_store.py`
- `src/data/mock_data.py`
- `src/main.py`
- `src/components/layout.py`
- `src/pages/scenario_templates_page.py`
- `src/pages/scenario_detail_page.py`
- `src/pages/situations_page.py`
- `src/pages/situation_detail_page.py`
- `docs/PROJECT_STATUS.md`
- `docs/TASKS.md`
- `docs/APP_SCREENS.md`
- `docs/CHANGELOG.md`
- `docs/DECISIONS.md`
- `README.md`

### Результат проверки

- Выполнено: `.venv/bin/python -m compileall src`.
- Выполнен smoke-check сборки `ScenarioTemplatesPage`, `ScenarioDetailPage`, `SituationsPage`, `SituationDetailPage` и `local_store`.
- Выполнено: `.venv/bin/flet run src/main.py` (старт без traceback).

## 2026-05-18

### Что изменено

- Добавлено локальное редактирование документов через диалог.
- Добавлено локальное удаление документов с подтверждением.
- Добавлено локальное редактирование ситуаций: название, статус и прогресс.
- Добавлено локальное удаление ситуаций с очисткой связанных задач.
- Добавлено локальное редактирование и удаление задач внутри детального экрана ситуации.
- Все операции сохраняются в `data/app_state.json`.
- Обновлены экраны документов, ситуаций и детальной ситуации под новые действия.

### Какие файлы затронуты

- `src/main.py`
- `src/pages/documents_page.py`
- `src/pages/situations_page.py`
- `src/pages/situation_detail_page.py`
- `docs/PROJECT_STATUS.md`
- `docs/TASKS.md`
- `docs/APP_SCREENS.md`
- `docs/CHANGELOG.md`
- `README.md`

### Результат проверки

- Выполнено: `.venv/bin/python -m compileall src`.
- Выполнен smoke-check сборки `DocumentsPage`, `SituationsPage`, `SituationDetailPage`.
- Выполнено: `.venv/bin/flet run src/main.py` (старт без traceback).

## 2026-05-16 (локальное сохранение и доводка MVP)

### Что изменено

- Добавлен сервис `src/services/local_store.py` для сохранения локального состояния в `data/app_state.json`.
- Локально сохраняются: демо-пользователи, профиль, настройки, документы, ситуации, задачи, уведомления, сохранённые карточки проблем и закон-апдейты.
- Задачи теперь привязаны к конкретной ситуации через `situation_id`; прогресс считается только по задачам открытой ситуации.
- В моковые закон-апдейты добавлены официальные URL, а кнопка «Открыть первоисточник» теперь открывает ссылку через Flet.
- Расширены подробные карточки проблем: «Рождение ребёнка», «Расторжение брака», «Оформление больничного», «Регистрация автомобиля».
- Обновлен `.gitignore`, чтобы локальное пользовательское состояние не попадало в репозиторий.

### Какие файлы затронуты

- `.gitignore`
- `src/main.py`
- `src/data/mock_data.py`
- `src/pages/situation_detail_page.py`
- `src/services/local_store.py`
- `docs/PROJECT_STATUS.md`
- `docs/TASKS.md`
- `docs/APP_SCREENS.md`
- `docs/LEARNING_MODULE.md`
- `docs/CHANGELOG.md`
- `docs/DECISIONS.md`
- `README.md`

### Результат проверки

- Выполнено: `python3 -m compileall src`.
- Выполнено: `.venv/bin/python -m compileall src`.
- Выполнен smoke-check `local_store`, `SituationDetailPage` и `LawDetailPage`.
- Выполнено: `.venv/bin/flet run src/main.py` (старт без traceback).

## 2026-05-16 (финальный функциональный проход)

### Что изменено

- Добавлены экраны локальной MVP-авторизации:
  - `LoginPage`;
  - `RegisterPage`;
  - маршруты `/login` и `/register`;
  - демо-вход `ivan@example.by / 123456`;
  - регистрация локального пользователя в текущей сессии;
  - выход из профиля.
- Оживлены пользовательские действия:
  - создание персонального плана из карточки проблемы;
  - сохранение карточки проблемы;
  - добавление документа через форму;
  - добавление ситуации через форму;
  - добавление задачи в ситуации;
  - отметка задач выполненными и сохранение прогресса;
  - прочтение одного уведомления и всех уведомлений;
  - сохранение профиля;
  - добавление интереса;
  - сохранение закон-апдейта.
- Расширены статьи в `mock_data.py`: медкнижка, ЖКХ-квитанция, налоговая ошибка, переезд, открытие ИП, увольнение.
- Обновлены экраны документов, ситуаций, уведомлений, профиля, деталей ситуации и закон-апдейта для приема локального состояния и callback-обработчиков.
- Обновлена документация статуса, задач и экранов.

### Какие файлы затронуты

- `src/main.py`
- `src/data/mock_data.py`
- `src/pages/login_page.py`
- `src/pages/register_page.py`
- `src/pages/documents_page.py`
- `src/pages/situations_page.py`
- `src/pages/situation_detail_page.py`
- `src/pages/notifications_page.py`
- `src/pages/profile_page.py`
- `src/pages/law_detail_page.py`
- `src/pages/home_page.py`
- `README.md`
- `docs/PROJECT_STATUS.md`
- `docs/TASKS.md`
- `docs/APP_SCREENS.md`
- `docs/CHANGELOG.md`

### Результат проверки

- Выполнено: `python3 -m compileall src`.
- Выполнен smoke-check сборки ключевых Flet-страниц.
- Выполнено: `.venv/bin/flet run src/main.py` (старт без traceback).

## 2026-05-16 (поздний вечер)

### Что изменено

- Доработан `LegalUpdatesPage`:
  - добавлен интерактивный поиск;
  - добавлены рабочие чипы категорий;
  - добавлено пустое состояние при отсутствии результатов.
- Добавлен public API-клиент `src/services/public_api.py`.
- В `main.py` добавлена поэтапная mobile API-интеграция:
  - для карточки проблемы `childbirth` выполняется попытка загрузки сценария `rozhdenie-rebenka` через `/api/scenarios/{slug}`;
  - данные сценария нормализуются в формат экрана карточки проблемы;
  - при недоступном API используется fallback на существующие моки.
- `ProblemDetailPage` расширена поддержкой `problem_override`, чтобы безопасно подменять моковые данные API-данными.
- Обновлены документы статуса/задач/экранов.

### Какие файлы затронуты

- `src/main.py`
- `src/pages/legal_updates_page.py`
- `src/pages/problem_detail_page.py`
- `src/services/public_api.py`
- `src/services/__init__.py`
- `docs/PROJECT_STATUS.md`
- `docs/TASKS.md`
- `docs/APP_SCREENS.md`
- `docs/CHANGELOG.md`

### Результат проверки

- Выполнено: `python3 -m compileall src`.
- Выполнено: `.venv/bin/flet run src/main.py` (старт без traceback).
- Выполнена runtime-проверка сборки `LegalUpdatesPage` и `ProblemDetailPage` с API override через Python smoke-check.

## 2026-05-16

### Что изменено

- Доработан backend admin API для конструктора сценариев:
  - добавлен endpoint `GET /api/admin/scenarios/{scenario_id}` (полная структура сценария);
  - добавлен endpoint `GET /api/admin/scenarios/{scenario_id}/stages`;
  - добавлен endpoint `GET /api/admin/stages/{stage_id}/steps`.
- Расширен клиент `src/services/admin_api.py`:
  - загрузка full-сценария для конструктора;
  - создание/обновление этапов и шагов;
  - загрузка документов/организаций/сроков;
  - привязка документа к шагу через API.
- `AdminPage` переведена из preview-режима в рабочий MVP-конструктор:
  - выбор сценария для редактирования;
  - формы добавления этапов и шагов;
  - выбор action type, срока, организации и документов;
  - визуальный список этапов и шагов;
  - переключение обязательности этапов и шагов.
- Обновлен `src/main.py`:
  - расширено состояние админ-панели;
  - добавлены callback-обработчики конструктора;
  - добавлена синхронизация структуры сценария после операций create/update.
- Обновлена документация по текущему состоянию и задачам.

### Какие файлы затронуты

- `src/backend/api/admin.py`
- `src/backend/service.py`
- `src/services/admin_api.py`
- `src/pages/admin_page.py`
- `src/main.py`
- `docs/PROJECT_STATUS.md`
- `docs/TASKS.md`
- `docs/APP_SCREENS.md`
- `docs/CHANGELOG.md`

### Результат проверки

- Выполнено: `python3 -m compileall src`.
- Выполнено: `PYTHONPATH=src .venv/bin/uvicorn backend.app:app --host 127.0.0.1 --port 8060`.
- Выполнено: API smoke/E2E для конструктора через `AdminAPIClient`:
  - создание тестового этапа;
  - создание тестового шага;
  - привязка документа к шагу;
  - чтение full-структуры сценария;
  - очистка тестовых данных.
- Выполнено: `.venv/bin/flet run src/main.py` (старт без traceback).

## 2026-05-15

### Что изменено

- Добавлен HTTP-клиент для Flet-админки: `src/services/admin_api.py` (без proxy, с обработкой ошибок API).
- Подключена `AdminPage` к backend API:
  - загрузка проблем и сценариев;
  - создание проблемы;
  - создание сценария;
  - смена статусов `draft/published` для проблем и сценариев;
  - индикатор статуса подключения API и времени синхронизации.
- Обновлен `main.py`: добавлено состояние админ-панели и callback-обработчики интеграции с `/api/admin/*`.
- Выполнена end-to-end проверка клиента:
  - создание проблемы и сценария через API,
  - обновление статусов,
  - очистка тестовых записей после проверки.

### Какие файлы затронуты

- `src/main.py`
- `src/pages/admin_page.py`
- `src/services/__init__.py`
- `src/services/admin_api.py`
- `docs/PROJECT_STATUS.md`
- `docs/TASKS.md`
- `docs/APP_SCREENS.md`
- `docs/CHANGELOG.md`

### Результат проверки

- Выполнено: `python -m compileall src`.
- Выполнено: `PYTHONPATH=src python -m backend.scripts.init_db`.
- Выполнено: `PYTHONPATH=src python -m backend.scripts.seed_db`.
- Выполнено: `flet run src/main.py` (старт без traceback).
- Выполнено: `uvicorn backend.app:app --host 127.0.0.1 --port 8064`.
- Проверены через Python-клиент `AdminAPIClient` операции create/update/list.

## 2026-05-15

### Что изменено

- Добавлена backend-основа для сценариев и админ-панели:
  - ORM-модели и связи для сущностей Problem, Scenario, ScenarioStage, ScenarioStep, Document, Authority, Deadline, NotificationRule, ScenarioDependency, RelatedScenario, SourceReference, LawUpdate.
  - Миграция базы данных `src/backend/migrations/0001_initial.sql`.
  - Service-слой с загрузкой полного сценария и CRUD-операциями.
  - Public API endpoints:
    - `GET /api/problems`
    - `GET /api/problems/{slug}`
    - `GET /api/scenarios/{slug}`
    - `GET /api/scenarios/{slug}/steps`
    - `GET /api/documents`
    - `GET /api/authorities`
  - Admin API endpoints для управления проблемами, сценариями, этапами, шагами, документами, организациями, сроками, зависимостями, источниками и law updates.
- Добавлены скрипты:
  - `PYTHONPATH=src python -m backend.scripts.init_db`
  - `PYTHONPATH=src python -m backend.scripts.seed_db`
- Добавлен seed MVP-сценария «Рождение ребёнка» с этапами, шагами, документами, организациями, сроками, зависимостями, официальными источниками РБ и обновлением законодательства.
- Доработан Flet-экран `AdminPage`: отображает структуру разделов админ-панели и конструктор сценария в MVP-виде.
- Обновлены `requirements.txt`, `pyproject.toml`, `.gitignore`, README и документация статуса/архитектуры.

### Какие файлы затронуты

- `.gitignore`
- `requirements.txt`
- `pyproject.toml`
- `README.md`
- `AGENTS.md`
- `src/backend/__init__.py`
- `src/backend/config.py`
- `src/backend/database.py`
- `src/backend/enums.py`
- `src/backend/models.py`
- `src/backend/schemas.py`
- `src/backend/service.py`
- `src/backend/app.py`
- `src/backend/api/__init__.py`
- `src/backend/api/public.py`
- `src/backend/api/admin.py`
- `src/backend/migrations/0001_initial.sql`
- `src/backend/scripts/migrate.py`
- `src/backend/scripts/init_db.py`
- `src/backend/scripts/seed_db.py`
- `src/backend/seeds/__init__.py`
- `src/backend/seeds/mvp_childbirth.py`
- `src/pages/admin_page.py`
- `docs/ARCHITECTURE.md`
- `docs/PROJECT_CONTEXT.md`
- `docs/MVP_SCOPE.md`
- `docs/CODEX_WORKFLOW.md`
- `docs/DECISIONS.md`
- `docs/APP_SCREENS.md`
- `docs/SCENARIO_BACKEND.md`
- `docs/PROJECT_STATUS.md`
- `docs/TASKS.md`
- `docs/CHANGELOG.md`

### Результат проверки

- Выполнено: `PATH="$PWD/.venv/bin:$PATH" python -m compileall src`.
- Выполнено: `PYTHONPATH=src python -m backend.scripts.init_db`.
- Выполнено: `PYTHONPATH=src python -m backend.scripts.seed_db`.
- Выполнено: `PYTHONPATH=src uvicorn backend.app:app --host 127.0.0.1 --port 8060`.
- Проверены endpoints через `curl` (`/api/health`, `/api/problems`, `/api/scenarios/rozhdenie-rebenka`, `/api/authorities`, `/api/admin/scenarios`).

## 2026-05-14

### Что изменено

- Исправлена ошибка переключения вкладок на iPhone/ Python 3.14: удалена несовместимая проверка `isinstance(..., ft.ControlEvent)` в обработчике нижней навигации.
- Обновлен обработчик `on_nav_change`: теперь корректно обрабатывает строковый ключ, `event.data` и fallback по `selected_index`.
- Выровнен кроссплатформенный дизайн: `NotificationsPage`, `SituationDetailPage` и `AdminPage` переведены на единый desktop-контейнер через `desktop_content(...)`.
- Улучшен визуальный баланс и единообразие отступов/ширин карточек на desktop и мобильном.
- Цвет фона приложения приведен к `#F6F8FB` по дизайн-системе.
- Добавлена mobile safe-area адаптация для экранов iPhone с челкой (верх/низ): контент и заголовки не заходят под системные зоны.
- Нижняя навигация вынесена в отдельную safe-area по нижнему краю для корректного отображения рядом с gesture-зоной iOS.
- Снижен нижний padding мобильного контента (`page_padding`) для устранения лишней серой полосы над нижней навигацией.

### Какие файлы затронуты

- `src/main.py`
- `src/pages/notifications_page.py`
- `src/pages/situation_detail_page.py`
- `src/pages/admin_page.py`
- `src/theme/app_theme.py`
- `docs/PROJECT_STATUS.md`
- `docs/TASKS.md`
- `docs/CHANGELOG.md`

### Результат проверки

- Выполнено: `PATH="$PWD/.venv/bin:$PATH" python -m compileall src`.
- Выполнено: `PATH="$PWD/.venv/bin:$PATH" flet run -w src/main.py --host 127.0.0.1 -p 8552`.
- Проверено: `curl -I http://127.0.0.1:8552` вернул `HTTP/1.1 200 OK`.

## 2026-05-14

### Что изменено

- Добавлен интерактивный мобильный MVP на моковых данных: поиск, фильтры, маршруты и локальное состояние.
- Добавлены маршруты `/problem-detail`, `/situation-detail`, `/legal-updates`, `/law-detail`, `/learning`.
- `HomePage` теперь передает поисковый запрос и категорию в каталог проблем.
- `ProblemsPage` фильтрует проблемы по категории и поисковому запросу, добавлено пустое состояние.
- `ProblemDetailPage` доработан: чекбоксы шагов, прогресс выполнения, блоки документов, сроков, адресатов, частых ошибок, сохранение в моковом режиме.
- Добавлен микро-тест «Проверьте себя» для темы «Потерял паспорт».
- Добавлен экран `LearningProgressPage`.
- В `ProfilePage` добавлены переключатель «Режим обучения», достижения и переход к обучению.
- Моковые данные расширены: детали проблемы, детали законов, вопросы теста, статистика обучения, прогресс категорий, достижения.
- Рабочее приложение осталось на Flet/Python без backend, PostgreSQL, WebView, React/Vite и npm-зависимостей.

### Какие файлы затронуты

- `src/main.py`
- `src/data/mock_data.py`
- `src/components/layout.py`
- `src/pages/home_page.py`
- `src/pages/problems_page.py`
- `src/pages/problem_detail_page.py`
- `src/pages/profile_page.py`
- `src/pages/legal_updates_page.py`
- `src/pages/law_detail_page.py`
- `src/pages/learning_progress_page.py`
- `docs/PROJECT_STATUS.md`
- `docs/TASKS.md`
- `docs/CHANGELOG.md`
- `docs/LEARNING_MODULE.md`
- `docs/APP_SCREENS.md`

### Результат проверки

- Команда `python -m compileall src` без активации окружения не сработала, потому что глобальная команда `python` отсутствует в системе.
- Выполнено: `PATH="$PWD/.venv/bin:$PATH" python -m compileall src`.
- Выполнена runtime-проверка создания всех основных Flet-экранов.
- Выполнено: `PATH="$PWD/.venv/bin:$PATH" flet run src/main.py`.
- Выполнено: `PATH="$PWD/.venv/bin:$PATH" flet run -w src/main.py --host 127.0.0.1 -p 8550`.
- Проверено: `curl -I http://127.0.0.1:8550` вернул `HTTP/1.1 200 OK`.
- В браузере проверены маршруты `/`, `/problems`, `/problem-detail`, `/situation-detail`, `/legal-updates`, `/law-detail`, `/profile`, `/learning`, `/admin`.

## 2026-05-13

### Что изменено

- Доработан desktop/web-визуал Flet-приложения по reference-скриншотам: верхняя навигация, футер, светлый фон, карточки, сетки, чипы и основные состояния.
- Обновлены основные экраны: Главная, Каталог проблем, Карточка проблемы, Мои ситуации, Мои документы, Закон-апдейты и Профиль.
- Добавлена общая desktop-оболочка `src/components/layout.py`.
- Исправлена нижняя мобильная навигация: подписи больше не переносятся в две строки.
- Исправлены точечные визуальные дефекты: широкий поиск в каталоге, подрезанные статусы документов, наложение заглушки на фото профиля.
- Backend, база данных, WebView, React/Vite и npm-зависимости в рабочее приложение не добавлялись.

### Какие файлы затронуты

- `src/main.py`
- `src/theme/app_theme.py`
- `src/components/layout.py`
- `src/components/bottom_nav.py`
- `src/components/buttons.py`
- `src/components/cards.py`
- `src/data/mock_data.py`
- `src/pages/home_page.py`
- `src/pages/problems_page.py`
- `src/pages/problem_detail_page.py`
- `src/pages/situations_page.py`
- `src/pages/documents_page.py`
- `src/pages/legal_updates_page.py`
- `src/pages/profile_page.py`
- `docs/PROJECT_STATUS.md`
- `docs/TASKS.md`
- `docs/CHANGELOG.md`

### Результат проверки

- Выполнено: `.venv/bin/python -m compileall src`.
- Выполнена runtime-проверка создания controls для ключевых экранов.
- Выполнено: `PATH="$PWD/.venv/bin:$PATH" flet run src/main.py`.
- Выполнено: `PATH="$PWD/.venv/bin:$PATH" flet run -w src/main.py --host 127.0.0.1 -p 8550`.
- Проверено: `curl -I http://127.0.0.1:8550` возвращает `HTTP/1.1 200 OK`.
- Внешний вид проверен скриншотами в браузере на `1536x1200` и `390x844`.

## 2026-05-13

### Что изменено

- Исправлен пустой стартовый экран Flet-приложения.
- Начальный экран теперь рендерится прямым вызовом `route_change()` после настройки `page.on_route_change`.
- Убран несовместимый параметр `surface_tint_color` из `NavigationBar`.
- Кнопки переведены с deprecated `ElevatedButton`/`OutlinedButton`/`TextButton` на `Button`.
- Установлен и добавлен в зависимости `flet-web==0.85.0`.
- В `requirements.txt` и `pyproject.toml` зафиксированы `flet-cli==0.85.0`, `flet-desktop==0.85.0`, `flet-web==0.85.0`.

### Какие файлы затронуты

- `src/main.py`
- `src/components/bottom_nav.py`
- `src/components/buttons.py`
- `requirements.txt`
- `pyproject.toml`
- `docs/PROJECT_STATUS.md`
- `docs/TASKS.md`
- `docs/CHANGELOG.md`

### Результат проверки

- Выполнено: `.venv/bin/python -m compileall src`.
- Выполнена runtime-проверка сборки 11 экранов.
- Выполнено: `PATH="$PWD/.venv/bin:$PATH" flet run src/main.py`.
- Выполнено: `PATH="$PWD/.venv/bin:$PATH" flet run -w src/main.py --host 127.0.0.1 -p 8550`.
- Проверено: `curl -I http://127.0.0.1:8550` вернул `HTTP/1.1 200 OK`.

## 2026-05-13

### Что изменено

- React/Vite-макет `Web app design for Belpomoshch` проанализирован как визуальный reference.
- Основной интерфейс переписан на Flet/Python: фон, карточки, chip-фильтры, нижняя навигация, списки, детальные страницы и профиль.
- Добавлены недостающие Flet-страницы для закон-апдейтов, детальной ситуации и моковой админ-панели.
- Моковые данные расширены под reference-макет.
- Навигация переведена на маршруты Flet через `on_route_change` и асинхронный `push_route`.
- Backend, PostgreSQL, WebView, React, Vite, JSX, CSS и npm-зависимости в рабочее приложение не добавлялись.

### Какие файлы затронуты

- `src/main.py`
- `src/theme/app_theme.py`
- `src/data/mock_data.py`
- `src/components/cards.py`
- `src/components/buttons.py`
- `src/components/bottom_nav.py`
- `src/components/app_bar.py`
- `src/pages/home_page.py`
- `src/pages/problems_page.py`
- `src/pages/problem_detail_page.py`
- `src/pages/situations_page.py`
- `src/pages/situation_detail_page.py`
- `src/pages/documents_page.py`
- `src/pages/notifications_page.py`
- `src/pages/legal_updates_page.py`
- `src/pages/profile_page.py`
- `src/pages/admin_page.py`
- `docs/PROJECT_STATUS.md`
- `docs/TASKS.md`
- `docs/CHANGELOG.md`

### Результат проверки

- Выполнено: `.venv/bin/python -m compileall src`.
- Выполнена runtime-проверка сборки 11 экранов через импорт и создание Flet controls.
- Выполнено: `PATH="$PWD/.venv/bin:$PATH" flet run src/main.py`.
- Приложение запустилось без traceback; процесс остановлен вручную через `Ctrl+C`.

## 2026-05-13

### Что изменено

- Создана документационная основа проекта.
- Добавлены правила для AI-агентов.
- Описаны контекст проекта, MVP, экраны, дизайн-система, архитектура, моковые данные, обучающий модуль, задачи, статус, решения и workflow Codex.
- Обновлен `README.md`.

### Какие файлы затронуты

- `AGENTS.md`
- `README.md`
- `docs/PROJECT_CONTEXT.md`
- `docs/MVP_SCOPE.md`
- `docs/APP_SCREENS.md`
- `docs/DESIGN_SYSTEM.md`
- `docs/FIGMA_TRANSFER_GUIDE.md`
- `docs/ARCHITECTURE.md`
- `docs/DATA_MODEL_DRAFT.md`
- `docs/MOCK_DATA_SPEC.md`
- `docs/LEARNING_MODULE.md`
- `docs/TASKS.md`
- `docs/PROJECT_STATUS.md`
- `docs/DECISIONS.md`
- `docs/CHANGELOG.md`
- `docs/CODEX_WORKFLOW.md`

### Результат проверки

- Markdown-файлы созданы.
- Код приложения не изменялся.
- Требование не добавлять backend, базу данных и авторизацию соблюдено.
