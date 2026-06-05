"""Local intent router for the built-in assistant.

The module is intentionally small and deterministic now. Later it can delegate
the same normalized prompt and section registry to a real LLM/API without
changing the chat UI contract.
"""
from __future__ import annotations

from dataclasses import dataclass

from services.role_guard import ROLE_RANK


SYSTEM_PROMPT = """
Ты — встроенный ИИ-помощник сайта «Белпомощник».
Твоя задача — помогать пользователю ориентироваться по разделам сайта и
подсказывать, где он может решить свой вопрос.

Ты не должен выдумывать несуществующие функции. Используй только те разделы и
возможности, которые реально есть в проекте.

Тебе доступны сведения о разделах сайта:
- Главное
- Глобальный поиск
- Каталог проблем
- Карточки проблем
- Жизненные сценарии
- Мои ситуации
- Документы
- Уведомления
- Закон-апдейты
- Профиль
- Настройки
- Админ-панель, если пользователь имеет роль администратора
- Редакторские разделы, если пользователь имеет роль редактора контента

Если пользователь спрашивает, где что-то найти или сделать, определи наиболее
подходящий раздел и верни короткий понятный ответ, название раздела, описание
действия и route/path/id раздела для перехода.

Если пользователь не авторизован, можно подсказывать раздел, но для действий,
требующих аккаунт, нужно сообщить, что для выполнения действия понадобится вход
или регистрация.

Отвечай простым языком, без юридически сложных формулировок. Ориентируйся на
пользователей от 14 до 60+ лет.
""".strip()


@dataclass(frozen=True)
class SectionInfo:
    id: str
    title: str
    description: str
    route: str
    keywords: tuple[str, ...]
    requires_auth: bool = False
    min_role: str = "guest"


@dataclass(frozen=True)
class IntentResult:
    section: SectionInfo
    response_text: str
    requires_auth_warning: bool = False
    confidence: float = 0.0


SECTION_REGISTRY: tuple[SectionInfo, ...] = (
    SectionInfo(
        id="home",
        title="Главное",
        description="Обзор ситуаций, ближайших задач, документов и быстрых действий.",
        route="/",
        keywords=("главная", "главное", "обзор", "дашборд", "старт", "начать", "куда перейти"),
    ),
    SectionInfo(
        id="search",
        title="Глобальный поиск",
        description="Поиск по проблемам, сценариям, документам, учреждениям и новостям.",
        route="/search",
        keywords=("поиск", "найти", "искать", "где найти", "подобрать", "по адресу", "рядом"),
    ),
    SectionInfo(
        id="problems",
        title="Каталог проблем",
        description="Справочные карточки с понятным планом действий по жизненным проблемам.",
        route="/problems",
        keywords=("проблема", "каталог", "карточка", "паспорт", "медкнижка", "жкх", "налог", "развод"),
    ),
    SectionInfo(
        id="scenarios",
        title="Жизненные сценарии",
        description="Готовые маршруты: этапы, задачи, документы, сроки и организации.",
        route="/scenarios",
        keywords=("сценарий", "ситуация из шаблона", "рождение", "ребенок", "ребёнок", "ип", "переезд", "маршрут"),
    ),
    SectionInfo(
        id="situations",
        title="Мои ситуации",
        description="Личные планы, задачи, чек-листы и прогресс выполнения.",
        route="/situations",
        keywords=("мои ситуации", "личная ситуация", "план", "задача", "чеклист", "чек-лист", "прогресс", "отметить"),
        requires_auth=True,
    ),
    SectionInfo(
        id="documents",
        title="Документы",
        description="Добавление документов, сроки действия, сканы и напоминания.",
        route="/documents",
        keywords=("документ", "документы", "паспорт", "id", "скан", "файл", "медкнижка", "срок действия", "добавить паспорт"),
        requires_auth=True,
    ),
    SectionInfo(
        id="notifications",
        title="Уведомления",
        description="Напоминания о сроках задач, документов и важных изменениях.",
        route="/notifications",
        keywords=("уведомление", "напоминание", "срок", "дедлайн", "подписка", "оповещение"),
        requires_auth=True,
    ),
    SectionInfo(
        id="legal_updates",
        title="Закон-апдейты",
        description="Понятная лента изменений правил, сроков и документов.",
        route="/legal-updates",
        keywords=("закон", "законы", "новости", "изменения", "правила", "апдейт", "обновления законодательства"),
    ),
    SectionInfo(
        id="utility",
        title="ЖКХ-трекер",
        description="Контроль лицевого счёта, сроков оплаты и передачи показаний.",
        route="/utility",
        keywords=("жкх", "коммуналка", "квитанция", "лицевой счет", "лицевой счёт", "показания", "оплата"),
        requires_auth=True,
    ),
    SectionInfo(
        id="taxes",
        title="Налоговый трекер",
        description="Контроль налоговых обязательств, сроков и статусов оплаты.",
        route="/taxes",
        keywords=("налог", "налоги", "ип", "имущество", "оплатить налог", "налоговый"),
        requires_auth=True,
    ),
    SectionInfo(
        id="profile",
        title="Профиль",
        description="Личные данные, регион, интересы, прогресс обучения и настройки аккаунта.",
        route="/profile",
        keywords=("профиль", "личные данные", "регион", "город", "интересы", "аккаунт"),
        requires_auth=True,
    ),
    SectionInfo(
        id="settings",
        title="Настройки",
        description="Тема, язык, уведомления, доступность и приватность.",
        route="/settings",
        keywords=("настройки", "язык", "тема", "темная", "тёмная", "доступность", "контраст", "приватность"),
        requires_auth=True,
    ),
    SectionInfo(
        id="learning",
        title="Обучение",
        description="Короткие тесты, достижения и прогресс по категориям.",
        route="/learning",
        keywords=("обучение", "тест", "проверить себя", "достижение", "прогресс обучения"),
        requires_auth=True,
    ),
    SectionInfo(
        id="admin",
        title="Админ-панель",
        description="Управление пользователями, ролями, справочниками и аудитом.",
        route="/admin",
        keywords=("админ", "администратор", "пользователи", "роли", "аудит", "справочники"),
        min_role="platform_admin",
    ),
    SectionInfo(
        id="editor",
        title="Редакторская",
        description="Управление сценариями, проблемами, шагами, источниками и закон-апдейтами.",
        route="/admin",
        keywords=("редактор", "контент", "создать сценарий", "редактировать сценарий", "источники", "публикация"),
        min_role="content_editor",
    ),
)


