# Журнал изменений

## 2026-06-13 (импорт публикационного контента 2022-2026)

### Что изменено

- `data/import/content_news_calendar_2022_2026.json` — нормализован и импортирован пакет новостей: исправлен `batch_meta.category_id`, удалены дубли тегов.
- `data/import/content_law_updates_2022_2026.json` — нормализован и импортирован пакет закон-апдейтов: `source.id` приведены к формату `src-*`.
- `data/import/content_extremist_materials_2022_2026.json` — записи переведены в `published` после структурной проверки, чтобы раздел отображался на сайте.
- `scripts/normalize_content_batch.py` — добавлены нормализация `batch_meta.category_id`, дедупликация тегов новостей и приведение `law_update.source.id` к `src-*`.
- `scripts/import_content_batches.py` — идемпотентность новостей исправлена с `sourceUrl` на пару `title + sourceUrl`, чтобы разные статьи с одним официальным источником не склеивались.
- `src/backend/migrations/0020_expand_publication_content_columns.sql` — расширены поля публикаций в MySQL: `articles.summary/body_html/gallery/tags`, `law_updates.description/body_html/source_url`, `extremist_entries.short_description/media_urls/attachment_urls/filters_json`.
- `docs/PROJECT_STATUS.md`, `docs/TASKS.md` — зафиксирован результат публикационного импорта.

### Результат проверки

- `scripts/validate_content_batch.py` для трёх новых файлов — ✅ 0 ошибок, 0 предупреждений.
- `backend.scripts.migrate` с локальным XAMPP MySQL URL `root` без пароля — ✅ применена миграция `0020`.
- `scripts/import_content_batches.py --dry-run` — ✅ 88 новостей к созданию, 32 к обновлению, 80 закон-апдейтов к обновлению, 60 записей экстремистского раздела к обновлению.
- `scripts/import_content_batches.py` — ✅ импорт выполнен.
- Контроль БД: `articles` published — 120, `law_updates` — 80, `extremist_entries` published — 60, сумма seed-просмотров — 121620.
- TestClient: `/api/articles?kind=news` — 200 и 120 записей; `/api/law-updates` — 200 и 80 записей; `/api/extremist-entries` — 200 и 60 записей.
- `.venv/bin/python -m compileall src scripts/validate_content_batch.py scripts/normalize_content_batch.py scripts/import_content_batches.py` — ✅ без ошибок.

## 2026-06-13 (публикационные промпты для новостей, закон-апдейтов и экстремистских материалов)

### Что изменено

- `docs/CONTENT_PUBLICATION_RESEARCH_PROMPTS.md` — добавлен отдельный пакет из трёх больших промптов для ChatGPT/Deep Research: новости, закон-апдейты и экстремистские материалы за 2022-2026 годы.
- `docs/CONTENT_PUBLICATION_RESEARCH_PROMPTS.md` — промпты требуют официальный источник, полноценный `bodyHtml`, краткий `summary` для карточки, несколько официальных media URL, `status: "published"` и `views_seed` для новостей.
- `scripts/import_content_batches.py` — новости, импортированные через content-batch, теперь получают автора `Тестовый редактор`.
- `scripts/validate_content_batch.py` — валидатор допускает `registry`, `news`, `explanation` и статусы `draft`/`published` для записей раздела «Экстремистские материалы».
- `data/import/README.md`, `docs/CONTENT_PROMPTS.md` — уточнены правила публикации юридически чувствительного раздела: `published` допускается только при прямом официальном `source_url` и нейтральном безопасном описании.

### Результат проверки

- `.venv/bin/python -m compileall scripts/validate_content_batch.py scripts/import_content_batches.py` — ✅ без ошибок.

## 2026-06-13 (добавление проблем и сценариев в «Мои ситуации»)

### Что изменено

- `reactvitemaket/src/app/pages.tsx` — карточка проблемы теперь подбирает связанный жизненный сценарий по названию и категории; если план уже создан, кнопка открывает существующую ситуацию, если нет — добавляет её в «Мои ситуации». Если подходящий сценарий не найден, пользователь переводится в каталог сценариев с выбранной категорией.
- `reactvitemaket/src/app/pages.tsx` — добавлен явный статус «уже добавлено в „Мои ситуации“» / «найден подходящий сценарий» на детальной странице проблемы.
- `reactvitemaket/src/app/pages.tsx`, `reactvitemaket/src/app/components/extra-screens.tsx` — CTA-кнопки добавления плана и избранного на mobile приведены к единому стилю: нормальная высота, скругление, иконки, readable-текст без сплющивания.
- `reactvitemaket/src/app/components/extra-screens.tsx` — на детальной странице сценария кнопка «Создать мою ситуацию» открывает уже существующую ситуацию, если сценарий ранее добавлен.

### Результат проверки

