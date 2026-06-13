"""AI assistant proxy (ТЗ §2, §3).

Keeps the Groq API key server-side: the React client never sees it. A local
keyword intent-router always picks the target section (deterministic, safe);
the LLM only writes the short conversational reply. If the LLM is unavailable
the endpoint still returns a useful canned answer.

Also exposes a second router `/api/admin/assistant/content` for editors
that helps draft/rewrite/summarize publication bodies.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from backend.api.auth import get_current_user_email, require_role
from backend.database import get_db
from backend.models import ExtremistEntry
from backend.service import (
    list_authorities,
    list_published_documents,
    list_published_law_updates,
    list_published_problems,
    list_published_scenarios,
    search_published_news,
)
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/assistant", tags=["assistant"])
admin_router = APIRouter(prefix="/api/admin/assistant", tags=["assistant-admin"])

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

SYSTEM_PROMPT = (
    "Ты — встроенный помощник сайта «Белпомощник» для граждан Беларуси. "
    "Помогаешь сориентироваться по разделам сайта и коротко подсказываешь, где решить вопрос. "
    "Не выдумывай функции, которых нет. Не давай сложных юридических заключений. "
    "Отвечай простым языком, 1–3 предложения, по-русски. "
    "Тебе уже выбран подходящий раздел — сошлись на него естественно, не выводи технические id."
)

CONTENT_SYSTEM_PROMPT = (
    "Ты — редактор белорусского информационного портала «Белпомощник». "
    "Помогаешь редакторам и админам с текстами публикаций: новости, жизненные сценарии, "
    "правовые апдейты. Сохраняй факты; если не уверен — пиши осторожно. "
    "Не выдумывай статьи "
    "законов, номера документов и конкретные суммы, если их не было во входных "
    "данных. Пиши по-русски, грамотно, в официально-публицистическом стиле. "
    "Отвечай строго валидным JSON с полями title, summary, bodyHtml. "
    "bodyHtml — корректный HTML (p, ul/li, strong, em, h3, a). Никакого "
    "<script>, <style>, <iframe> — только безопасный контент. Не используй "
    "Markdown-разметку, не оборачивай ответ в ```json и т.п."
)


@dataclass(frozen=True)
class Section:
    id: str
    title: str
    description: str
    route: str
    keywords: tuple[str, ...]
    requires_auth: bool = False
    min_role: str = "guest"


SECTIONS: tuple[Section, ...] = (
    Section("search", "Поиск", "Поиск по проблемам, сценариям, документам и учреждениям.", "/catalog",
            ("поиск", "найти", "искать", "где найти", "подобрать")),
    Section("problems", "Каталог проблем", "Справочные карточки с планом действий по жизненным проблемам.", "/problems",
            ("проблема", "каталог", "карточка", "паспорт", "потерял", "медкнижка", "развод", "увольнение")),
    Section("scenarios", "Жизненные сценарии", "Готовые маршруты: этапы, задачи, документы, сроки и организации.", "/scenarios",
            ("сценарий", "рождение", "ребенок", "ребёнок", "ип", "переезд", "маршрут", "пошагово")),
    Section("situations", "Мои ситуации", "Личные планы, задачи и прогресс выполнения.", "/situations",
            ("моя ситуация", "мои ситуации", "план", "задача", "прогресс", "отметить", "чек-лист"), requires_auth=True),
    Section("documents", "Документы", "Личные документы, сроки действия, сканы и напоминания.", "/documents",
            ("документ", "паспорт", "скан", "срок действия", "добавить паспорт", "права", "удостоверение"), requires_auth=True),
    Section("finance", "ЖКХ и налоги", "Лицевые счета, показания, оплата ЖКХ и налоговые обязательства.", "/finance",
            ("жкх", "коммуналка", "квитанция", "показания", "лицевой счет", "лицевой счёт", "налог", "налоги", "оплат"), requires_auth=True),
    Section("notifications", "Уведомления", "Напоминания о сроках задач, документов и важных изменениях.", "/notifications",
            ("уведомление", "напоминание", "срок", "дедлайн", "оповещение"), requires_auth=True),
    Section("legal", "Закон-апдейты", "Понятная лента изменений правил, сроков и документов.", "/legal",
            ("закон", "новости", "изменения", "правила", "апдейт", "законодательств")),
    Section("learning", "Обучение", "Короткие тесты, достижения и прогресс по темам.", "/learning",
            ("обучение", "тест", "проверить себя", "достижение")),
    Section("profile", "Профиль", "Личные данные, регион, интересы и роль.", "/profile",
            ("профиль", "личные данные", "регион", "город", "интересы", "аккаунт"), requires_auth=True),
    Section("settings", "Настройки", "Тема, язык, уведомления, приватность.", "/settings",
            ("настройки", "язык", "тема", "тёмная", "темная", "приватность", "контраст"), requires_auth=True),
)

ROLE_RANK = {"guest": 0, "citizen": 1, "editor": 2, "admin": 3}


def _normalize(text: str) -> str:
    return " ".join((text or "").lower().replace("ё", "е").split())


def _score(section: Section, query: str) -> float:
    if not query:
        return 0.0
    title = _normalize(section.title)
    score = 0.0
    if query == title or title in query:
        score += 0.4
    for kw in section.keywords:
        k = _normalize(kw)
        if not k:
            continue
        if query == k:
            score += 0.6
        elif k in query or query in k:
            score += 0.3
    return min(score, 1.0)


def detect_section(query: str) -> tuple[Section, float]:
    normalized = _normalize(query)
    best, best_score = SECTIONS[0], 0.0
    for section in SECTIONS:
        s = _score(section, normalized)
        if s > best_score:
            best, best_score = section, s
    return best, best_score


def _llm_reply(message: str, section: Section, auth_warning: bool) -> str | None:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    context = (
        f"Подходящий раздел: «{section.title}» — {section.description}. "
        + ("Для этого действия пользователю нужен вход или регистрация. " if auth_warning else "")
    )
    try:
        resp = httpx.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "temperature": 0.4,
                "max_tokens": 180,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT + " " + context},
                    {"role": "user", "content": message},
                ],
            },
            timeout=15.0,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        return None


class AssistantRequest(BaseModel):
    message: str
    role: str = "guest"
    is_guest: bool = True


class AssistantSection(BaseModel):
    id: str
    title: str
    description: str
    route: str


class AssistantResponse(BaseModel):
    response_text: str
    section: AssistantSection
    requires_auth_warning: bool
    source: str  # "llm" | "local"


@router.post("", response_model=AssistantResponse)
def ask(payload: AssistantRequest):
    section, _score_value = detect_section(payload.message)
    auth_warning = bool(payload.is_guest and section.requires_auth)

    reply = _llm_reply(payload.message, section, auth_warning)
    source = "llm"
    if not reply:
        source = "local"
        reply = f"Похоже, это раздел «{section.title}». {section.description}"
        if auth_warning:
            reply += " Для личного действия понадобится вход или регистрация."

    return AssistantResponse(
        response_text=reply,
        section=AssistantSection(id=section.id, title=section.title, description=section.description, route=section.route),
        requires_auth_warning=auth_warning,
        source=source,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Admin Content Assistant — помогает редакторам писать/переписывать контент.
# ─────────────────────────────────────────────────────────────────────────────

# Промпт 5: расширенные режимы редакторского AI.
ContentMode = Literal[
    "generate", "rewrite", "expand", "summarize", "translate",
    "headline", "outline", "simplify", "proofread", "fact_check",
    "seo", "social", "neutralize",
]
ContentKind = Literal["news", "scenario", "problem", "law", "guide"]
ContentTone = Literal["official", "simple", "newsworthy", "neutral"]
ContentLength = Literal["short", "medium", "long"]


class ContentAssistSuggestion(BaseModel):
    type: Literal["warning", "improvement", "source_needed", "headline"] = "improvement"
    text: str


class ContentAssistRequest(BaseModel):
    mode: ContentMode
    kind: ContentKind = "news"
    current_title: str = Field(default="", max_length=255)
    current_summary: str = Field(default="", max_length=2000)
    current_body_html: str = Field(default="")
    hint: str = Field(default="", max_length=1000)
    # Промпт 5: тон и длина.
    tone: ContentTone | None = None
    length: ContentLength | None = None
    # Категория / теги / источник — для лучшей подсказки.
    category: str = Field(default="", max_length=120)
    tags: list[str] = Field(default_factory=list)
    audience: str = Field(default="", max_length=200)
    source_label: str = Field(default="", max_length=255)
    source_url: str = Field(default="", max_length=500)


class ContentAssistResponse(BaseModel):
    title: str
    summary: str
    body_html: str
    source: str  # "llm" | "local"
    # Промпт 5: расширенный ответ.
    suggestions: list[ContentAssistSuggestion] = Field(default_factory=list)
    headlines: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    model: str = ""
    disclaimer: str = "AI-черновик требует проверки редактором."


_MODE_PROMPTS = {
    "generate": "Сгенерируй новую публикацию на указанную тему (hint). Пиши содержательно, 3-5 абзацев в bodyHtml.",
    "rewrite": "Перепиши существующий текст, сохранив смысл и факты, но улучшив стиль, ясность и читабельность.",
    "expand": "Расширь существующий текст: добавь детали, контекст, шаги, ссылки на источники. Не выдумывай цифры.",
    "summarize": "Сократи существующий текст до краткого summary (1-2 предложения) и сделай bodyHtml лаконичнее.",
    "translate": "Переведи существующий текст на белорусский язык. Сохрани структуру HTML. Стиль — официально-публицистический.",
    "headline": "Предложи 5 заголовков для этого материала. Помести их в массив headlines. Заголовки — короткие, без кликбейта.",
    "outline": "Сделай структуру материала: основные блоки и пункты. Верни в bodyHtml как ul/li с h3.",
    "simplify": "Объясни материал простым языком для обычного гражданина без юридического образования. Сохрани факты.",
    "proofread": "Исправь стилистические и грамматические ошибки. Не меняй смысла. В suggestions перечисли важные правки.",
    "fact_check": "Не меняй текст. В suggestions перечисли места, где нужны источники, проверка дат, сумм, статей закона.",
    "seo": "Улучши title и summary без кликбейта. Предложи 3-5 тегов в массиве tags.",
    "social": "Сделай короткий анонс материала для соцсетей (1-2 предложения в summary). bodyHtml не меняй.",
    "neutralize": "Убери эмоциональность и оценочные суждения. Сделай тон официально-нейтральным.",
}

_KIND_HINTS = {
    "news": "новость / событие с датой и контекстом",
    "scenario": "жизненный сценарий: этапы, шаги, документы, куда обращаться",
    "problem": "описание проблемы: что делать сейчас, документы, сроки, куда идти",
    "law": "правовое обновление: что изменилось, кого касается, когда вступает в силу",
    "guide": "пошаговое руководство для гражданина",
}

_TONE_LABEL = {
    "official": "официально-публицистический, без эмоций",
    "simple": "простой и понятный обычному гражданину",
    "newsworthy": "новостной, информативный",
    "neutral": "нейтральный, без эмоций",
}

_LENGTH_LABEL = {
    "short": "очень коротко (1-2 абзаца)",
    "medium": "среднего объёма (3-5 абзацев)",
    "long": "подробный материал (6-10 абзацев)",
}


def _strip_dangerous_html(value: str) -> str:
    """Промпт 5: усиленная sanitization для редакторского AI.
    - удаляет опасные теги (script/iframe/style/link/meta/base/form/frameset/object/embed/img)
    - удаляет on*-атрибуты
    - удаляет javascript: / data: в href/src
    """
    if not value:
        return value
    # Парные опасные теги.
    value = re.sub(
        r"<\s*(?:script|iframe|object|embed|style|link|meta|base|form|frame|frameset|img)\b.*?<\s*/\s*\w+\s*>",
        "",
        value,
        flags=re.IGNORECASE | re.DOTALL,
    )
    # Самозакрывающиеся / непарные.
    value = re.sub(
        r"<\s*(?:script|iframe|object|embed|style|link|meta|base|form|frame|frameset|img)\b[^>]*/?>",
        "",
        value,
        flags=re.IGNORECASE,
    )
    # on*-атрибуты (onclick, onload и т.д.).
    value = re.sub(r"\son[a-z]+\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s>]+)", "", value, flags=re.IGNORECASE)
    # javascript: и data: в href/src — выкидываем целиком атрибут.
    value = re.sub(
        r"\s(?:href|src)\s*=\s*(?:\"\s*(?:javascript|data):[^\"]*\"|'\s*(?:javascript|data):[^']*'|(?:javascript|data):[^\s>]+)",
        "",
        value,
        flags=re.IGNORECASE,
    )
    return value


def _local_fallback(req: ContentAssistRequest) -> ContentAssistResponse:
    """Заглушка без GROQ_API_KEY — чтобы UI работал и в офлайне (промпт 5)."""
    title = req.current_title.strip() or "Новая публикация"
    kind_label = _KIND_HINTS.get(req.kind, "публикация")
    body_clean = _strip_dangerous_html(req.current_body_html) or ""

    if req.mode == "generate":
        summary = req.hint.strip()[:200] or f"Краткое описание для {kind_label}."
        body = (
            f"<p>{req.hint.strip() or 'Здесь должно быть описание темы.'}</p>"
            "<h3>Что важно знать</h3>"
            "<ul><li>Основные факты и сроки.</li>"
            "<li>Какие документы понадобятся.</li>"
            "<li>Куда обращаться.</li></ul>"
            "<p><em>Это автоматический черновик. Отредактируйте перед публикацией.</em></p>"
        )
        return ContentAssistResponse(title=title, summary=summary, body_html=body, source="local")
    if req.mode == "summarize":
        summary = (req.current_summary or re.sub(r"<[^>]+>", " ", body_clean)[:150] or "—")[:200]
        return ContentAssistResponse(
            title=title,
            summary=summary,
            body_html=f"<p>{summary}</p><p><em>Краткое содержание. Полный текст требует редактирования.</em></p>",
            source="local",
        )
    if req.mode == "translate":
        body = body_clean or "<p>Нет текста для перевода.</p>"
        return ContentAssistResponse(
            title=title,
            summary=req.current_summary or "—",
            body_html=body + "<p><em>Аўтаматычны пераклад недаступны (GROQ_API_KEY не наладжаны).</em></p>",
            source="local",
        )
    if req.mode == "headline":
        base = title
        return ContentAssistResponse(
            title=title,
            summary=req.current_summary or "—",
            body_html=body_clean,
            source="local",
            headlines=[
                base,
                f"{base}: что нужно знать",
                f"Кратко о теме: {base}",
            ],
        )
    if req.mode == "fact_check":
        return ContentAssistResponse(
            title=title,
            summary=req.current_summary or "—",
            body_html=body_clean,
            source="local",
            suggestions=[
                ContentAssistSuggestion(type="source_needed", text="Проверьте даты и сроки в официальных источниках."),
                ContentAssistSuggestion(type="source_needed", text="Сверьте суммы (тарифы, штрафы, пошлины) с актуальными нормативами."),
                ContentAssistSuggestion(type="source_needed", text="Укажите ссылки на статьи закона / постановления, если они упоминаются."),
                ContentAssistSuggestion(type="warning", text="Не публикуйте без подтверждения юридических формулировок."),
            ],
        )
    if req.mode == "outline":
        return ContentAssistResponse(
            title=title,
            summary=req.current_summary or "—",
            body_html=(
                "<h3>Введение</h3><p>Кратко о теме и зачем материал нужен.</p>"
                "<h3>Основная часть</h3><ul><li>Факт 1</li><li>Факт 2</li><li>Факт 3</li></ul>"
                "<h3>Что делать читателю</h3><ul><li>Шаг 1</li><li>Шаг 2</li></ul>"
                "<h3>Где проверить</h3><p>Официальные источники.</p>"
            ),
            source="local",
            suggestions=[ContentAssistSuggestion(type="improvement", text="Это шаблон-структура. Заполните содержимое перед публикацией.")],
        )
    if req.mode == "seo":
        return ContentAssistResponse(
            title=title,
            summary=(req.current_summary or "")[:160] or "—",
            body_html=body_clean,
            source="local",
            tags=[t for t in [req.category, req.kind] if t][:5],
        )
    # rewrite / expand / simplify / proofread / social / neutralize — без изменений + подсказка
    return ContentAssistResponse(
        title=title,
        summary=req.current_summary or "—",
        body_html=body_clean or "<p>Нет текста. Добавьте содержимое.</p>",
        source="local",
        suggestions=[ContentAssistSuggestion(type="improvement", text="Локальный fallback: AI-провайдер не настроен. Отредактируйте текст вручную.")],
    )


def _llm_assist(req: ContentAssistRequest) -> ContentAssistResponse | None:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    user_prompt = (
        f"Тип публикации: {req.kind} ({_KIND_HINTS.get(req.kind, '')}).\n"
        f"Режим: {req.mode} — {_MODE_PROMPTS.get(req.mode, '')}.\n"
    )
    if req.tone:
        user_prompt += f"Тон: {_TONE_LABEL.get(req.tone, req.tone)}.\n"
    if req.length:
        user_prompt += f"Длина: {_LENGTH_LABEL.get(req.length, req.length)}.\n"
    if req.category:
        user_prompt += f"Категория: {req.category}.\n"
    if req.tags:
        user_prompt += f"Текущие теги: {', '.join(req.tags[:10])}.\n"
    if req.audience:
        user_prompt += f"Аудитория: {req.audience}.\n"
    if req.source_label or req.source_url:
        user_prompt += f"Источник: {req.source_label} {req.source_url}.\n"
    if req.hint:
        user_prompt += f"Дополнительная подсказка от редактора: {req.hint.strip()}\n"
    if req.current_title:
        user_prompt += f"Текущий заголовок: {req.current_title.strip()}\n"
    if req.current_summary:
        user_prompt += f"Текущее краткое описание: {req.current_summary.strip()}\n"
    if req.current_body_html:
        user_prompt += f"Текущий текст (HTML):\n{req.current_body_html.strip()[:3000]}\n"
    user_prompt += (
        '\nОтвет строго JSON: {"title": str, "summary": str, "bodyHtml": str, '
        '"suggestions": [{"type":"warning|improvement|source_needed|headline", "text": str}], '
        '"headlines": [str], "tags": [str]}. '
        "Без markdown-обёрток, без комментариев. Поля suggestions/headlines/tags могут быть пустыми."
    )
    try:
        resp = httpx.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "temperature": 0.5,
                "max_tokens": 1400,
                "messages": [
                    {"role": "system", "content": CONTENT_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
            },
            timeout=25.0,
        )
        resp.raise_for_status()
        text = resp.json()["choices"][0]["message"]["content"].strip()
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            return None
        data = json.loads(match.group(0))
        # Парсим suggestions/headlines/tags безопасно.
        raw_suggestions = data.get("suggestions") or []
        suggestions: list[ContentAssistSuggestion] = []
        if isinstance(raw_suggestions, list):
            for s in raw_suggestions[:10]:
                if isinstance(s, dict):
                    suggestions.append(ContentAssistSuggestion(
                        type=s.get("type") if s.get("type") in ("warning", "improvement", "source_needed", "headline") else "improvement",
                        text=str(s.get("text") or "")[:500],
                    ))
        raw_headlines = data.get("headlines") or []
        headlines = [str(h)[:200] for h in raw_headlines[:5]] if isinstance(raw_headlines, list) else []
        raw_tags = data.get("tags") or []
        tags = [str(t)[:60] for t in raw_tags[:8]] if isinstance(raw_tags, list) else []

        return ContentAssistResponse(
            title=str(data.get("title") or req.current_title or "Без заголовка")[:255],
            summary=str(data.get("summary") or req.current_summary or "")[:2000],
            body_html=_strip_dangerous_html(str(data.get("bodyHtml") or req.current_body_html or "")),
            source="llm",
            suggestions=suggestions,
            headlines=headlines,
            tags=tags,
            model=model,
        )
    except Exception:
        return None


@admin_router.post("/content", response_model=ContentAssistResponse)
def assist_content(
    payload: ContentAssistRequest,
    actor: str = Depends(require_role("content_editor")),
):
    """P12 — ИИ-помощник для контента. Доступ: content_editor+."""
    # Промпт 5: fact_check режим не должен заменять текст вообще.
    if payload.mode == "fact_check":
        # Возвращаем оригинал + suggestions через local-fallback (LLM может попытаться,
        # но если ничего не выдаст — отдадим safe-список вопросов).
        result = _llm_assist(payload)
        if result is None or not result.suggestions:
            result = _local_fallback(payload)
        return result
    result = _llm_assist(payload)
    if result is None:
        result = _local_fallback(payload)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Public RAG chat — `/api/assistant/chat` (citizen+).
# Подтягивает релевантные сущности из БД, отдаёт LLM (или локальный fallback)
# вместе с ghost-промптом. Frontend склеивает пути с window.location.origin.
# ─────────────────────────────────────────────────────────────────────────────

# Промпт 3: исправлен parents[2] → parents[3]. Файл лежит в src/backend/api,
# docs/ — в корне проекта.
_AI_GUIDE_PATH = Path(__file__).resolve().parents[3] / "docs" / "AI_GUIDE.md"
try:
    AI_GUIDE_MD_TEXT = _AI_GUIDE_PATH.read_text(encoding="utf-8")
except FileNotFoundError:
    import logging
    logging.getLogger(__name__).warning("AI_GUIDE.md not found at %s; using minimal fallback prompt", _AI_GUIDE_PATH)
    AI_GUIDE_MD_TEXT = (
        "Ты — встроенный AI-ассистент «Белпомощник». Отвечай по-русски, "
        "кратко. Не выдумывай ссылки и факты. Возвращай только пути вида "
        "`/scenarios/3`. (AI guide file is missing; fall back to minimal rules.)"
    )


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    role: str = "citizen"
    is_guest: bool = False


class ChatLink(BaseModel):
    title: str
    path: str
    kind: str
    snippet: str = ""


class ChatResponse(BaseModel):
    response_text: str
    links: list[ChatLink]
    source: str  # "llm" | "local"


# Cap общей выдачи в system prompt. 12 сущностей × ~80 символов ≈ 1 КБ, укладываемся.
_RAG_TOTAL_CAP = 12


def _tokenize(text: str) -> list[str]:
    return [t for t in re.split(r"[\s,.;:!?()«»\"'`]+", (text or "").lower().replace("ё", "е")) if len(t) > 1]


def _score(text: str, tokens: list[str]) -> int:
    if not text or not tokens:
        return 0
    haystack = text.lower().replace("ё", "е")
    return sum(1 for t in tokens if t in haystack)


def _snippet(value: str, max_len: int = 240) -> str:
    value = re.sub(r"<[^>]+>", " ", value or "").strip()
    return value[:max_len]


def _collect_rag_entities(db: Session, message: str) -> list[dict]:
    """Собирает до _RAG_TOTAL_CAP релевантных сущностей из 7 категорий.

    Простой keyword-score (без эмбеддингов). Score = sum(1 for tok in tokens if
    tok in haystack), где tokens — токены сообщения, haystack — title+summary+description.
    """
    tokens = _tokenize(message)
    if not tokens:
        return []

    candidates: list[dict] = []

    for p in list_published_problems(db):
        text = f"{p.title} {p.short_description or ''} {p.description or ''}"
        s = _score(text, tokens)
        if s > 0:
            candidates.append({
                "kind": "problem", "id": p.id, "title": p.title,
                "path": f"/problem-detail/{p.id}",
                "snippet": _snippet(p.short_description or p.description or ""),
                "score": s,
            })

    for scn in list_published_scenarios(db):
        text = f"{scn.title} {scn.short_description or ''} {scn.description or ''} {scn.target_audience or ''}"
        s = _score(text, tokens)
        if s > 0:
            candidates.append({
                "kind": "scenario", "id": scn.id, "title": scn.title,
                "path": f"/scenarios/{scn.id}",
                "snippet": _snippet(scn.short_description or scn.description or ""),
                "score": s,
            })

    for d in list_published_documents(db):
        text = f"{d.title} {d.description or ''}"
        s = _score(text, tokens)
        if s > 0:
            candidates.append({
                "kind": "document", "id": d.id, "title": d.title,
                "path": "/documents",
                "snippet": _snippet(d.description or ""),
                "score": s,
            })

    for a in list_authorities(db):
        text = f"{a.title} {a.description or ''} {a.type or ''} {a.region or ''} {a.city or ''}"
        s = _score(text, tokens)
        if s > 0:
            candidates.append({
                # Промпт 3: исправлен битый route `/scenarios/{authority_id}` —
                # отдельной публичной страницы у учреждений нет, ведём в каталог.
                "kind": "authority", "id": a.id, "title": a.title,
                "path": "/catalog",
                "snippet": _snippet(a.description or a.address or ""),
                "score": s,
            })

    for law in list_published_law_updates(db):
        text = f"{law.title} {law.description or ''} {law.body_html or ''}"
        s = _score(text, tokens)
        if s > 0:
            candidates.append({
                "kind": "law", "id": law.id, "title": law.title,
                "path": f"/law-detail/{law.id}",
                "snippet": _snippet(law.description or ""),
                "score": s,
            })

    for art in search_published_news(db, message, limit=30):
        text = f"{art.title} {art.summary or ''} {art.body_html or ''}"
        s = _score(text, tokens)
        if s > 0:
            candidates.append({
                "kind": "news", "id": art.id, "title": art.title,
                "path": f"/news?article={art.id}",
                "snippet": _snippet(art.summary or ""),
                "score": s,
            })

    for ex in db.query(ExtremistEntry).filter(ExtremistEntry.status == "published").all():
        text = f"{ex.title} {ex.short_description or ''} {ex.source_name or ''}"
        s = _score(text, tokens)
        if s > 0:
            candidates.append({
                "kind": "extremist", "id": ex.id, "title": ex.title,
                "path": f"/extremist/{ex.id}",
                "snippet": _snippet(ex.short_description or ""),
                "score": s,
            })

    candidates.sort(key=lambda c: c["score"], reverse=True)
    return candidates[:_RAG_TOTAL_CAP]


def _build_system_prompt(entities: list[dict]) -> str:
    """Собирает system-prompt: AI_GUIDE.md + список ENTITIES."""
    if entities:
        lines = "\n".join(
            f"- [{e['kind']}] {e['title']} → {e['path']}"
            + (f" | {e['snippet']}" if e.get("snippet") else "")
            for e in entities
        )
    else:
        lines = "— (ничего подходящего не нашлось; предложи подходящий раздел-каталог)"
    return (
        AI_GUIDE_MD_TEXT
        + "\n\n## Доступные сущности (ENTITIES)\n\n"
        + lines
        + "\n\nОтвет строго JSON: {\"text\": str, \"links\": [str, ...]}. Без markdown-обёрток."
    )


def _llm_chat(message: str, system_prompt: str) -> str | None:
    """Groq-вызов. Возвращает text или None при ошибке/отсутствии ключа."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    try:
        resp = httpx.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "temperature": 0.3,
                "max_tokens": 400,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message},
                ],
            },
            timeout=15.0,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        return None


