from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.enums import (
    ActionType,
    ContentStatus,
    DifficultyLevel,
    DurationUnit,
    LawUpdateStatus,
    NotificationType,
    RelationType,
    SourceType,
)
from backend.models import (
    Authority,
    Deadline,
    Document,
    LawUpdate,
    NotificationRule,
    Problem,
    RelatedScenario,
    Scenario,
    ScenarioDependency,
    ScenarioStage,
    ScenarioStep,
    SourceReference,
)


def _get_or_create_problem(db: Session) -> Problem:
    problem = db.query(Problem).filter(Problem.slug == "semya-i-deti").first()
    if problem:
        return problem
    problem = Problem(
        title="Семья и дети",
        slug="semya-i-deti",
        short_description="Сценарии семейных жизненных ситуаций: рождение ребёнка, развод, алименты и другие.",
        description="Проблемная область, объединяющая жизненные сценарии семьи и детей.",
        icon="FAMILY_RESTROOM_OUTLINED",
        category="Семья",
        status=ContentStatus.PUBLISHED,
    )
    db.add(problem)
    db.flush()
    return problem


def _get_or_create_scenario(db: Session, problem_id: int) -> Scenario:
    scenario = db.query(Scenario).filter(Scenario.slug == "rozhdenie-rebenka").first()
    if scenario:
        return scenario
    scenario = Scenario(
        problem_id=problem_id,
        title="Рождение ребёнка",
        slug="rozhdenie-rebenka",
        short_description="Полный маршрут действий после рождения ребёнка.",
        description="Пошаговый сценарий от получения документов в роддоме до прикрепления ребёнка к поликлинике.",
        target_audience="Родители новорождённого ребёнка в Республике Беларусь",
        estimated_duration="От дня рождения до 1 месяца",
        difficulty_level=DifficultyLevel.MEDIUM,
        status=ContentStatus.PUBLISHED,
        priority=100,
    )
    db.add(scenario)
    db.flush()
    return scenario


def _get_or_create_authorities(db: Session) -> dict[str, Authority]:
    data = [
        ("ЗАГС", "Орган записи актов гражданского состояния.", "https://minjust.gov.by", "registry"),
        ("Исполком", "Местный исполнительный комитет.", "https://www.portal.gov.by", "local_government"),
        ("Служба «Одно окно»", "Служба приема заявлений и документов.", "https://www.portal.gov.by", "one_window"),
        ("Поликлиника", "Детская поликлиника по месту жительства.", "https://www.minzdrav.gov.by", "healthcare"),
        (
            "Органы социальной защиты",
            "Органы для назначения и выплаты пособий.",
            "https://www.mintrud.gov.by",
            "social_support",
        ),
    ]
    result: dict[str, Authority] = {}
    for title, description, website, authority_type in data:
        item = db.query(Authority).filter(Authority.title == title).first()
        if not item:
            item = Authority(
                title=title,
                description=description,
                website_url=website,
                phone="",
                address="По месту регистрации",
                working_hours="Уточняйте на официальном сайте",
                type=authority_type,
                region="Минская область",
                city="Минск",
            )
            db.add(item)
            db.flush()
        result[title] = item
    return result


def _get_or_create_deadlines(db: Session) -> dict[str, Deadline]:
    data = [
        ("В день обращения", "Процедура выполняется в день подачи документов.", 0, DurationUnit.DAYS, False),
        ("В течение 3 рабочих дней", "Срок до 3 рабочих дней.", 3, DurationUnit.DAYS, True),
        ("Не позднее 1 месяца", "Выполнить не позднее 1 месяца.", 1, DurationUnit.MONTHS, False),
    ]
    result: dict[str, Deadline] = {}
    for title, description, duration_value, duration_unit, is_business_days in data:
        item = db.query(Deadline).filter(Deadline.title == title).first()
        if not item:
            item = Deadline(
                title=title,
                description=description,
                duration_value=duration_value,
                duration_unit=duration_unit,
                is_business_days=is_business_days,
            )
            db.add(item)
            db.flush()
        result[title] = item
    return result