def _normalize(text: str) -> str:
    cleaned = (text or "").lower().replace("ё", "е")
    return " ".join(cleaned.split())


def _role_allows(role: str, required_role: str) -> bool:
    return ROLE_RANK.get(role, -1) >= ROLE_RANK.get(required_role, 99)


def _score(section: SectionInfo, query: str) -> float:
    if not query:
        return 0.0
    title = _normalize(section.title)
    if query == title:
        return 1.0
    score = 0.0
    if query in title or title in query:
        score += 0.35
    for keyword in section.keywords:
        normalized_keyword = _normalize(keyword)
        if not normalized_keyword:
            continue
        if query == normalized_keyword:
            score += 0.60
        elif query.startswith(normalized_keyword) or normalized_keyword.startswith(query):
            score += 0.32
        elif normalized_keyword in query:
            score += 0.26
    return min(score, 1.0)


def _resolve_via_llm(_query: str, _role: str, _is_guest: bool) -> IntentResult | None:
    """Future integration point for a real AI model."""
    return None


def _fallback_section(role: str) -> SectionInfo:
    for section in SECTION_REGISTRY:
        if section.id == "search" and _role_allows(role, section.min_role):
            return section
    return SECTION_REGISTRY[0]


def detect_intent(query: str, *, role: str = "guest", is_guest: bool = True) -> IntentResult:
    """Return the most suitable section for a user question."""
    normalized_query = _normalize(query)
    llm_result = _resolve_via_llm(normalized_query, role, is_guest)
    if llm_result is not None:
        return llm_result

    candidates: list[tuple[float, SectionInfo]] = []
    inaccessible: list[tuple[float, SectionInfo]] = []
    for section in SECTION_REGISTRY:
        score = _score(section, normalized_query)
        if score <= 0:
            continue
        if _role_allows(role, section.min_role):
            candidates.append((score, section))
        else:
            inaccessible.append((score, section))

    if candidates:
        confidence, section = max(candidates, key=lambda item: item[0])
    elif inaccessible:
        confidence, section = max(inaccessible, key=lambda item: item[0])
    else:
        section = _fallback_section(role)
        confidence = 0.15

    role_blocked = not _role_allows(role, section.min_role)
    requires_auth_warning = bool(is_guest and section.requires_auth)

    if role_blocked:
        response = (
            f"Похоже, вам нужен раздел «{section.title}», но он доступен только "
            "пользователям с подходящей ролью. Для обычных вопросов лучше начать с поиска "
            "или каталога проблем."
        )
        fallback = _fallback_section(role)
        return IntentResult(
            section=fallback,
            response_text=response,
            requires_auth_warning=False,
            confidence=confidence,
        )

    response = f"Вы можете решить этот вопрос в разделе «{section.title}». {section.description}"
    if requires_auth_warning:
        response += " Для выполнения личного действия понадобится вход или регистрация."

    return IntentResult(
        section=section,
        response_text=response,
        requires_auth_warning=requires_auth_warning,
        confidence=confidence,
    )
