#!/usr/bin/env python3
"""Validate Belpomoshnik content import batches.

The script intentionally uses only the Python standard library: it is a
lightweight gate before generated JSON goes into the project import pipeline.
It validates the batch contract reconstructed in docs/CONTENT_PROMPTS.md and
the deep research report supplied for the 2022-2026 content generation pass.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]

PERIOD_FROM = date(2022, 1, 1)
PERIOD_TO = date(2026, 6, 8)
TODAY = date.today()

ROOT_KEYS = {
    "batch_meta",
    "official_sources_used",
    "problems",
    "scenarios",
    "news_articles",
    "law_updates",
    "extremist_entries",
    "source_candidates",
    "rejected_items",
}

CATEGORY_IDS = {
    "documents",
    "family",
    "work",
    "business",
    "housing",
    "taxes",
    "health",
    "auto",
}

PROJECT_SOURCE_IDS = {
    "source-pravo",
    "source-portal-gov",
    "source-mintrud",
    "source-nalog",
    "source-minjust",
    "source-mvd",
    "source-gibdd",
    "source-court",
    "source-nbki",
}

EXTREMIST_SOURCE_IDS = {
    "source-pravo",
    "source-mvd",
    "source-minjust",
    "source-court",
}

SOURCE_CANDIDATE_TYPES = {
    "law",
    "government_portal",
    "ministry",
    "tax",
    "registry",
    "court",
}

DIFFICULTIES = {"Простая", "Средняя", "Сложная"}
EXTREMIST_CATEGORIES = {"registry"}
EXTREMIST_CONTENT_TYPES = {
    "social",
    "channels",
    "media",
    "persons",
    "organizations",
    "music",
    "other",
}

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
NEWS_ID_RE = re.compile(r"^news-[a-z0-9]+(?:-[a-z0-9]+)*$")
LAW_ID_RE = re.compile(r"^law-[a-z0-9]+(?:-[a-z0-9]+)*$")
SRC_ID_RE = re.compile(r"^src-[a-z0-9]+(?:-[a-z0-9]+)*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

CATEGORY_FILE_RE = re.compile(
    r"^content_(documents|family|work|business|housing|taxes|health|auto)_2022_2026\.json$"
)

SPECIAL_FILES = {
    "content_news_calendar_2022_2026.json": {
        "kind": "news_calendar",
        "category_ids": {"news_calendar", "news", "all"},
        "expected_non_empty": {"news_articles"},
        "targets": {"news_articles": 120},
    },
    "content_law_updates_2022_2026.json": {
        "kind": "law_updates",
        "category_ids": {"law_updates", "all"},
        "expected_non_empty": {"law_updates"},
        "targets": {"law_updates": 80},
    },
    "content_extremist_materials_2022_2026.json": {
        "kind": "extremist",
        "category_ids": {"extremist", "extremist_materials", "all"},
        "expected_non_empty": {"extremist_entries"},
        "targets": {"extremist_entries": 60},
    },
}

CATEGORY_TARGETS = {
    "problems": 12,
    "scenarios": 5,
    "news_articles": 18,
    "law_updates": 12,
}

ALLOWED_PROBLEM_KEYS = {
    "id",
    "title",
    "category",
    "shortDescription",
    "whatToDoNow",
    "steps",
    "documents",
    "deadlines",
    "institutions",
    "mistakes",
    "sourceIds",
    "sources",
}

ALLOWED_SCENARIO_KEYS = {
    "id",
    "title",
    "category",
    "shortDescription",
    "longDescription",
    "forWhom",
    "estimatedTime",
    "difficulty",
    "stages",
    "documents",
    "institutions",
    "sources",
    "relatedIds",
}

ALLOWED_NEWS_KEYS = {
    "id",
    "kind",
    "title",
    "summary",
    "bodyHtml",
    "cover",
    "video",
    "gallery",
    "tags",
    "category",
    "source",
    "sourceUrl",
    "sourceIds",
    "status",
    "date",
    "views_seed",
    "media_notes",
}

ALLOWED_LAW_KEYS = {
    "id",
    "category",
    "title",
    "summary",
    "bodyHtml",
    "whoAffected",
    "whatChanged",
    "whatToDo",
    "effectiveDate",
    "source",
    "sourceIds",
    "priority",
    "matchesProfile",
    "media",
}

ALLOWED_EXTREMIST_KEYS = {
    "title",
    "category",
    "source_url",
    "source_name",
    "included_at",
    "last_checked_at",
    "short_description",
    "cover_url",
    "media_urls",
    "attachment_urls",
    "filters_json",
    "status",
    "verification_notes",
}


@dataclass(frozen=True)
class Issue:
    file: str
    path: str
    message: str


class DuplicateKeyError(ValueError):
    pass


class ValidationContext:
    def __init__(self, file_path: Path, strict_counts: bool = False) -> None:
        self.file_path = file_path
        self.strict_counts = strict_counts
        self.errors: list[Issue] = []
        self.warnings: list[Issue] = []
        self.profile = detect_profile(file_path.name)
        self.allowed_source_ids: set[str] = set(PROJECT_SOURCE_IDS)

    def error(self, path: str, message: str) -> None:
        self.errors.append(Issue(str(self.file_path), path, message))

    def warn(self, path: str, message: str) -> None:
        self.warnings.append(Issue(str(self.file_path), path, message))

    def count_issue(self, path: str, message: str) -> None:
        if self.strict_counts:
            self.error(path, message)
        else:
            self.warn(path, message)


def detect_profile(filename: str) -> dict[str, Any]:
    category_match = CATEGORY_FILE_RE.match(filename)
    if category_match:
        category = category_match.group(1)
        return {
            "kind": "category",
            "category": category,
            "category_ids": {category},
            "expected_non_empty": set(CATEGORY_TARGETS),
            "targets": CATEGORY_TARGETS,
        }
    if filename in SPECIAL_FILES:
        return SPECIAL_FILES[filename]
    return {
        "kind": "generic",
        "category": None,
        "category_ids": set(),
        "expected_non_empty": set(),
        "targets": {},
    }


def duplicate_guard_object_pairs_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    for key, value in pairs:
        if key in obj:
            raise DuplicateKeyError(f"duplicate key {key!r}")
        obj[key] = value
    return obj


def load_json(ctx: ValidationContext) -> Any | None:
    try:
        text = ctx.file_path.read_text(encoding="utf-8")
    except OSError as exc:
        ctx.error("$", f"Не удалось прочитать файл: {exc}")
        return None

    if text.lstrip().startswith("```"):
        ctx.error("$", "Файл содержит markdown-обертку. Нужен чистый JSON-объект.")
        return None

    try:
        return json.loads(text, object_pairs_hook=duplicate_guard_object_pairs_hook)
    except DuplicateKeyError as exc:
        ctx.error("$", f"В JSON есть дублирующийся ключ: {exc}")
    except json.JSONDecodeError as exc:
        ctx.error("$", f"Некорректный JSON: {exc.msg} (строка {exc.lineno}, колонка {exc.colno})")
    return None


def is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def is_https_url(value: Any) -> bool:
    return isinstance(value, str) and value.startswith("https://") and " " not in value


def is_url_or_empty(value: Any) -> bool:
    return value == "" or is_https_url(value)


def parse_date(value: Any) -> date | None:
    if not isinstance(value, str) or not DATE_RE.match(value):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def require_keys(ctx: ValidationContext, obj: Any, path: str, keys: set[str]) -> bool:
    if not isinstance(obj, dict):
        ctx.error(path, "Ожидался JSON-объект.")
        return False
    for key in sorted(keys):
        if key not in obj:
            ctx.error(path, f"Нет обязательного поля `{key}`.")
    return True


def disallow_extra_keys(ctx: ValidationContext, obj: dict[str, Any], path: str, allowed: set[str]) -> None:
    for key in sorted(set(obj) - allowed):
        ctx.error(f"{path}.{key}", f"Лишнее поле `{key}` не входит в контракт импорта.")


def expect_string(ctx: ValidationContext, obj: dict[str, Any], path: str, key: str) -> str | None:
    value = obj.get(key)
    if not is_non_empty_string(value):
        ctx.error(f"{path}.{key}", f"`{key}` должно быть непустой строкой.")
        return None
    return value.strip()


def expect_bool(ctx: ValidationContext, obj: dict[str, Any], path: str, key: str) -> bool | None:
    value = obj.get(key)
    if not isinstance(value, bool):
        ctx.error(f"{path}.{key}", f"`{key}` должно быть boolean.")
        return None
    return value


def expect_array(ctx: ValidationContext, obj: dict[str, Any], path: str, key: str) -> list[Any]:
    value = obj.get(key)
    if not isinstance(value, list):
        ctx.error(f"{path}.{key}", f"`{key}` должно быть массивом.")
        return []
    return value


def validate_date_field(
    ctx: ValidationContext,
    obj: dict[str, Any],
    path: str,
    key: str,
    *,
    period: bool = False,
    no_future: bool = False,
    nullable: bool = False,
) -> date | None:
    value = obj.get(key)
    if nullable and value is None:
        return None
    parsed = parse_date(value)
    if parsed is None:
        ctx.error(f"{path}.{key}", f"`{key}` должно быть датой в формате YYYY-MM-DD.")
        return None
    if period and not (PERIOD_FROM <= parsed <= PERIOD_TO):
        ctx.error(
            f"{path}.{key}",
            f"`{key}` должно быть в периоде {PERIOD_FROM.isoformat()} - {PERIOD_TO.isoformat()}.",
        )
    if no_future and parsed > TODAY:
        ctx.error(f"{path}.{key}", f"`{key}` не может быть позже текущей даты {TODAY.isoformat()}.")
    return parsed


def validate_string_list(
    ctx: ValidationContext,
    values: Any,
    path: str,
    *,
    min_items: int = 0,
    max_items: int | None = None,
) -> list[str]:
    if not isinstance(values, list):
        ctx.error(path, "Ожидался массив строк.")
        return []
    if len(values) < min_items:
        ctx.error(path, f"Минимум элементов: {min_items}.")
    if max_items is not None and len(values) > max_items:
        ctx.error(path, f"Максимум элементов: {max_items}.")
    result: list[str] = []
    for index, item in enumerate(values):
        if not is_non_empty_string(item):
            ctx.error(f"{path}[{index}]", "Элемент должен быть непустой строкой.")
            continue
        result.append(item.strip())
    if len(result) != len(set(result)):
        ctx.error(path, "Массив строк содержит дубликаты.")
    return result


def validate_source_ids(
    ctx: ValidationContext,
    values: Any,
    path: str,
    *,
    allowed: set[str] | None = None,
    min_items: int = 1,
) -> list[str]:
    allowed_ids = allowed or ctx.allowed_source_ids
    ids = validate_string_list(ctx, values, path, min_items=min_items)
    for source_id in ids:
        if source_id not in allowed_ids:
            ctx.error(
                path,
                f"`{source_id}` не входит в разрешенный каталог source_id: {', '.join(sorted(allowed_ids))}.",
            )
    return ids


def validate_source_object(ctx: ValidationContext, obj: Any, path: str) -> None:
    if not require_keys(ctx, obj, path, {"title", "url", "checked_at"}):
        return
    disallow_extra_keys(ctx, obj, path, {"title", "url", "checked_at"})
    expect_string(ctx, obj, path, "title")
    if not is_https_url(obj.get("url")):
        ctx.error(f"{path}.url", "`url` должен быть https:// URL официального источника.")
    validate_date_field(ctx, obj, path, "checked_at", no_future=True)


def validate_official_sources(ctx: ValidationContext, values: Any) -> None:
    if not isinstance(values, list):
        ctx.error("$.official_sources_used", "`official_sources_used` должен быть массивом.")
        return
    seen: set[str] = set()
    allowed = EXTREMIST_SOURCE_IDS if ctx.profile["kind"] == "extremist" else PROJECT_SOURCE_IDS
    for index, item in enumerate(values):
        path = f"$.official_sources_used[{index}]"
        if not require_keys(ctx, item, path, {"source_id", "title", "url", "checked_at"}):
            continue
        disallow_extra_keys(ctx, item, path, {"source_id", "title", "url", "checked_at"})
        source_id = expect_string(ctx, item, path, "source_id")
        if source_id:
            if source_id not in allowed and ctx.profile["kind"] == "extremist":
                ctx.error(
                    f"{path}.source_id",
                    f"`{source_id}` нельзя использовать в этом батче.",
                )
            elif source_id not in allowed and not re.match(r"^source-[a-z0-9]+(?:-[a-z0-9]+)*$", source_id):
                ctx.error(f"{path}.source_id", "`source_id` должен иметь вид `source-kebab-case`.")
            elif source_id not in allowed:
                ctx.warn(
                    f"{path}.source_id",
                    f"`{source_id}` отсутствует в базовом каталоге, но принят как новый официальный источник батча.",
                )
            if source_id in seen:
                ctx.error(f"{path}.source_id", f"Источник `{source_id}` повторяется.")
            seen.add(source_id)
            if ctx.profile["kind"] != "extremist":
                ctx.allowed_source_ids.add(source_id)
        expect_string(ctx, item, path, "title")
        if not is_https_url(item.get("url")):
            ctx.error(f"{path}.url", "`url` должен быть https:// URL.")
        validate_date_field(ctx, item, path, "checked_at", no_future=True)


def validate_batch_meta(ctx: ValidationContext, obj: Any) -> None:
    path = "$.batch_meta"
    required = {
        "project",
        "generated_for",
        "category_id",
        "period_from",
        "period_to",
        "checked_at",
        "requires_human_review",
    }
    if not require_keys(ctx, obj, path, required):
        return
    disallow_extra_keys(ctx, obj, path, required)

    if obj.get("project") != "Белпомощник":
        ctx.error(f"{path}.project", "`project` должен быть `Белпомощник`.")
    if obj.get("generated_for") != "content_import":
        ctx.error(f"{path}.generated_for", "`generated_for` должен быть `content_import`.")

    category_id = expect_string(ctx, obj, path, "category_id")
    allowed_categories = ctx.profile.get("category_ids") or CATEGORY_IDS | {"news_calendar", "news", "law_updates", "extremist", "extremist_materials", "all"}
    if category_id and category_id not in allowed_categories:
        ctx.error(
            f"{path}.category_id",
            f"`category_id` не соответствует имени файла. Допустимо: {', '.join(sorted(allowed_categories))}.",
        )

    period_from = validate_date_field(ctx, obj, path, "period_from")
    period_to = validate_date_field(ctx, obj, path, "period_to")
    if period_from and period_from != PERIOD_FROM:
        ctx.error(f"{path}.period_from", f"`period_from` должен быть {PERIOD_FROM.isoformat()}.")
    if period_to and period_to != PERIOD_TO:
        ctx.error(f"{path}.period_to", f"`period_to` должен быть {PERIOD_TO.isoformat()}.")

    checked_at = validate_date_field(ctx, obj, path, "checked_at", no_future=True)
    if checked_at and checked_at < PERIOD_TO:
        ctx.warn(f"{path}.checked_at", "`checked_at` раньше конца импортного периода.")

    review = expect_bool(ctx, obj, path, "requires_human_review")
    if review is not True:
        ctx.error(f"{path}.requires_human_review", "`requires_human_review` должен быть true.")


def validate_problem(ctx: ValidationContext, obj: Any, path: str) -> str | None:
    required = {
        "id",
        "title",
        "category",
        "shortDescription",
        "whatToDoNow",
        "steps",
        "documents",
        "deadlines",
        "institutions",
        "mistakes",
        "sourceIds",
        "sources",
    }
    if not require_keys(ctx, obj, path, required):
        return None
    disallow_extra_keys(ctx, obj, path, ALLOWED_PROBLEM_KEYS)

    item_id = expect_string(ctx, obj, path, "id")
    if item_id and not SLUG_RE.match(item_id):
        ctx.error(f"{path}.id", "`id` должен быть kebab-case.")
    validate_category(ctx, obj, path)
    expect_string(ctx, obj, path, "title")
    expect_string(ctx, obj, path, "shortDescription")
    validate_string_list(ctx, obj.get("whatToDoNow"), f"{path}.whatToDoNow", min_items=3, max_items=5)
    validate_string_list(ctx, obj.get("documents"), f"{path}.documents")
    validate_string_list(ctx, obj.get("deadlines"), f"{path}.deadlines")
    validate_string_list(ctx, obj.get("institutions"), f"{path}.institutions")
    validate_string_list(ctx, obj.get("mistakes"), f"{path}.mistakes")
    validate_source_ids(ctx, obj.get("sourceIds"), f"{path}.sourceIds")

    steps = expect_array(ctx, obj, path, "steps")
    if not steps:
        ctx.error(f"{path}.steps", "Нужен минимум один шаг.")
    for step_index, step in enumerate(steps):
        step_path = f"{path}.steps[{step_index}]"
        if not require_keys(ctx, step, step_path, {"id", "title"}):
            continue
        disallow_extra_keys(ctx, step, step_path, {"id", "title"})
        step_id = expect_string(ctx, step, step_path, "id")
        if step_id and not SLUG_RE.match(step_id):
            ctx.error(f"{step_path}.id", "`id` шага должен быть kebab-case.")
        expect_string(ctx, step, step_path, "title")

    sources = expect_array(ctx, obj, path, "sources")
    if not sources:
        ctx.error(f"{path}.sources", "Нужен минимум один официальный источник.")
    for source_index, source in enumerate(sources):
        validate_source_object(ctx, source, f"{path}.sources[{source_index}]")
    return item_id


def validate_scenario(ctx: ValidationContext, obj: Any, path: str) -> str | None:
    required = {
        "id",
        "title",
        "category",
        "shortDescription",
        "longDescription",
        "forWhom",
        "estimatedTime",
        "difficulty",
        "stages",
        "documents",
        "institutions",
        "sources",
        "relatedIds",
    }
    if not require_keys(ctx, obj, path, required):
        return None
    disallow_extra_keys(ctx, obj, path, ALLOWED_SCENARIO_KEYS)

    item_id = expect_string(ctx, obj, path, "id")
    if item_id and not SLUG_RE.match(item_id):
        ctx.error(f"{path}.id", "`id` должен быть kebab-case.")
    validate_category(ctx, obj, path)
    for key in ("title", "shortDescription", "longDescription", "forWhom", "estimatedTime"):
        expect_string(ctx, obj, path, key)
    if obj.get("difficulty") not in DIFFICULTIES:
        ctx.error(f"{path}.difficulty", f"`difficulty` должен быть одним из: {', '.join(sorted(DIFFICULTIES))}.")
    validate_string_list(ctx, obj.get("institutions"), f"{path}.institutions")
    validate_string_list(ctx, obj.get("relatedIds"), f"{path}.relatedIds")

    documents = expect_array(ctx, obj, path, "documents")
    for doc_index, doc in enumerate(documents):
        doc_path = f"{path}.documents[{doc_index}]"
        if not require_keys(ctx, doc, doc_path, {"title", "required"}):
            continue
        disallow_extra_keys(ctx, doc, doc_path, {"title", "required"})
        expect_string(ctx, doc, doc_path, "title")
        expect_bool(ctx, doc, doc_path, "required")

    sources = expect_array(ctx, obj, path, "sources")
    if not sources:
        ctx.error(f"{path}.sources", "Нужен минимум один официальный источник.")
    for source_index, source in enumerate(sources):
        validate_source_object(ctx, source, f"{path}.sources[{source_index}]")

    all_task_ids: set[str] = set()
    stages = expect_array(ctx, obj, path, "stages")
    if not stages:
        ctx.error(f"{path}.stages", "Нужен минимум один этап.")
    for stage_index, stage in enumerate(stages):
        stage_path = f"{path}.stages[{stage_index}]"
        if not require_keys(ctx, stage, stage_path, {"id", "title", "tasks"}):
            continue
        disallow_extra_keys(ctx, stage, stage_path, {"id", "title", "tasks"})
        stage_id = expect_string(ctx, stage, stage_path, "id")
        if stage_id and not SLUG_RE.match(stage_id):
            ctx.error(f"{stage_path}.id", "`id` этапа должен быть kebab-case.")
        expect_string(ctx, stage, stage_path, "title")
        tasks = expect_array(ctx, stage, stage_path, "tasks")
        if not tasks:
            ctx.error(f"{stage_path}.tasks", "В этапе нужна минимум одна задача.")
        for task_index, task in enumerate(tasks):
            task_path = f"{stage_path}.tasks[{task_index}]"
            if not require_keys(ctx, task, task_path, {"id", "title", "durationHint", "dueOffsetDays", "blockedBy"}):
                continue
            disallow_extra_keys(ctx, task, task_path, {"id", "title", "durationHint", "dueOffsetDays", "blockedBy"})
            task_id = expect_string(ctx, task, task_path, "id")
            if task_id:
                if not SLUG_RE.match(task_id):
                    ctx.error(f"{task_path}.id", "`id` задачи должен быть kebab-case.")
                if task_id in all_task_ids:
                    ctx.error(f"{task_path}.id", f"Задача `{task_id}` повторяется в сценарии.")
                all_task_ids.add(task_id)
            expect_string(ctx, task, task_path, "title")
            expect_string(ctx, task, task_path, "durationHint")
            due_offset = task.get("dueOffsetDays")
            if due_offset is not None and (not isinstance(due_offset, int) or due_offset < 0):
                ctx.error(f"{task_path}.dueOffsetDays", "`dueOffsetDays` должен быть null или неотрицательным integer.")
            blocked_by = validate_string_list(ctx, task.get("blockedBy"), f"{task_path}.blockedBy")
            for dep_id in blocked_by:
                if not SLUG_RE.match(dep_id):
                    ctx.error(f"{task_path}.blockedBy", f"Зависимость `{dep_id}` должна быть kebab-case.")

    for stage_index, stage in enumerate(stages):
        if not isinstance(stage, dict):
            continue
        for task_index, task in enumerate(stage.get("tasks") or []):
            if not isinstance(task, dict):
                continue
            for dep_id in task.get("blockedBy") or []:
                if isinstance(dep_id, str) and dep_id not in all_task_ids:
                    ctx.error(
                        f"{path}.stages[{stage_index}].tasks[{task_index}].blockedBy",
                        f"Зависимость `{dep_id}` не найдена среди задач сценария.",
                    )
    return item_id


def validate_news(ctx: ValidationContext, obj: Any, path: str) -> str | None:
    required = {
        "id",
        "kind",
        "title",
        "summary",
        "bodyHtml",
        "cover",
        "video",
        "gallery",
        "tags",
        "category",
        "source",
        "sourceUrl",
        "sourceIds",
        "status",
        "date",
        "media_notes",
    }
    if not require_keys(ctx, obj, path, required):
        return None
    disallow_extra_keys(ctx, obj, path, ALLOWED_NEWS_KEYS)

    item_id = expect_string(ctx, obj, path, "id")
    if item_id and not NEWS_ID_RE.match(item_id):
        ctx.error(f"{path}.id", "`id` новости должен начинаться с `news-` и быть kebab-case.")
    if obj.get("kind") != "news":
        ctx.error(f"{path}.kind", "`kind` должен быть `news`.")
    if obj.get("status") != "published":
        ctx.error(f"{path}.status", "`status` новости должен быть `published`.")
    validate_category(ctx, obj, path)
    for key in ("title", "summary", "source", "media_notes"):
        expect_string(ctx, obj, path, key)
    body = expect_string(ctx, obj, path, "bodyHtml")
    if body and "<p>" not in body:
        ctx.error(f"{path}.bodyHtml", "`bodyHtml` новости должен содержать HTML-параграфы `<p>`.")
    if not is_https_url(obj.get("sourceUrl")):
        ctx.error(f"{path}.sourceUrl", "`sourceUrl` должен быть https:// URL официального источника.")
    if not is_url_or_empty(obj.get("cover")):
        ctx.error(f"{path}.cover", "`cover` должен быть пустой строкой или https:// URL.")
    if not is_url_or_empty(obj.get("video")):
        ctx.error(f"{path}.video", "`video` должен быть пустой строкой или https:// URL.")
    validate_url_list(ctx, obj.get("gallery"), f"{path}.gallery")
    validate_string_list(ctx, obj.get("tags"), f"{path}.tags")
    validate_source_ids(ctx, obj.get("sourceIds"), f"{path}.sourceIds")
    validate_date_field(ctx, obj, path, "date", period=True)
    views_seed = obj.get("views_seed", 0)
    if not isinstance(views_seed, int) or views_seed < 0:
        ctx.error(f"{path}.views_seed", "`views_seed` должен быть неотрицательным integer.")
    return item_id


def validate_law_update(ctx: ValidationContext, obj: Any, path: str) -> str | None:
    required = {
        "id",
        "category",
        "title",
        "summary",
        "bodyHtml",
        "whoAffected",
        "whatChanged",
        "whatToDo",
        "effectiveDate",
        "source",
        "sourceIds",
        "priority",
        "matchesProfile",
        "media",
    }
    if not require_keys(ctx, obj, path, required):
        return None
    disallow_extra_keys(ctx, obj, path, ALLOWED_LAW_KEYS)

    item_id = expect_string(ctx, obj, path, "id")
    if item_id and not LAW_ID_RE.match(item_id):
        ctx.error(f"{path}.id", "`id` закон-апдейта должен начинаться с `law-` и быть kebab-case.")
    validate_category(ctx, obj, path)
    for key in ("title", "summary", "bodyHtml", "whoAffected", "whatChanged", "whatToDo"):
        expect_string(ctx, obj, path, key)
    body = obj.get("bodyHtml")
    if isinstance(body, str):
        for title in ("<h3>Что изменилось</h3>", "<h3>Кого это касается</h3>", "<h3>Что сделать</h3>"):
            if title not in body:
                ctx.error(f"{path}.bodyHtml", f"В `bodyHtml` отсутствует обязательный блок `{title}`.")
    validate_date_field(ctx, obj, path, "effectiveDate", period=True)
    validate_source_ids(ctx, obj.get("sourceIds"), f"{path}.sourceIds")
    expect_bool(ctx, obj, path, "priority")
    expect_bool(ctx, obj, path, "matchesProfile")
    validate_law_source(ctx, obj.get("source"), f"{path}.source")
    validate_law_media(ctx, obj.get("media"), f"{path}.media")
    return item_id


def validate_law_source(ctx: ValidationContext, obj: Any, path: str) -> None:
    if not require_keys(ctx, obj, path, {"id", "title", "url", "description", "checkedAt"}):
        return
    disallow_extra_keys(ctx, obj, path, {"id", "title", "url", "description", "checkedAt"})
    source_id = expect_string(ctx, obj, path, "id")
    if source_id and not SRC_ID_RE.match(source_id):
        ctx.error(f"{path}.id", "`id` источника закон-апдейта должен начинаться с `src-`.")
    expect_string(ctx, obj, path, "title")
    expect_string(ctx, obj, path, "description")
    if not is_https_url(obj.get("url")):
        ctx.error(f"{path}.url", "`url` должен быть https:// URL.")
    validate_date_field(ctx, obj, path, "checkedAt", no_future=True)


def validate_law_media(ctx: ValidationContext, obj: Any, path: str) -> None:
    if not require_keys(ctx, obj, path, {"cover_url", "gallery_urls", "attachment_urls"}):
        return
    disallow_extra_keys(ctx, obj, path, {"cover_url", "gallery_urls", "attachment_urls"})
    if not is_url_or_empty(obj.get("cover_url")):
        ctx.error(f"{path}.cover_url", "`cover_url` должен быть пустой строкой или https:// URL.")
    validate_url_list(ctx, obj.get("gallery_urls"), f"{path}.gallery_urls")
    validate_url_list(ctx, obj.get("attachment_urls"), f"{path}.attachment_urls")


def validate_extremist_entry(ctx: ValidationContext, obj: Any, path: str) -> str | None:
    required = {
        "title",
        "category",
        "source_url",
        "source_name",
        "included_at",
        "last_checked_at",
        "short_description",
        "cover_url",
        "media_urls",
        "attachment_urls",
        "filters_json",
        "status",
        "verification_notes",
    }
    if not require_keys(ctx, obj, path, required):
        return None
    disallow_extra_keys(ctx, obj, path, ALLOWED_EXTREMIST_KEYS)

    title = expect_string(ctx, obj, path, "title")
    if obj.get("category") not in EXTREMIST_CATEGORIES:
        ctx.error(f"{path}.category", "`category` для этого батча должен быть `registry`.")
    if obj.get("status") != "draft":
        ctx.error(f"{path}.status", "`status` юридически чувствительной записи должен быть `draft` до ручной проверки.")
    for key in ("source_name", "short_description", "verification_notes"):
        expect_string(ctx, obj, path, key)
    if not is_https_url(obj.get("source_url")):
        ctx.error(f"{path}.source_url", "`source_url` должен быть https:// URL официального источника.")
    if not is_url_or_empty(obj.get("cover_url")):
        ctx.error(f"{path}.cover_url", "`cover_url` должен быть пустой строкой или https:// URL.")
    validate_url_list(ctx, obj.get("media_urls"), f"{path}.media_urls")
    validate_url_list(ctx, obj.get("attachment_urls"), f"{path}.attachment_urls")
    validate_date_field(ctx, obj, path, "included_at", period=True, nullable=True)
    validate_date_field(ctx, obj, path, "last_checked_at", no_future=True)
    validate_filters_json(ctx, obj.get("filters_json"), f"{path}.filters_json")

    description = obj.get("short_description")
    if isinstance(description, str) and re.search(r"https?://|t\.me|telegram|vk\.com|instagram|youtube", description, re.I):
        ctx.error(
            f"{path}.short_description",
            "Описание не должно содержать прямые ссылки или распространение запрещенного материала.",
        )
    return title


def validate_filters_json(ctx: ValidationContext, value: Any, path: str) -> None:
    if not isinstance(value, str):
        ctx.error(path, "`filters_json` должен быть JSON-строкой.")
        return
    try:
        decoded = json.loads(value)
    except json.JSONDecodeError as exc:
        ctx.error(path, f"`filters_json` не декодируется как JSON: {exc.msg}.")
        return
    if not isinstance(decoded, dict):
        ctx.error(path, "`filters_json` после декодирования должен быть объектом.")
        return
    extra_keys = set(decoded) - {"content_types"}
    if extra_keys:
        ctx.error(path, f"В `filters_json` лишние поля: {', '.join(sorted(extra_keys))}.")
    content_types = decoded.get("content_types")
    values = validate_string_list(ctx, content_types, f"{path}.content_types", min_items=1)
    for content_type in values:
        if content_type not in EXTREMIST_CONTENT_TYPES:
            ctx.error(
                f"{path}.content_types",
                f"`{content_type}` не входит в допустимые типы: {', '.join(sorted(EXTREMIST_CONTENT_TYPES))}.",
            )


def validate_url_list(ctx: ValidationContext, values: Any, path: str) -> None:
    if not isinstance(values, list):
        ctx.error(path, "Ожидался массив URL.")
        return
    seen: set[str] = set()
    for index, value in enumerate(values):
        if not is_https_url(value):
            ctx.error(f"{path}[{index}]", "URL должен начинаться с `https://`.")
            continue
        if value in seen:
            ctx.error(f"{path}[{index}]", "URL повторяется.")
        seen.add(value)


def validate_category(ctx: ValidationContext, obj: dict[str, Any], path: str) -> None:
    category = expect_string(ctx, obj, path, "category")
    if not category:
        return
    if category not in CATEGORY_IDS:
        ctx.error(f"{path}.category", f"`category` должен быть одним из: {', '.join(sorted(CATEGORY_IDS))}.")
    expected = ctx.profile.get("category")
    if expected and category != expected:
        ctx.error(f"{path}.category", f"`category` должен совпадать с файлом: `{expected}`.")


def validate_source_candidates(ctx: ValidationContext, values: Any) -> None:
    if not isinstance(values, list):
        ctx.error("$.source_candidates", "`source_candidates` должен быть массивом.")
        return
    required = {"title", "url", "type", "description", "last_checked", "official", "reason_to_add"}
    allowed = required
    for index, item in enumerate(values):
        path = f"$.source_candidates[{index}]"
        if not require_keys(ctx, item, path, required):
            continue
        disallow_extra_keys(ctx, item, path, allowed)
        for key in ("title", "description", "reason_to_add"):
            expect_string(ctx, item, path, key)
        if not is_https_url(item.get("url")):
            ctx.error(f"{path}.url", "`url` должен быть https:// URL.")
        if item.get("type") not in SOURCE_CANDIDATE_TYPES:
            ctx.error(f"{path}.type", f"`type` должен быть одним из: {', '.join(sorted(SOURCE_CANDIDATE_TYPES))}.")
        official = expect_bool(ctx, item, path, "official")
        if official is not True:
            ctx.error(f"{path}.official", "`official` должен быть true.")
        validate_date_field(ctx, item, path, "last_checked", no_future=True)


def validate_rejected_items(ctx: ValidationContext, values: Any) -> None:
    if not isinstance(values, list):
        ctx.error("$.rejected_items", "`rejected_items` должен быть массивом.")
        return
    for index, item in enumerate(values):
        if not isinstance(item, dict):
            ctx.error(f"$.rejected_items[{index}]", "Элемент `rejected_items` должен быть объектом.")


def validate_counts(ctx: ValidationContext, data: dict[str, Any]) -> None:
    profile = ctx.profile
    if profile["kind"] == "generic":
        ctx.warn("$", "Имя файла не распознано как content_*_2022_2026.json; применены только общие проверки.")
        return

    expected_non_empty: set[str] = profile["expected_non_empty"]
    for key in ("problems", "scenarios", "news_articles", "law_updates", "extremist_entries"):
        value = data.get(key)
        if not isinstance(value, list):
            continue
        if expected_non_empty and key not in expected_non_empty and value:
            ctx.error(f"$.{key}", f"Для файла `{ctx.file_path.name}` этот массив должен быть пустым.")

    for key, target in profile["targets"].items():
        value = data.get(key)
        if not isinstance(value, list):
            continue
        if len(value) < target:
            ctx.count_issue(f"$.{key}", f"Ожидаемая нагрузка батча: {target}, сейчас {len(value)}.")
        elif len(value) > target:
            ctx.count_issue(f"$.{key}", f"Ожидаемая нагрузка батча: {target}, сейчас {len(value)}.")


def validate_item_ids(ctx: ValidationContext, ids: list[tuple[str, str]]) -> None:
    seen: dict[str, str] = {}
    for item_id, path in ids:
        if item_id in seen:
            ctx.error(path, f"`id` `{item_id}` уже встречался в {seen[item_id]}.")
        else:
            seen[item_id] = path


def validate_content(ctx: ValidationContext, data: Any) -> None:
    if not require_keys(ctx, data, "$", ROOT_KEYS):
        return
    disallow_extra_keys(ctx, data, "$", ROOT_KEYS)

    for key in ROOT_KEYS:
        if key == "batch_meta":
            continue
        if key in data and not isinstance(data[key], list):
            ctx.error(f"$.{key}", f"`{key}` должен быть массивом.")

    validate_batch_meta(ctx, data.get("batch_meta"))
    validate_official_sources(ctx, data.get("official_sources_used"))
    validate_source_candidates(ctx, data.get("source_candidates"))
    validate_rejected_items(ctx, data.get("rejected_items"))
    validate_counts(ctx, data)

    ids: list[tuple[str, str]] = []
    for index, item in enumerate(data.get("problems") or []):
        item_id = validate_problem(ctx, item, f"$.problems[{index}]")
        if item_id:
            ids.append((item_id, f"$.problems[{index}].id"))
    for index, item in enumerate(data.get("scenarios") or []):
        item_id = validate_scenario(ctx, item, f"$.scenarios[{index}]")
        if item_id:
            ids.append((item_id, f"$.scenarios[{index}].id"))
    for index, item in enumerate(data.get("news_articles") or []):
        item_id = validate_news(ctx, item, f"$.news_articles[{index}]")
        if item_id:
            ids.append((item_id, f"$.news_articles[{index}].id"))
    for index, item in enumerate(data.get("law_updates") or []):
        item_id = validate_law_update(ctx, item, f"$.law_updates[{index}]")
        if item_id:
            ids.append((item_id, f"$.law_updates[{index}].id"))
    for index, item in enumerate(data.get("extremist_entries") or []):
        item_id = validate_extremist_entry(ctx, item, f"$.extremist_entries[{index}]")
        if item_id:
            ids.append((item_id, f"$.extremist_entries[{index}].title"))
    validate_item_ids(ctx, ids)


def validate_file(path: Path, strict_counts: bool = False) -> ValidationContext:
    ctx = ValidationContext(path, strict_counts=strict_counts)
    data = load_json(ctx)
    if data is not None:
        validate_content(ctx, data)
    return ctx


def print_text_report(contexts: list[ValidationContext]) -> None:
    for ctx in contexts:
        rel = ctx.file_path
        try:
            rel = ctx.file_path.relative_to(PROJECT_ROOT)
        except ValueError:
            pass
        status = "OK" if not ctx.errors else "FAIL"
        print(f"{status}: {rel} ({len(ctx.errors)} errors, {len(ctx.warnings)} warnings)")
        for issue in ctx.errors:
            print(f"  ERROR {issue.path}: {issue.message}")
        for issue in ctx.warnings:
            print(f"  WARN  {issue.path}: {issue.message}")


def print_json_report(contexts: list[ValidationContext]) -> None:
    payload = {
        "ok": all(not ctx.errors for ctx in contexts),
        "files": [
            {
                "file": str(ctx.file_path),
                "profile": ctx.profile["kind"],
                "errors": [issue.__dict__ for issue in ctx.errors],
                "warnings": [issue.__dict__ for issue in ctx.warnings],
            }
            for ctx in contexts
        ],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Проверка JSON-батчей content_*_2022_2026.json перед импортом в Белпомощник.",
    )
    parser.add_argument("files", nargs="+", type=Path, help="JSON-файлы для проверки.")
    parser.add_argument(
        "--strict-counts",
        action="store_true",
        help="Считать отклонение от целевого числа записей ошибкой, а не предупреждением.",
    )
    parser.add_argument("--json", action="store_true", help="Вывести машинно-читаемый JSON-отчет.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    contexts = [validate_file(path, strict_counts=args.strict_counts) for path in args.files]
    if args.json:
        print_json_report(contexts)
    else:
        print_text_report(contexts)
    return 0 if all(not ctx.errors for ctx in contexts) else 1


if __name__ == "__main__":
    raise SystemExit(main())
