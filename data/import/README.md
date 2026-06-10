# data/import/

Папка для ручного импорта контента в «Белпомощник».

## Текущие ручные import-файлы

Эти файлы используются для обычного локального наполнения справочников и
каталогов:

| Файл | Промпт | Содержимое |
|------|--------|------------|
| `regions.json` | 1 | регионы/районы РБ (справочник, опционально) |
| `institutions.json` | 2 | госучреждения (имя, адрес, контакты) |
| `problems.json` | 3 | каталог проблем + пошаговые планы |
| `scenarios.json` | 4 | многоэтапные сценарии |
| `news.json` | 5 | новости / закон-апдейты / реестр |

Формат: чистый UTF-8 JSON-массив (`[ ... ]`), без markdown-обёрток.

Когда файлы готовы — напиши: «импортируй данные из data/import».

## Большие content-батчи 2022-2026

Для массового наполнения по `docs/CONTENT_PROMPTS.md` ожидаются отдельные
JSON-объекты:

| Файл | Содержимое |
|------|------------|
| `content_documents_2022_2026.json` | документы, проблемы, сценарии, новости и закон-апдейты категории `documents` |
| `content_family_2022_2026.json` | категория `family` |
| `content_work_2022_2026.json` | категория `work` |
| `content_business_2022_2026.json` | категория `business` |
| `content_housing_2022_2026.json` | категория `housing` |
| `content_taxes_2022_2026.json` | категория `taxes` |
| `content_health_2022_2026.json` | категория `health` |
| `content_auto_2022_2026.json` | категория `auto` |
| `content_news_calendar_2022_2026.json` | календарь новостей за 2022-2026 |
| `content_law_updates_2022_2026.json` | общий пакет закон-апдейтов |
| `content_extremist_materials_2022_2026.json` | юридически чувствительный реестр, только `draft` |

Перед импортом обязательно проверить файлы:

```bash
.venv/bin/python scripts/validate_content_batch.py data/import/content_documents_2022_2026.json
```

Проверить сразу все content-батчи:

```bash
.venv/bin/python scripts/validate_content_batch.py data/import/content_*_2022_2026.json
```

Жёстко требовать целевое число записей из research-контракта:

```bash
.venv/bin/python scripts/validate_content_batch.py --strict-counts data/import/content_*_2022_2026.json
```

Важно: валидатор проверяет структуру, даты, источники, категории и безопасный
режим для чувствительных записей. Он не заменяет ручную проверку фактов по
официальным источникам.