- `.venv/bin/python -m compileall src scripts/import_institutions.py` — ✅ без ошибок.
- `cd reactvitemaket && pnpm build` — ✅ без ошибок; остался стандартный warning Vite о крупном JS-chunk.

## 2026-06-13 (полный импорт учреждений и подбор по адресам)

### Что изменено

- `src/backend/models.py`, `src/backend/schemas.py` — расширена сущность `authorities`: внешний id, район, населённый пункт, email, услуги, теги, связи со сценариями/категориями, source URL, дата проверки, confidence и active-флаг.
- `src/backend/migrations/0019_authority_import_fields.sql` — добавлена миграция для расширенного справочника учреждений.
- `scripts/import_institutions.py` — добавлен идемпотентный импортёр JSON-файлов `data/import/*institutions*.json`; поддерживает `institutions[]` и старый `items[]`, `rejected_items` не импортирует.
- `data/import/*institutions*.json` — подключены JSON-файлы с подтверждёнными учреждениями Минска и областей Беларуси.
- `reactvitemaket/src/app/services/institutions.ts` — улучшен подбор учреждений: нормализация `г. Минск`/`Минск`, район/город/область, несколько адресов, подбор по категории сценария и типам учреждений.
- `reactvitemaket/src/app/components/extra-screens.tsx` — в детальной странице сценария и пользовательской ситуации показываются учреждения из общего справочника по адресу пользователя.
- `reactvitemaket/src/app/pages.tsx` — детальная карточка проблемы получила динамический блок учреждений по адресам профиля.
- `reactvitemaket/src/app/components/authorities-editor.tsx` — редактор учреждений дополнен типом, районом, населённым пунктом, email и сайтом.
- `scripts/check.sh`, `docs/TASKS.md`, `docs/PROJECT_STATUS.md` — обновлены под миграцию `0019` и новый статус этапа «Госучреждения».

### Результат проверки

- `.venv/bin/python -m compileall src scripts/import_institutions.py` — ✅ без ошибок.
- `cd reactvitemaket && pnpm build` — ✅ без ошибок; остался стандартный warning Vite о крупном JS-chunk.
- `PYTHONPATH=src .venv/bin/python -m backend.scripts.migrate` с XAMPP MySQL URL `root` без пароля — ✅ применены миграции `0001`–`0019`.
- `scripts/import_institutions.py --dry-run` — ✅ 1566 записей к созданию, 0 пропусков.
- `scripts/import_institutions.py` — ✅ импортировано 1566 учреждений.
- Повторный `--dry-run` — ✅ 0 новых, 1566 обновляемых, то есть импорт идемпотентный.
- TestClient `GET /api/authorities` — ✅ 200, 1566 записей.
- `cd reactvitemaket && pnpm exec tsc --noEmit` — не выполнено: в frontend-зависимостях не установлен `tsc`.

## 2026-06-13 (фиксация следующих задач по учреждениям и контенту)

### Что изменено

- `docs/TASKS.md` — зафиксированы новые TODO после проверки web-версии: учреждения должны переноситься в «Мои ситуации», подбор должен динамически реагировать на основной адрес профиля, сценарии из каталога должны быть видны в админке, новости/статьи должны получить полноценные detail-страницы.
- `docs/INSTITUTIONS_RESEARCH_PROMPT.md` — добавлен отдельный deep-research промпт для сбора базы учреждений Республики Беларусь по официальным источникам в JSON-формате.

### Результат проверки

- Документационный шаг, код приложения не менялся.

## 2026-06-12 (Теги контента и безопасность профиля)

### Что изменено

- **Справочник тегов** — добавлена backend-сущность `content_tags`, миграция `0018_content_tags.sql`, публичный endpoint `/api/content-tags` и защищённый CRUD `/api/admin/content-tags` для редактора/администратора.
- **Редактор контента** — произвольный ввод тегов заменён на выбор из утверждённого списка; неизвестные теги дополнительно отклоняются backend-валидацией при создании/редактировании публикаций.
- **Админ-панель** — добавлен раздел «Теги»: создание, редактирование названия/описания/цвета, включение/отключение и удаление тегов.
- **Профиль пользователя** — добавлено быстрое редактирование имени через карандаш на карточке профиля.
- **Безопасность профиля** — добавлен блок «Безопасность»: смена email с подтверждением текущим паролем и смена пароля через старый пароль + два ввода нового пароля.
- **Роли в React store** — проверки редактора/администратора приведены к новым значениям `content_editor` / `platform_admin` с сохранением совместимости со старыми `editor` / `admin`.

### Результат проверки

- `.venv/bin/python -m compileall src` — ✅ без ошибок.
- `cd reactvitemaket && pnpm build` — ✅ без ошибок; остался только стандартный warning Vite о крупном JS-chunk.