def _get_or_create_documents(db: Session) -> dict[str, Document]:
    data = [
        ("Паспорт матери", "Основной документ, удостоверяющий личность матери.", "identity"),
        ("Паспорт отца", "Основной документ, удостоверяющий личность отца.", "identity"),
        ("Медицинская справка о рождении", "Справка из роддома для регистрации рождения.", "medical"),
        ("Свидетельство о браке", "Документ о браке родителей (если применимо).", "registry"),
        ("Заявление", "Заявление установленной формы.", "form"),
        ("Свидетельство о рождении ребёнка", "Документ, выдаваемый после регистрации рождения.", "registry"),
    ]
    result: dict[str, Document] = {}
    for title, description, document_type in data:
        item = db.query(Document).filter(Document.title == title).first()
        if not item:
            item = Document(
                title=title,
                description=description,
                document_type=document_type,
                is_required=True,
                where_to_get="Уполномоченный государственный орган",
                validity_period="По правилам соответствующего органа",
                status=ContentStatus.PUBLISHED,
            )
            db.add(item)
            db.flush()
        result[title] = item
    return result


def _create_stage_if_missing(db: Session, scenario_id: int, order_index: int, title: str, description: str) -> ScenarioStage:
    stage = (
        db.query(ScenarioStage)
        .filter(ScenarioStage.scenario_id == scenario_id, ScenarioStage.order_index == order_index)
        .first()
    )
    if stage:
        return stage
    stage = ScenarioStage(
        scenario_id=scenario_id,
        title=title,
        description=description,
        order_index=order_index,
        is_required=True,
    )
    db.add(stage)
    db.flush()
    return stage


def _create_step_if_missing(
    db: Session,
    stage: ScenarioStage,
    order_index: int,
    title: str,
    description: str,
    action_type: ActionType,
    authority: Authority | None,
    deadline: Deadline | None,
    required_documents: list[Document],
) -> ScenarioStep:
    step = (
        db.query(ScenarioStep)
        .filter(ScenarioStep.stage_id == stage.id, ScenarioStep.order_index == order_index)
        .first()
    )
    if not step:
        step = ScenarioStep(
            stage_id=stage.id,
            title=title,
            description=description,
            order_index=order_index,
            action_type=action_type,
            authority_id=authority.id if authority else None,
            deadline_id=deadline.id if deadline else None,
            is_required=True,
        )
        db.add(step)
        db.flush()
    for document in required_documents:
        if document not in step.documents:
            step.documents.append(document)
    return step