def _parse_chat_response(text: str, entities: list[dict]) -> tuple[str, list[dict]]:
    """Парсит JSON-ответ LLM. Если парсинг не удался — текст целиком + топ-3
    серверных сущностей как fallback links.
    """
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(0))
            response_text = str(data.get("text") or "").strip()
            raw_links = data.get("links") or []
            if not isinstance(raw_links, list):
                raw_links = []
            # Фильтруем только пути из entities — не даём LLM выдумывать.
            valid_paths = {e["path"] for e in entities}
            links = [p for p in raw_links if isinstance(p, str) and p in valid_paths][:3]
            if response_text or links:
                return response_text, [
                    {
                        "title": e["title"], "path": e["path"], "kind": e["kind"],
                        "snippet": e.get("snippet", ""),
                    }
                    for e in entities
                    if e["path"] in {l for l in links}
                ][:3]
        except (json.JSONDecodeError, AttributeError):
            pass
    # Fallback: текст целиком, ссылки — топ-3 из entities.
    return text, [
        {
            "title": e["title"], "path": e["path"], "kind": e["kind"],
            "snippet": e.get("snippet", ""),
        }
        for e in entities[:3]
    ]


def _local_chat_fallback(message: str, entities: list[dict]) -> tuple[str, list[dict]]:
    """Без GROQ: топ-3 сущности + статичный вводный текст."""
    if not entities:
        return (
            "Я не нашёл подходящего материала в базе знаний. Попробуйте иначе сформулировать вопрос "
            "или откройте каталог помощи — там есть готовые карточки по типовым ситуациям.",
            [],
        )
    top = entities[:3]
    titles = ", ".join(e["title"] for e in top)
    return (
        f"По вашему вопросу нашлось несколько материалов: {titles}. "
        "Откройте подходящий — ниже ссылки. Если ничего не подходит, попробуйте иначе сформулировать.",
        [
            {
                "title": e["title"], "path": e["path"], "kind": e["kind"],
                "snippet": e.get("snippet", ""),
            }
            for e in top
        ],
    )