## 2026-06-11 (Гость — лендинг, read-only доступ, показ пароля)

### Что изменено

- **Лендинг (`WelcomePage`)** — убрана верхняя панель (лого / `DataModeBadge` «Мок-данные» / «Каталог» / «Войти»); добавлен safe-area отступ сверху (`pt-[calc(env(safe-area-inset-top)+1.5rem)]`); в hero «Посмотреть каталог» → «Войти»; секция «Популярные направления» заменена на блок «Каталог помощи и новости» с кнопками «Открыть каталог» (→ /catalog) и «Новости» (→ /news). Удалён неиспользуемый импорт `DataModeBadge`.
- **Доступ гостя** — гость смотрит каталог и новости **read-only** (route-guard НЕ ограничивает навигацию; действия, требующие аккаунт, по-прежнему гейтятся guest-guard модалкой). `OnboardingGate` оставляет только редирект `/` → `/welcome`.
- **Mobile-навигация (`MobileNav`)** — роле-зависимая правая группа: гость видит `Новости` (а не `Ситуации`, которым нужен аккаунт), залогиненный — `Ситуации`. Левая группа, ИИ-кнопка и `Профиль` — у всех.
- **Mobile-хедер (`MobileBrandBar`)** — у гостя вместо настроек/уведомлений показывается кнопка «Войти» (быстрый путь к регистрации при просмотре).
- **Onboarding** — добавлен safe-area отступ сверху.
- **Показ пароля** — новый компонент `PasswordInput` с кнопкой-глазиком (Eye/EyeOff): на входе (`LoginPage`) и регистрации (`RegisterPage`, оба поля) можно посмотреть введённый пароль. Тогглы независимы по полям.

### Результат проверки

- Mobile preview (375px): чистый лендинг (без верхней панели, safe-area сверху, «Создать аккаунт» + «Войти», кнопки «Открыть каталог»/«Новости»); гость свободно открывает `/catalog` и `/news` (read-only); нижнее меню гостя = `Главная`/`Каталог`/`Новости`/`Профиль` + ИИ-кнопка; в хедере «Войти». Залогиненный — `Ситуации` вместо `Новости`, настройки/колокольчик без изменений. Показ пароля: на регистрации 2 независимых глазика (поле «Пароль» → text, «Повтор» остаётся скрытым), на входе — 1. Консоль чистая (кроме pre-existing предупреждения о вложенных `<button>` в `NewsCard`).

## 2026-06-11 (Мои ситуации — фиксы и mobile-доводка)

### Что изменено

- **Баг добавления ситуации** — `reactvitemaket/src/app/data/store.tsx`, `data/types.ts`: `createSituation` больше не подменяет локальный `id` серверным (раньше открытая `/situations/<local-id>` ломалась на «не найдена», когда приходил ответ бэкенда). Локальный id стабилен, серверный хранится в `UserSituation.backendId`; новый `mergeSituations` дедуплицирует по `scenarioId` (без дублей при загрузке), `deleteSituation` использует `backendId`.
- **Быстрый доступ к ситуациям (mobile)** — `App.tsx`: в нижнем меню добавлена вкладка «Ситуации» (вместо «Новости», которые остаются на главной плиткой и в «Важное для вас»).
- **Ближайшее учреждение по основному адресу** — `components/extra-screens.tsx`: подбор учреждений идёт по основному адресу профиля (`addresses.find(isPrimary)`), а не по legacy city/region; несовпавшие больше не выкидываются (раздел не пустой), ближайшие помечаются «рядом». `data/mock.ts`: учреждениям проставлены `city`/`region` (Минск), чтобы matching работал.
- **Гейтинг выполнения плана** — `components/extra-screens.tsx`: в просмотре сценария задачи read-only (маркеры-точки/замок вместо псевдо-чекбоксов) + подсказка «Отмечать можно после добавления в „Мои ситуации“»; при добавленной ситуации — ссылка «Перейти к выполнению». Отметка задач — только в `MySituationDetail`.
- **Кнопки на mobile** — `components/extra-screens.tsx`: ряд «избранное + Создать мою ситуацию» теперь во всю ширину и в стилистике сайта (звезда h-12 rounded-2xl, основная кнопка `flex-1`), больше не сплющивается.

### Результат проверки

- Mobile preview (375px, citizen): создание ситуации «Рождение ребёнка» → страница не ломается, ситуация в списке без дублей; вкладка «Ситуации» в навигации; «Куда обращаться» → МФЦ г. Минск с бейджем «рядом · В вашем городе (Минск)»; подсказка-гейтинг и кнопки — ОК; консоль без ошибок.

## 2026-06-10 (Аватар профиля — редактор в стиле Telegram)

### Что изменено

