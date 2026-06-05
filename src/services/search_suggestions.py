"""Google-like local suggestions for global search."""
from __future__ import annotations

from dataclasses import dataclass


POPULAR_QUERIES: tuple[tuple[str, str], ...] = (
    ("Потеря паспорта", "популярный запрос"),
    ("Рождение ребёнка", "жизненный сценарий"),
    ("Открытие ИП", "жизненный сценарий"),
    ("Переезд и регистрация", "жизненный сценарий"),
    ("Добавить паспорт", "документы"),
    ("Срок действия медкнижки", "документы"),
    ("Оплата ЖКХ", "ЖКХ"),
    ("Передать показания ЖКХ", "ЖКХ"),
    ("Налог на имущество", "налоги"),
    ("Учреждение рядом", "учреждения"),
)


@dataclass(frozen=True)
class SearchSuggestion:
    title: str
    source: str
    hint: str = ""


def _normalize(text: str) -> str:
    cleaned = (text or "").lower().replace("ё", "е")
    return " ".join(cleaned.split())


def _add(items: list[SearchSuggestion], seen: set[str], title: str, source: str, hint: str = "") -> None:
    normalized = _normalize(title)
    if not normalized or normalized in seen:
        return
    seen.add(normalized)
    items.append(SearchSuggestion(title=title.strip(), source=source, hint=hint.strip()))


def _score(suggestion: SearchSuggestion, query: str) -> float:
    title = _normalize(suggestion.title)
    hint = _normalize(suggestion.hint)
    source = _normalize(suggestion.source)
    if not query:
        return 0.0
    if title == query:
        return 1.0
    score = 0.0
    if title.startswith(query):
        score += 0.72
    words = title.split()
    if any(word.startswith(query) for word in words):
        score += 0.42
    if query in title:
        score += 0.34
    if query in hint:
        score += 0.16
    if query in source:
        score += 0.10
    return min(score, 1.0)


def build_search_suggestions(
    query: str,
    *,
    problems: list[dict],
    scenarios: list[dict],
    situations: list[dict],
    documents: list[dict],
    laws: list[dict],
    institutions: list[dict],
    limit: int = 10,
) -> list[SearchSuggestion]:
    normalized = _normalize(query)
    if len(normalized) < 2:
        return []

    items: list[SearchSuggestion] = []
    seen: set[str] = set()

    for title, source in POPULAR_QUERIES:
        _add(items, seen, title, source)

    for problem in problems:
        _add(items, seen, problem.get("title", ""), "проблема", problem.get("description", ""))
        _add(items, seen, problem.get("category_name", ""), "категория")

    for scenario in scenarios:
        _add(items, seen, scenario.get("title", ""), "сценарий", scenario.get("short_description") or scenario.get("description", ""))
        _add(items, seen, scenario.get("category", ""), "категория")

    for situation in situations:
        _add(items, seen, situation.get("title", ""), "моя ситуация", situation.get("status", ""))

    for document in documents:
        _add(items, seen, document.get("title", ""), "документ", document.get("type") or document.get("document_type", ""))
        _add(items, seen, document.get("issuer", ""), "организация выдачи")

    for law in laws:
        _add(items, seen, law.get("title", ""), "закон-апдейт", law.get("short") or law.get("description", ""))
        _add(items, seen, law.get("category_name", ""), "категория")

    for institution in institutions:
        _add(items, seen, institution.get("short_name") or institution.get("title", ""), "учреждение", institution.get("address", ""))
        _add(items, seen, institution.get("institution_type", ""), "тип учреждения")
        _add(items, seen, institution.get("city", ""), "населённый пункт")

    scored: list[tuple[float, SearchSuggestion]] = []
    for suggestion in items:
        score = _score(suggestion, normalized)
        if score > 0:
            scored.append((score, suggestion))

    scored.sort(key=lambda item: (-item[0], item[1].title.lower()))
    return [suggestion for _score_value, suggestion in scored[:limit]]