def seed_mvp_childbirth(db: Session) -> dict[str, int]:
    problem = _get_or_create_problem(db)
    scenario = _get_or_create_scenario(db, problem.id)
    authorities = _get_or_create_authorities(db)
    deadlines = _get_or_create_deadlines(db)
    documents = _get_or_create_documents(db)

    stage_1 = _create_stage_if_missing(
        db,
        scenario.id,
        1,
        "Получение медицинских документов",
        "Получите в роддоме документы, подтверждающие факт рождения.",
    )
    stage_2 = _create_stage_if_missing(
        db,
        scenario.id,
        2,
        "Регистрация рождения",
        "Подайте документы для регистрации рождения ребёнка в ЗАГС.",
    )
    stage_3 = _create_stage_if_missing(
        db,
        scenario.id,
        3,
        "Получение свидетельства о рождении",
        "Получите свидетельство о рождении ребёнка.",
    )
    stage_4 = _create_stage_if_missing(
        db,
        scenario.id,
        4,
        "Оформление пособий",
        "Подайте заявление на пособия и выплаты.",
    )
    stage_5 = _create_stage_if_missing(
        db,
        scenario.id,
        5,
        "Регистрация ребёнка по месту жительства",
        "Оформите регистрацию ребёнка по месту жительства родителей.",
    )
    stage_6 = _create_stage_if_missing(
        db,
        scenario.id,
        6,
        "Прикрепление ребёнка к поликлинике",
        "Прикрепите ребёнка к детской поликлинике по месту жительства.",
    )

    step_1 = _create_step_if_missing(
        db,
        stage_1,
        1,
        "Получить медицинскую справку о рождении ребёнка",
        "Получите справку в роддоме для последующей регистрации.",
        ActionType.DOCUMENT_PREPARE,
        authorities["Поликлиника"],
        deadlines["В день обращения"],
        [documents["Медицинская справка о рождении"]],
    )
    step_2 = _create_step_if_missing(
        db,
        stage_1,
        2,
        "Подготовить паспорта родителей и свидетельство о браке",
        "Подготовьте документы родителей, которые потребуются для обращения в ЗАГС.",
        ActionType.DOCUMENT_PREPARE,
        None,
        deadlines["Не позднее 1 месяца"],
        [documents["Паспорт матери"], documents["Паспорт отца"], documents["Свидетельство о браке"]],
    )
    step_3 = _create_step_if_missing(
        db,
        stage_2,
        1,
        "Обратиться в ЗАГС",
        "Подайте документы для регистрации рождения.",
        ActionType.VISIT_OFFICE,
        authorities["ЗАГС"],
        deadlines["Не позднее 1 месяца"],
        [documents["Паспорт матери"], documents["Паспорт отца"], documents["Медицинская справка о рождении"]],
    )
    step_4 = _create_step_if_missing(
        db,
        stage_3,
        1,
        "Получить свидетельство о рождении ребёнка",
        "Получите готовое свидетельство о рождении после регистрации.",
        ActionType.WAITING,
        authorities["ЗАГС"],
        deadlines["В течение 3 рабочих дней"],
        [documents["Свидетельство о рождении ребёнка"]],
    )
    step_5 = _create_step_if_missing(
        db,
        stage_4,
        1,
        "Подать заявление на пособие",
        "Обратитесь в органы социальной защиты или в службу «Одно окно».",
        ActionType.ONLINE_REQUEST,
        authorities["Органы социальной защиты"],
        deadlines["Не позднее 1 месяца"],
        [documents["Заявление"], documents["Свидетельство о рождении ребёнка"]],
    )
    step_6 = _create_step_if_missing(
        db,
        stage_5,
        1,
        "Зарегистрировать ребёнка по месту жительства",
        "Подайте документы для регистрации по месту жительства.",
        ActionType.VISIT_OFFICE,
        authorities["Исполком"],
        deadlines["Не позднее 1 месяца"],
        [documents["Свидетельство о рождении ребёнка"], documents["Паспорт матери"]],
    )
    step_7 = _create_step_if_missing(
        db,
        stage_6,
        1,
        "Прикрепить ребёнка к детской поликлинике",
        "Подайте документы в поликлинику по месту жительства.",
        ActionType.VISIT_OFFICE,
        authorities["Поликлиника"],
        deadlines["В день обращения"],
        [documents["Свидетельство о рождении ребёнка"], documents["Паспорт матери"]],
    )

    # Зависимость: пособие можно оформить после получения свидетельства о рождении.
    dependency = (
        db.query(ScenarioDependency)
        .filter(
            ScenarioDependency.scenario_id == scenario.id,
            ScenarioDependency.step_id == step_5.id,
            ScenarioDependency.depends_on_step_id == step_4.id,
        )
        .first()
    )
    if not dependency:
        db.add(
            ScenarioDependency(
                scenario_id=scenario.id,
                step_id=step_5.id,
                depends_on_step_id=step_4.id,
                description="Пособие оформляется после получения свидетельства о рождении.",
            )
        )

    # Связанный сценарий (заготовка на расширение).
    divorce = db.query(Scenario).filter(Scenario.slug == "razvod").first()
    if not divorce:
        divorce = Scenario(
            problem_id=problem.id,
            title="Развод",
            slug="razvod",
            short_description="Базовый сценарий развода: документы, сроки, органы.",
            description="Заготовка сценария для следующего этапа MVP.",
            target_audience="Супруги, оформляющие расторжение брака",
            estimated_duration="1-3 месяца",
            difficulty_level=DifficultyLevel.HARD,
            status=ContentStatus.DRAFT,
            priority=10,
        )
        db.add(divorce)
        db.flush()

    relation = (
        db.query(RelatedScenario)
        .filter(
            RelatedScenario.scenario_id == scenario.id,
            RelatedScenario.related_scenario_id == divorce.id,
            RelatedScenario.relation_type == RelationType.RELATED_PROBLEM,
        )
        .first()
    )
    if not relation:
        db.add(
            RelatedScenario(
                scenario_id=scenario.id,
                related_scenario_id=divorce.id,
                relation_type=RelationType.RELATED_PROBLEM,
                description="Семейный блок сценариев и связанных юридических действий.",
            )
        )

    # Уведомление для одного из ключевых шагов.
    reminder = (
        db.query(NotificationRule)
        .filter(
            NotificationRule.step_id == step_5.id,
            NotificationRule.title == "Напоминание о подаче пособия",
        )
        .first()
    )
    if not reminder:
        db.add(
            NotificationRule(
                step_id=step_5.id,
                title="Напоминание о подаче пособия",
                message="Подайте заявление на пособие в установленные сроки.",
                notify_before_days=3,
                notification_type=NotificationType.REMINDER,
                is_active=True,
            )
        )

    # Источники: только официальные домены РБ.
    def add_source(sourceable_type: str, sourceable_id: int, title: str, url: str, source_type: SourceType, description: str):
        exists = (
            db.query(SourceReference)
            .filter(
                SourceReference.sourceable_type == sourceable_type,
                SourceReference.sourceable_id == sourceable_id,
                SourceReference.url == url,
            )
            .first()
        )
        if not exists:
            db.add(
                SourceReference(
                    sourceable_type=sourceable_type,
                    sourceable_id=sourceable_id,
                    title=title,
                    url=url,
                    source_type=source_type,
                    description=description,
                    last_checked_at=datetime.now(timezone.utc),
                )
            )

    add_source(
        "scenario",
        scenario.id,
        "Официальный правовой портал Республики Беларусь",
        "https://pravo.by",
        SourceType.LAW,
        "Нормативные правовые акты и официальные публикации.",
    )
    add_source(
        "step",
        step_3.id,
        "Министерство юстиции Республики Беларусь",
        "https://minjust.gov.by",
        SourceType.MINISTRY,
        "Регистрация актов гражданского состояния.",
    )
    add_source(
        "step",
        step_5.id,
        "Министерство труда и социальной защиты Республики Беларусь",
        "https://www.mintrud.gov.by",
        SourceType.MINISTRY,
        "Пособия семьям с детьми.",
    )
    add_source(
        "step",
        step_6.id,
        "Единый портал электронных услуг и органов госуправления",
        "https://www.portal.gov.by",
        SourceType.GOVERNMENT_PORTAL,
        "Информация по регистрации по месту жительства.",
    )

    law_update = (
        db.query(LawUpdate)
        .filter(
            LawUpdate.title == "Уточнение порядка назначения пособий семьям с детьми",
            LawUpdate.affected_scenario_id == scenario.id,
        )
        .first()
    )
    if not law_update:
        db.add(
            LawUpdate(
                title="Уточнение порядка назначения пособий семьям с детьми",
                description="Требования к комплекту документов обновлены, сроки подачи уточнены.",
                source_url="https://pravo.by",
                affected_scenario_id=scenario.id,
                affected_step_id=step_5.id,
                update_date=datetime.now(timezone.utc),
                status=LawUpdateStatus.APPLIED,
            )
        )
    elif law_update.status != LawUpdateStatus.APPLIED:
        law_update.status = LawUpdateStatus.APPLIED

    db.commit()

    return {
        "problem_id": problem.id,
        "scenario_id": scenario.id,
        "stages_count": len(scenario.stages),
        "steps_seeded": 7,
    }