- `src/backend/migrations/0017_user_avatar.sql`, `src/backend/models.py` — у пользователя добавлена колонка `avatar_url`.
- `src/backend/api/user.py` — `POST /api/user/avatar` (multipart) с валидацией формата (magic-bytes JPG/PNG/WEBP → 415) и размера (8 МБ → 413); сохраняет файл в `data/uploads/avatars/<uid>/<token>.<ext>`, затирая прежний; `DELETE /api/user/avatar`; `avatar_url` добавлен в `UserProfileOut`.
- `reactvitemaket/src/app/components/avatar-cropper.tsx` — **новый** редактор: круглая обрезка, перетаскивание (pointer), зум (слайдер + колесо + pinch), экспорт квадрата 512×512 в WebP/JPEG через `<canvas>`. Адаптив desktop/tablet/mobile через `ResizeObserver`.
- `reactvitemaket/src/app/pages.tsx` — `ProfileAvatar`: выбор файла → валидация (jpg/jpeg/png/webp, размер) → открытие кропера → загрузка обрезанного фото; аватар теперь круглый (`rounded-full`).
- `reactvitemaket/src/app/services/api.ts` — методы `uploadUserAvatar` / `deleteUserAvatar`.
- `reactvitemaket/src/app/data/store.tsx`, `data/adapters.ts`, `data/types.ts` — действия `uploadAvatar` / `removeAvatar`; маппинг `avatar_url` → абсолютный URL; аватар теперь хранится на бэке и синхронизируется между устройствами (раньше был local-only base64).

Доработка (отображение + контекстное меню):

- `reactvitemaket/src/app/components/belp-ui.tsx` — **новый** примитив `UserAvatarCircle` (фото или инициал на градиенте), единый для хедера/меню/профиля.
- `reactvitemaket/src/app/App.tsx` — аватар текущего пользователя теперь виден в `HeaderUserMenu` (хедер на desktop) и в `DesktopSidebar` (меню на tablet).
- `reactvitemaket/src/app/pages.tsx` — клик по аватару в профиле открывает контекстное меню «Выбрать новое фото» / «Удалить фото» (вместо прямого file-picker); удаление через `removeAvatar`.

### Результат проверки

- Backend E2E (curl): валидный PNG → ✅ 200 + отдаётся по `/uploads/...`; текстовый файл → ✅ 415; 9 МБ → ✅ 413; `DELETE` → ✅ 204 (файл и ссылка очищены).
- Frontend (Vite preview): кропер открывается по выбору файла, зум слайдером меняет масштаб (0 = «вписать»), `Сохранить` грузит WebP-кроп → аватар обновляется и отображается круглым; mobile (375px) и desktop — ✅; консоль без ошибок.
- Отображение/меню (Vite preview): аватар в хедере (desktop ≥1200) и в сайдбаре-меню (tablet) — ✅; клик по аватару в профиле открывает меню «Выбрать новое фото» / «Удалить фото» — ✅.

---

## 2026-06-09 (Экстремистские материалы — детальные карточки)

### Что изменено

- `src/backend/api/extremist.py` — добавлен публичный endpoint `/api/extremist-entries/{entry_id}` для детального просмотра только опубликованных записей.
- `src/backend/api/admin.py` — добавлен admin endpoint `/api/admin/extremist-entries/{entry_id}` для просмотра черновиков редактором/администратором.
- `reactvitemaket/src/app/services/api.ts` — добавлены методы получения одной публичной и admin-записи.
- `reactvitemaket/src/app/data/store.tsx` — `authSession` открыт для страниц, чтобы редакторский список и detail обновлялись сразу после появления backend-токена.
- `reactvitemaket/src/app/routes.tsx`, `reactvitemaket/src/app/App.tsx` — добавлен маршрут `/extremist/:id`; служебный раздел скрывается из нижней навигации и для вложенного маршрута.
- `reactvitemaket/src/app/pages.tsx` — карточки раздела «Экстремистские материалы» теперь открывают внутреннюю подробную страницу с источником, датами, статусом проверки, типами материалов, медиа и вложениями.

### Результат проверки

- `cd reactvitemaket && pnpm build` — ✅ без ошибок.
- `.venv/bin/python -m compileall src scripts/import_content_batches.py scripts/normalize_content_batch.py scripts/validate_content_batch.py` — ✅ без ошибок.
- FastAPI TestClient: публичный список `/api/extremist-entries` — ✅ 200; публичный detail для `draft` — ✅ 404; admin detail с ролью editor — ✅ 200.

---

## 2026-06-09 (Контент — нормализация и импорт JSON-батчей)

### Что изменено