@router.post("/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    email: str = Depends(get_current_user_email),
    db: Session = Depends(get_db),
):
    """RAG-чат ассистента. Доступ: citizen+ (требуется JWT)."""
    entities = _collect_rag_entities(db, payload.message)
    system_prompt = _build_system_prompt(entities)
    raw = _llm_chat(payload.message, system_prompt)
    source = "llm"
    if raw is None:
        source = "local"
        response_text, links = _local_chat_fallback(payload.message, entities)
    else:
        response_text, links = _parse_chat_response(raw, entities)
        if not links and not response_text:
            # LLM вернул пустой JSON — fallback.
            source = "local"
            response_text, links = _local_chat_fallback(payload.message, entities)
    return ChatResponse(
        response_text=response_text,
        links=[ChatLink(**l) for l in links],
        source=source,
    )


# ─────────────────────────────────────────────────────────────────────────────
# SSE-стриминг: `/api/assistant/chat/stream`
# Поток чанков `data: {"delta": "<text>"}\n\n` + финальный `data: {"links":[...],"source":"..."}\n\n`.
# Если нет LLM → сразу один финальный event с полным текстом (как обычный /chat).
# ─────────────────────────────────────────────────────────────────────────────
from fastapi.responses import StreamingResponse


def _stream_generator(message: str, entities: list[dict], system_prompt: str):
    """Синхронный генератор SSE-событий. FastAPI обернёт в StreamingResponse."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        # Нет LLM — отдаём fallback как одно финальное событие.
        response_text, links = _local_chat_fallback(message, entities)
        payload = json.dumps({"text": response_text, "links": links, "source": "local"}, ensure_ascii=False)
        yield f"data: {payload}\n\n"
        return
    model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    try:
        with httpx.Client(timeout=30.0) as client:
            with client.stream(
                "POST",
                GROQ_URL,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": model,
                    "temperature": 0.3,
                    "max_tokens": 400,
                    "stream": True,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message},
                    ],
                },
            ) as resp:
                resp.raise_for_status()
                full_text = []
                for line in resp.iter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    chunk = line[6:]
                    if chunk.strip() == "[DONE]":
                        break
                    try:
                        data = json.loads(chunk)
                        delta = data["choices"][0].get("delta", {}).get("content", "")
                        if delta:
                            full_text.append(delta)
                            yield f"data: {json.dumps({'delta': delta}, ensure_ascii=False)}\n\n"
                    except (json.JSONDecodeError, KeyError):
                        pass
                # Финальный event: парсим собранный текст, добавляем ссылки.
                combined = "".join(full_text)
                response_text, links = _parse_chat_response(combined, entities)
                payload = json.dumps({"text": response_text, "links": links, "source": "llm"}, ensure_ascii=False)
                yield f"data: {payload}\n\n"
    except Exception as exc:
        response_text, links = _local_chat_fallback(message, entities)
        payload = json.dumps({"text": response_text, "links": links, "source": "local", "error": str(exc)}, ensure_ascii=False)
        yield f"data: {payload}\n\n"


@router.post("/chat/stream")
def chat_stream(
    payload: ChatRequest,
    email: str = Depends(get_current_user_email),
    db: Session = Depends(get_db),
):
    """SSE-стриминг RAG-чата. Каждый чанк = `data: {"delta": "..."}\n\n`.
    Последний чанк = `data: {"text": "...", "links": [...], "source": "..."}\n\n`.
    Доступ: citizen+ (требуется JWT)."""
    entities = _collect_rag_entities(db, payload.message)
    system_prompt = _build_system_prompt(entities)
    return StreamingResponse(
        _stream_generator(payload.message, entities, system_prompt),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# Промпт 3: история чатов (AIChatSession / AIChatMessage) + action
# create-situation. Все endpoints требуют JWT и проверяют владельца.
# ─────────────────────────────────────────────────────────────────────────────
import uuid as _uuid
from datetime import datetime as _dt

from sqlalchemy import select as _select
from backend.api.user import get_current_user as _get_current_user
from backend.models import (
    AIChatMessage,
    AIChatSession,
    User as _User,
    Scenario as _Scenario,
    ScenarioStage as _ScenarioStage,
    ScenarioStep as _ScenarioStep,
    UserSituation as _UserSituation,
    UserSituationTask as _UserSituationTask,
)


def _gen_id() -> str:
    return _uuid.uuid4().hex


class AIChatSessionOut(BaseModel):
    id: str
    title: str
    mode: str
    archived: bool
    last_message_preview: str
    created_at: str
    updated_at: str


class AIChatSessionCreate(BaseModel):
    title: str = ""
    mode: Literal["citizen", "editor"] = "citizen"


class AIChatSessionPatch(BaseModel):
    title: str | None = None
    archived: bool | None = None


class AIChatMessageOut(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    links: list[dict] = Field(default_factory=list)
    actions: list[dict] = Field(default_factory=list)
    sources: list[dict] = Field(default_factory=list)
    source: str
    model: str
    provider: str
    error_code: str
    created_at: str


class AIChatMessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=4000)


def _session_out(s: AIChatSession) -> AIChatSessionOut:
    return AIChatSessionOut(
        id=s.id,
        title=s.title or "Новый чат",
        mode=s.mode or "citizen",
        archived=bool(s.archived),
        last_message_preview=s.last_message_preview or "",
        created_at=s.created_at.isoformat() if s.created_at else "",
        updated_at=s.updated_at.isoformat() if s.updated_at else "",
    )


def _message_out(m: AIChatMessage) -> AIChatMessageOut:
    return AIChatMessageOut(
        id=m.id,
        session_id=m.session_id,
        role=m.role,
        content=m.content,
        links=_loads(m.links_json),
        actions=_loads(m.actions_json),
        sources=_loads(m.sources_json),
        source=m.source or "",
        model=m.model or "",
        provider=m.provider or "",
        error_code=m.error_code or "",
        created_at=m.created_at.isoformat() if m.created_at else "",
    )


def _loads(raw: str) -> list:
    try:
        v = json.loads(raw or "[]")
        return v if isinstance(v, list) else []
    except (ValueError, TypeError):
        return []


def _owned_session(db: Session, user: _User, session_id: str) -> AIChatSession:
    s = db.scalars(
        _select(AIChatSession).where(
            AIChatSession.id == session_id,
            AIChatSession.user_id == user.id,
        )
    ).first()
    if not s:
        from fastapi import HTTPException, status as st
        raise HTTPException(status_code=st.HTTP_404_NOT_FOUND, detail="Сессия не найдена.")
    return s


@router.get("/chat/sessions", response_model=list[AIChatSessionOut])
def list_chat_sessions(user: _User = Depends(_get_current_user), db: Session = Depends(get_db)):
    sessions = db.scalars(
        _select(AIChatSession)
        .where(AIChatSession.user_id == user.id, AIChatSession.mode == "citizen", AIChatSession.archived == False)  # noqa: E712
        .order_by(AIChatSession.updated_at.desc())
    ).all()
    return [_session_out(s) for s in sessions]


@router.post("/chat/sessions", response_model=AIChatSessionOut, status_code=201)
def create_chat_session(
    payload: AIChatSessionCreate,
    user: _User = Depends(_get_current_user),
    db: Session = Depends(get_db),
):
    s = AIChatSession(
        id=_gen_id(),
        user_id=user.id,
        title=(payload.title or "Новый чат")[:200],
        mode=payload.mode,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return _session_out(s)


@router.patch("/chat/sessions/{session_id}", response_model=AIChatSessionOut)
def patch_chat_session(
    session_id: str,
    payload: AIChatSessionPatch,
    user: _User = Depends(_get_current_user),
    db: Session = Depends(get_db),
):
    s = _owned_session(db, user, session_id)
    data = payload.model_dump(exclude_none=True)
    if "title" in data:
        s.title = data["title"][:200]
    if "archived" in data:
        s.archived = bool(data["archived"])
    db.commit()
    db.refresh(s)
    return _session_out(s)


@router.delete("/chat/sessions/{session_id}", status_code=204)
def delete_chat_session(session_id: str, user: _User = Depends(_get_current_user), db: Session = Depends(get_db)):
    s = _owned_session(db, user, session_id)
    db.delete(s)
    db.commit()


@router.get("/chat/sessions/{session_id}/messages", response_model=list[AIChatMessageOut])
def list_chat_messages(session_id: str, user: _User = Depends(_get_current_user), db: Session = Depends(get_db)):
    s = _owned_session(db, user, session_id)
    return [_message_out(m) for m in s.messages]


def _structured_response(
    db: Session,
    user: _User | None,
    message: str,
) -> dict:
    """Промпт 3: структурированный ответ ассистента.

    Возвращает dict с text/links/actions/sources/source/model. Никаких
    «выдуманных» путей — actions/links строятся только из server-side entities.
    """
    entities = _collect_rag_entities(db, message)
    system_prompt = _build_system_prompt(entities)
    raw = _llm_chat(message, system_prompt)
    if raw is None:
        text, links = _local_chat_fallback(message, entities)
        source = "local"
    else:
        text, links = _parse_chat_response(raw, entities)
        source = "llm"
        if not text and not links:
            text, links = _local_chat_fallback(message, entities)
            source = "local"

    # Actions: для каждого сценария среди entities (top 2) предлагаем добавить
    # в «Мои ситуации» (если пользователь авторизован).
    actions: list[dict] = []
    if user is not None:
        seen = set()
        for e in entities:
            if e["kind"] != "scenario":
                continue
            if e["id"] in seen:
                continue
            seen.add(e["id"])
            actions.append({
                "type": "create_user_situation",
                "label": f"Добавить «{e['title']}» в мои ситуации",
                "scenario_id": str(e["id"]),
                "title": e["title"],
            })
            if len(actions) >= 2:
                break

    sources = [{"kind": e["kind"], "title": e["title"], "path": e["path"]} for e in entities[:5]]

    return {
        "text": text,
        "links": links,
        "actions": actions,
        "sources": sources,
        "source": source,
        "model": os.getenv("GROQ_MODEL", "llama-3.1-8b-instant") if source == "llm" else "",
        "provider": "groq" if source == "llm" else "",
        "error_code": "",
    }


@router.post("/chat/sessions/{session_id}/messages", response_model=AIChatMessageOut, status_code=201)
def post_chat_message(
    session_id: str,
    payload: AIChatMessageCreate,
    user: _User = Depends(_get_current_user),
    db: Session = Depends(get_db),
):
    """Промпт 3: пользователь шлёт сообщение → backend сохраняет user-msg,
    делает RAG/LLM запрос, сохраняет assistant-msg, отдаёт его наружу."""
    s = _owned_session(db, user, session_id)
    user_msg_text = (payload.content or "").strip()
    if not user_msg_text:
        from fastapi import HTTPException, status as st
        raise HTTPException(status_code=st.HTTP_422_UNPROCESSABLE_ENTITY, detail="Пустое сообщение.")

    # 1) сохраняем сообщение пользователя
    user_msg = AIChatMessage(
        id=_gen_id(),
        session_id=s.id,
        role="user",
        content=user_msg_text[:4000],
    )
    db.add(user_msg)

    # 2) если у сессии нет осмысленного title — берём первый user-msg
    if not s.title or s.title == "Новый чат":
        s.title = user_msg_text[:60]

    # 3) делаем RAG+LLM
    resp = _structured_response(db, user, user_msg_text)

    # 4) сохраняем ответ ассистента
    assistant_msg = AIChatMessage(
        id=_gen_id(),
        session_id=s.id,
        role="assistant",
        content=(resp["text"] or "")[:4000],
        links_json=json.dumps(resp["links"], ensure_ascii=False),
        actions_json=json.dumps(resp["actions"], ensure_ascii=False),
        sources_json=json.dumps(resp["sources"], ensure_ascii=False),
        source=resp["source"],
        model=resp["model"],
        provider=resp["provider"],
        error_code=resp["error_code"],
    )
    db.add(assistant_msg)
    s.last_message_preview = (resp["text"] or "")[:200]
    db.commit()
    db.refresh(assistant_msg)
    return _message_out(assistant_msg)


# Промпт 3: action create-situation. Создаёт UserSituation из сценария.
class CreateSituationActionIn(BaseModel):
    scenario_id: str
    session_id: str | None = None


class CreateSituationActionOut(BaseModel):
    created: bool
    situation_id: str
    route: str
    message: str


def _build_situation_from_scenario(db: Session, user: _User, scenario: _Scenario) -> _UserSituation:
    sit = _UserSituation(
        id=_gen_id(),
        user_id=user.id,
        template_id=str(scenario.id),
        title=scenario.title,
        status="Не начата",
        progress=0,
        category=scenario.category or "",
    )
    db.add(sit)
    # Шаги → задачи. Если шагов нет — fallback на этапы.
    idx = 0
    for stage in sorted(scenario.stages or [], key=lambda x: x.order_index or 0):
        steps = sorted(stage.steps or [], key=lambda x: x.order_index or 0)
        if steps:
            for st in steps:
                db.add(_UserSituationTask(
                    id=_gen_id(),
                    situation_id=sit.id,
                    title=st.title,
                    completed=False,
                    due_date="",
                    stage_title=stage.title,
                    order_index=idx,
                ))
                idx += 1
        else:
            db.add(_UserSituationTask(
                id=_gen_id(),
                situation_id=sit.id,
                title=stage.title,
                completed=False,
                due_date="",
                stage_title=stage.title,
                order_index=idx,
            ))
            idx += 1
    return sit


@router.post("/actions/create-situation", response_model=CreateSituationActionOut)
def assistant_create_situation(
    payload: CreateSituationActionIn,
    user: _User = Depends(_get_current_user),
    db: Session = Depends(get_db),
):
    """Промпт 3: action из чата — добавить сценарий в «Мои ситуации».

    Идемпотентно: если уже есть ситуация по этому шаблону, возвращает её id.
    """
    try:
        scenario_id_int = int(payload.scenario_id)
    except ValueError:
        # slug-based scenario? в текущей БД scenarios.id — BigInteger.
        from fastapi import HTTPException, status as st
        raise HTTPException(status_code=st.HTTP_422_UNPROCESSABLE_ENTITY, detail="Невалидный scenario_id.")

    scenario = db.scalars(_select(_Scenario).where(_Scenario.id == scenario_id_int)).first()
    if not scenario:
        from fastapi import HTTPException, status as st
        raise HTTPException(status_code=st.HTTP_404_NOT_FOUND, detail="Сценарий не найден.")

    existing = db.scalars(
        _select(_UserSituation)
        .where(_UserSituation.user_id == user.id, _UserSituation.template_id == str(scenario.id))
    ).first()
    if existing:
        return CreateSituationActionOut(
            created=False,
            situation_id=existing.id,
            route=f"/situations/{existing.id}",
            message="Ситуация уже была добавлена ранее.",
        )

    sit = _build_situation_from_scenario(db, user, scenario)
    db.commit()
    db.refresh(sit)
    return CreateSituationActionOut(
        created=True,
        situation_id=sit.id,
        route=f"/situations/{sit.id}",
        message=f"«{scenario.title}» добавлена в ваши ситуации.",
    )
