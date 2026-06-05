"""AI assistant proxy (ТЗ §2, §3).

Keeps the Groq API key server-side: the React client never sees it. A local
keyword intent-router always picks the target section (deterministic, safe);
the LLM only writes the short conversational reply. If the LLM is unavailable
the endpoint still returns a useful canned answer.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

import httpx
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/assistant", tags=["assistant"])

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

SYSTEM_PROMPT = (
    "Ты — встроенный помощник сайта «Белпомощник» для граждан Беларуси. "
    "Помогаешь сориентироваться по разделам сайта и коротко подсказываешь, где решить вопрос. "
    "Не выдумывай функции, которых нет. Не давай сложных юридических заключений. "
    "Отвечай простым языком, 1–3 предложения, по-русски. "
    "Тебе уже выбран подходящий раздел — сошлись на него естественно, не выводи технические id."
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