- `scripts/normalize_content_batch.py` — добавлен нормализатор JSON-батчей: исправляет типовые ошибки LLM-вывода, нормализует `official_sources_used`, восстанавливает `sourceIds` по официальным URL, заполняет пустые `media_notes`, переименовывает файл с двойной точкой и переносит новости без официального источника в `rejected_items`.
- `scripts/validate_content_batch.py` — валидатор теперь принимает новые официальные `source_id`, если они явно описаны в `official_sources_used`.
- `scripts/import_content_batches.py` — добавлен идемпотентный импортёр `content_*_2022_2026.json` в backend SQLite: проблемы, сценарии, стадии, шаги, зависимости, документы, источники, новости, закон-апдейты и записи чувствительного реестра.
- `data/import/content_*_2022_2026.json` — все 11 файлов нормализованы и приведены к валидному формату; `content_extremist_materials_2022_2026..json` переименован в `content_extremist_materials_2022_2026.json`.
- `reactvitemaket/src/app/data/mock.ts` — список официальных источников дополнен Минздравом, ЕРИП, ЕГР, НЦЭС, 115.бел, Белтехосмотром, порталом Президента и Совмином.
- `reactvitemaket/src/app/pages.tsx` — лента новостей теперь сопоставляет источник по домену `sourceUrl`, чтобы импортированные backend-материалы попадали в фильтры официальных источников.

### Результат импорта

- Импортировано 11 content-батчей.
- Backend DB после импорта: `problems` — 110, `scenarios` — 47, `articles` — 65, `law_updates` — 61, `extremist_entries` — 60, `documents` — 122.
- Public API: `/api/problems` — 102, `/api/scenarios` — 46, `/api/articles?kind=news` — 65, `/api/law-updates` — 61.
- `/api/extremist-entries` отдаёт 0 публичных записей, потому что импортированные записи оставлены в `draft` до ручной проверки.

### Результат проверки

- `.venv/bin/python scripts/validate_content_batch.py data/import/content_*_2022_2026.json` — ✅ все файлы без ошибок; остались только предупреждения по объёму и новым источникам.
- `.venv/bin/python scripts/import_content_batches.py --dry-run` — ✅ без ошибок.
- `.venv/bin/python scripts/import_content_batches.py` — ✅ импорт выполнен.
- `.venv/bin/python -m compileall src scripts/import_content_batches.py scripts/normalize_content_batch.py scripts/validate_content_batch.py` — ✅ без ошибок.
- `cd reactvitemaket && pnpm build` — ✅ без ошибок.

---

## 2026-06-09 (Контент — рабочие промпты по категориям)

### Что изменено

- `docs/CONTENT_GENERATION_PROMPTS_BY_CATEGORY.md` — добавлен практический пакет промптов для генерации реальных JSON-пачек контента: общая неизменяемая часть и отдельные большие промпты по категориям `documents`, `family`, `work`, `business`, `housing`, `taxes`, `health`, `auto`.
- `docs/CONTENT_GENERATION_PROMPTS_BY_CATEGORY.md` — добавлены отдельные промпты для общего календаря новостей, общего пакета закон-апдейтов и юридически осторожного реестра «Экстремистские материалы».
- `docs/CONTENT_GENERATION_PROMPTS_BY_CATEGORY.md` — зафиксирован процесс: включать поиск/Deep Research, брать только официальные источники, сохранять ответы в `data/import/content_*_2022_2026.json`, затем прогонять через `scripts/validate_content_batch.py`.

### Примечание

- Это не импорт данных и не генерация контента внутри проекта. Документ нужен, чтобы пользователь мог отправлять категории в ChatGPT и получать фактические JSON-пачки для последующей проверки.

---

## 2026-06-09 (Контент — валидатор JSON-батчей 2022-2026)

### Что изменено

- `scripts/validate_content_batch.py` — добавлен локальный валидатор будущих файлов `content_*_2022_2026.json` без зависимости от `jsonschema`.
- `scripts/validate_content_batch.py` — проверяет общий batch-контракт, обязательные массивы, `batch_meta`, даты в периоде `2022-01-01` — `2026-06-08`, официальные `source_id`, категории, HTML-тело новостей/закон-апдейтов, media URL и `filters_json`.
- `scripts/validate_content_batch.py` — для юридически чувствительного раздела «Экстремистские материалы» требует `status: "draft"`, официальный `https://` источник и не допускает прямые ссылки в кратком описании.
- `data/import/README.md` — описаны новые content-батчи, команды проверки и отличие структурной валидации от ручной проверки официальных источников.
- `docs/PROJECT_STATUS.md`, `docs/TASKS.md` — обновлён статус P11: валидатор готов, backend-импорт остаётся следующим шагом после проверки источников.

### Результат проверки

- `.venv/bin/python -m py_compile scripts/validate_content_batch.py` — ✅ без ошибок.
- `.venv/bin/python scripts/validate_content_batch.py --help` — ✅ справка выводится.
- `.venv/bin/python scripts/validate_content_batch.py /tmp/content_documents_2022_2026.json` — ✅ структура проходит, недобор записей выводится как предупреждение.

---

## 2026-06-08 (Контент — промпты, источники и медиа для чувствительного раздела)

### Что изменено

- `docs/CONTENT_PROMPTS.md` — переписан пакет детальных research-промптов для генерации JSON-контента по всем категориям, проблемам, жизненным сценариям, новостям, закон-апдейтам и экстремистским материалам за период 2022-2026.
- `reactvitemaket/src/app/pages.tsx` — кнопка «Все источники» в `/news` теперь открывает полный список официальных источников внутри страницы с поиском, фильтрацией и выбором приоритетного источника.
- `src/backend/api/extremist.py` — добавлен публичный read-only endpoint `/api/extremist-entries` для опубликованных записей.
- `src/backend/models.py`, `src/backend/schemas.py`, `src/backend/api/admin.py`, `src/backend/migrations/0015_extremist_media.sql` — для записей «Экстремистские материалы» добавлены `cover_url`, `media_urls`, `attachment_urls` и сохранение через admin API.
- `src/backend/models.py`, `src/backend/schemas.py`, `src/backend/migrations/0016_law_update_body_html.sql`, `reactvitemaket/src/app/components/law-editor.tsx`, `reactvitemaket/src/app/data/adapters.ts`, `reactvitemaket/src/app/data/types.ts`, `reactvitemaket/src/app/pages.tsx` — закон-апдейты получили поле `body_html/bodyHtml`, редакторское поле HTML-статьи и отображение полноценного текста на детальной странице.
- `reactvitemaket/src/app/services/api.ts`, `reactvitemaket/src/app/data/types.ts`, `reactvitemaket/src/app/pages.tsx` — frontend-форма `/extremist` теперь поддерживает загрузку файлов и вставку URL для обложки, медиа и вложений.
- `src/backend/api/articles.py` — общий upload редакторских медиа разрешает PDF-вложения.

### Результат проверки

- `cd reactvitemaket && pnpm build` — ✅ без ошибок.
- `.venv/bin/python -m compileall src` — ✅ без ошибок.
- FastAPI TestClient: `/api/health` и `/api/extremist-entries` — ✅ отвечают 200.
- FastAPI TestClient: `/api/law-updates` — ✅ отвечает 200 после миграции `0016`.

### Примечание

- Мигратор SQLite сейчас использует `DEFAULT_DB_PATH`, даже если передать временный `BELPOMOSHNIK_DATABASE_URL`; при проверке миграция `0015` была применена к рабочей dev-базе. Данные не удалялись, таблица пересобирается с сохранением старых общих полей.

---

## 2026-06-08 (Новости — добавлена категория «Экстремистский контент»)

### Что изменено

- `reactvitemaket/src/app/pages.tsx` — на странице `/news` в ряд фильтров «Все / Новости / Закон-апдейт» добавлена кнопка «Реестр» с переходом в `/extremist`.
- `reactvitemaket/src/app/pages.tsx` — `/extremist` теперь доступен для просмотра всем ролям; добавление записей по-прежнему доступно только редактору и администратору.
- `reactvitemaket/src/app/pages.tsx` — mobile-лента новостей теперь растягивает карточки на всю ширину контейнера, а на широком mobile viewport переходит в аккуратную 2-колоночную сетку.

### Результат проверки

- `pnpm build` в `reactvitemaket/` — ✅ без ошибок.
- `.venv/bin/python -m compileall src` — ✅ без ошибок.

---

## 2026-06-08 (Mobile — восстановлен fade-gradient у bottom nav)

### Что изменено

- `reactvitemaket/src/app/App.tsx` — старый fade-слой над tab-bar заменён на устойчивый `MobileBottomFade`, который покрывает нижнюю nav-зону целиком и плавно растворяет контент под floating bottom nav.

### Результат проверки

- `pnpm build` в `reactvitemaket/` — ✅ без ошибок.
- `.venv/bin/python -m compileall src` — ✅ без ошибок.

---

## 2026-06-08 (WebView/LAN — исправлен ложный баннер недоступности API)

### Что изменено

- `reactvitemaket/src/app/services/api.ts` — API URL теперь корректно подстраивается под текущий LAN-host frontend: если `.env` указывает на `127.0.0.1`, а приложение открыто на телефоне через `http://<IP>:8560`, запросы уходят на `http://<IP>:8060`.
- `src/backend/app.py` — dev-CORS больше не привязан к одному старому LAN-IP и разрешает локальные private-network origins (`10.*`, `172.16-31.*`, `192.168.*`) для WebView/Vite-разработки.
- `reactvitemaket/.env.example` — пример переведён на `VITE_API_BASE_URL=auto`.

### Результат проверки

- `pnpm build` в `reactvitemaket/` — ✅ без ошибок.
- `.venv/bin/python -m compileall src` — ✅ без ошибок.
- FastAPI TestClient для `Origin: http://172.20.10.3:8560` — ✅ отдаёт `access-control-allow-origin`.

---

## 2026-06-07 (React/WebView — P4–P10 закрыты: профиль, адреса, заметки, a11y, push, ЖКХ/налоги summary, честная админка)

### Что изменено

- `src/backend/models.py` — добавлена `UserNote` (text, category, reminder_at, done) с relationship на `User`.
- `src/backend/migrations/0014_user_notes.sql` — новая таблица `user_notes` с индексами по user_id / done / reminder_at.
- `src/backend/schemas.py` — Pydantic v2 схемы `UserNoteCreate / UserNoteUpdate / UserNoteOut` и константа `USER_NOTE_CATEGORIES`.
- `src/backend/api/user.py` — CRUD `/api/user/notes` (GET, POST, PUT, DELETE) с валидацией категории и ISO-даты; модель и relationship подключены.
- `reactvitemaket/src/app/services/api.ts` — добавлены методы `getUserNotes / createUserNote / updateUserNote / deleteUserNote`.
- `reactvitemaket/src/app/data/adapters.ts` — `adaptUserNote` + `userNotePayload` (text/category/reminder_at/done, reminder_at приводится к yyyy-mm-dd).
- `reactvitemaket/src/app/data/store.tsx` — `addNote / updateNote / toggleNote / removeNote` теперь синхронизируются с backend; добавлен fetch-effect после JWT-входа.
- `reactvitemaket/src/app/services/institutions.ts` — новая `matchInstitutionsForAddresses(institutions, addresses[])` возвращает по группе учреждений на каждый адрес, дедуплицирует внутри группы, сортирует по релевантности.
- `reactvitemaket/src/app/services/a11y.ts` (новый) — `applyAccessibilitySettings` ставит реальный `font-size: 18px` и инжектирует high-contrast стили; `isNative()` детектит Capacitor/Flet/WebView; `Notification.permission` API для push; `isBiometricAvailable()` возвращает true только в native-оболочке.
- `reactvitemaket/src/app/App.tsx` — корневой effect применяет a11y к DOM при изменении настроек; `MobileHome` получил карточку «Мои заметки» рядом с «Мои ситуации».
- `reactvitemaket/src/app/pages.tsx` — `FinanceBody` получил 3-card summary (ближайший / просрочки / сумма месяца) на основе реальных utilityAccounts и taxes.
- `reactvitemaket/src/app/components/extra-screens.tsx` — SettingsPage: push-row использует `Notification.requestPermission` со статус-pill и кнопкой «Тест» при granted; Face/Touch ID строка показывается только в native-оболочке.
- `reactvitemaket/src/app/components/desktop.tsx` — `AdminPanel`: убраны синтетические `SAMPLE_ADMIN_STATS / SAMPLE_ADMIN_ROWS / SAMPLE_TOP_MATERIALS` и псевдо-рандомные просмотры; честный пустой state при отсутствии реальных данных.
- `docs/PROJECT_STATUS.md` — обновлены статусы P4–P10.

### Результат проверки

- `pnpm build` — ✅ без ошибок.
- `python -m compileall src` — ✅ без ошибок.
- Backend: UserNote + миграция 0014 применятся через `backend.bootstrap` (idempotent).
- P4 frontend-sync: заметки пользователя догружаются при JWT-входе, создание/обновление/удаление синхронизируются с `/api/user/notes` при наличии токена; local fallback остаётся рабочим.

---

## 2026-06-07 (React/WebView P3 — welcome, login и register)

### Что изменено

- `reactvitemaket/src/app/pages.tsx` — `/welcome` расширен до полноценной входной страницы: понятное позиционирование продукта, блок личного плана, разделение «Проблема / Жизненный сценарий / Моя ситуация», направления помощи и шаги работы.
- `reactvitemaket/src/app/pages.tsx` — фон `/welcome` растянут на всю страницу, декоративные слои больше не выглядят случайно обрезанными на desktop.
- `reactvitemaket/src/app/pages.tsx` — `/login` и `/register` получили desktop/tablet split-layout: слева смысловой блок с преимуществами, справа рабочая форма; mobile-композиция сохранена компактной.
- `docs/REACT_WEBVIEW_FINALIZATION_PLAN.md`, `docs/TASKS.md`, `docs/PROJECT_STATUS.md` — обновлён статус P3.

### Результат проверки

- `pnpm build` в `reactvitemaket/` — ✅ без ошибок.
- Browser check `/welcome` — ✅ новый входной экран отображается без error overlay.
- Browser check `/login` — ✅ форма входа и информационный desktop-блок отображаются с первого открытия.
- Browser check `/register` — ✅ форма регистрации и информационный desktop-блок отображаются с первого открытия.

---

## 2026-06-07 (React/WebView P2 — каталог проблем и жизненных сценариев)

### Что изменено

- `reactvitemaket/src/app/pages.tsx` — общий `/catalog` стал каталогом помощи с режимами «Все», «Проблемы» и «Жизненные сценарии».
- `reactvitemaket/src/app/pages.tsx` — добавлена обработка query-параметров `q`, `category` и `type`; старый маршрут `/scenarios` открывает каталог сразу в режиме жизненных сценариев.
- `reactvitemaket/src/app/App.tsx` — переходы с главной по категориям «Семья», «Работа», «Здоровье» теперь ведут в каталог с выбранным фильтром.
- `reactvitemaket/src/app/App.tsx`, `reactvitemaket/src/app/components/desktop.tsx`, `reactvitemaket/src/app/components/content-editor.tsx`, `reactvitemaket/src/app/components/extra-screens.tsx` — уточнены формулировки: проблема, жизненный сценарий и моя ситуация больше не смешиваются в ключевых местах интерфейса.
- `docs/REACT_WEBVIEW_FINALIZATION_PLAN.md`, `docs/TASKS.md`, `docs/PROJECT_STATUS.md` — обновлён статус P2.

### Результат проверки

- `pnpm build` в `reactvitemaket/` — ✅ без ошибок.
- Browser check `/catalog` — ✅ видны режимы «Все», «Проблемы», «Жизненные сценарии» и карточки обоих типов.
- Browser check `/catalog?category=family&type=all` — ✅ фильтр категории применяется из URL.
- Browser check `/scenarios` — ✅ открывается режим жизненных сценариев без карточек проблем.
- Browser check `/catalog?type=problem` — ✅ открывается режим проблем без карточек сценариев.

---

## 2026-06-07 (WebView-shell P1 — загрузка, ошибки сети и ориентация)

### Что изменено

- `src/mobile_webview.py` — старый технический экран подключения заменён на нативные пользовательские состояния: ввод адреса приложения, «Загрузка приложения», «Нет подключения к интернету» и «Сервис временно недоступен».
- `src/mobile_webview.py` — добавлена кнопка «Попробовать снова», которая повторно проверяет подключение и перезагружает WebView.
- `src/mobile_webview.py` — технические сообщения `React/Vite/WebView`, чеклист запуска и debug-тест скрыты из пользовательского UI; debug-тест доступен только через `BELPOMOSHNIK_WEBVIEW_DEBUG=1`.
- `src/mobile_webview.py` — добавлена нативная блокировка портретной ориентации через `set_allowed_device_orientations` только для iOS/Android phone viewport.
- `docs/REACT_WEBVIEW_FINALIZATION_PLAN.md`, `docs/TASKS.md`, `docs/PROJECT_STATUS.md`, `docs/DECISIONS.md` — обновлён статус P1.

### Результат проверки

- `.venv/bin/python -m compileall src` — ✅ без ошибок.
- Ручная проверка на реальном телефоне ещё требуется: offline, server-error, retry и портретная ориентация.

---

## 2026-06-07 (React/WebView — план финальной доводки и P0-стабилизация)

### Что изменено

- `docs/REACT_WEBVIEW_FINALIZATION_PLAN.md` — добавлен актуальный рабочий план после полного переноса UI на React/Vite и выделения Flet в WebView-оболочку.
- `AGENTS.md` — добавлено правило читать новый план перед задачами по React/WebView-доводке.
- `docs/TASKS.md` — добавлен этап 22 с приоритетами P0-P12: критичные маршруты, WebView-состояния, профиль, адреса, источники, настройки, админ-аналитика, контент и проверка.
- `docs/PROJECT_STATUS.md` — обновлён активный курс проекта на React/Vite + FastAPI + WebView-shell.
- `docs/DECISIONS.md` — зафиксировано архитектурное решение: React остаётся основным UI, Flet используется только как тонкая WebView-оболочка.
- `reactvitemaket/src/app/pages.tsx` — карточки закон-апдейтов в «Новостях» теперь открывают `/law-detail/:id`; внутри «Новостей» добавлен переход к реестру официальных источников.
- `reactvitemaket/src/app/App.tsx` — отдельный пункт «Источники» убран из desktop header/sidebar, чтобы реестр источников открывался через «Новости».

### Результат проверки

- `pnpm build` в `reactvitemaket/` — ✅ без ошибок.
- Browser check `http://127.0.0.1:8560/settings` — ✅ настройки отображаются с первого открытия.
- Browser check `http://127.0.0.1:8560/news` — ✅ вход в «Официальные источники» виден внутри раздела, отдельного пункта «Источники» в header нет.
- Browser click по закон-апдейту — ✅ переход на `/law-detail/law-4`, детальная страница показывает блок «Что изменилось».

---

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
