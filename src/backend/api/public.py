from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend import schemas
from backend.service import (
    get_published_problem_by_slug,
    get_published_scenario_by_slug,
    list_authorities,
    list_problems_admin,
    list_published_documents,
    list_published_law_updates,
    list_published_problem_scenarios,
    list_published_problems,
    list_published_scenario_steps,
    scenario_to_full_schema,
)


router = APIRouter(prefix="/api", tags=["public"])


@router.get("/problems", response_model=list[schemas.ProblemPublicOut])
def get_problems(db: Session = Depends(get_db)):
    return [schemas.ProblemPublicOut.model_validate(item) for item in list_published_problems(db)]


@router.get("/problems/{slug}", response_model=schemas.ProblemWithScenariosOut)
def get_problem(slug: str, db: Session = Depends(get_db)):
    problem = get_published_problem_by_slug(db, slug)
    if not problem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Проблема не найдена")

    scenarios = list_published_problem_scenarios(db, problem.id)
    payload = schemas.ProblemWithScenariosOut.model_validate(problem)
    return payload.model_copy(
        update={
            "scenarios": [schemas.ScenarioPublicSummary.model_validate(item) for item in scenarios],
        }
    )


@router.get("/scenarios/{slug}", response_model=schemas.ScenarioFullOut)
def get_scenario(slug: str, db: Session = Depends(get_db)):
    scenario = get_published_scenario_by_slug(db, slug)
    if not scenario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Сценарий не найден")
    return scenario_to_full_schema(db, scenario)


@router.get("/scenarios/{slug}/steps", response_model=list[schemas.ScenarioStepOut])
def get_scenario_steps(slug: str, db: Session = Depends(get_db)):
    steps = list_published_scenario_steps(db, slug)
    if not steps:
        scenario = get_published_scenario_by_slug(db, slug)
        if not scenario:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Сценарий не найден")
    return [schemas.ScenarioStepOut.model_validate(item) for item in steps]


@router.get("/documents", response_model=list[schemas.DocumentOut])
def get_documents(db: Session = Depends(get_db)):
    return [schemas.DocumentOut.model_validate(item) for item in list_published_documents(db)]


@router.get("/authorities", response_model=list[schemas.AuthorityOut])
def get_authorities(db: Session = Depends(get_db)):
    return [schemas.AuthorityOut.model_validate(item) for item in list_authorities(db)]


@router.get("/law-updates", response_model=list[schemas.LawUpdateOut])
def get_law_updates(db: Session = Depends(get_db)):
    """
    E7 — публичная лента закон-апдейтов со статусом APPLIED.
    В production Flet-клиент будет подтягивать этот список вместо mock_data.
    Статус APPLIED означает, что изменение проверено и применено в контенте.
    """
    return [schemas.LawUpdateOut.model_validate(item) for item in list_published_law_updates(db)]


@router.get("/law-updates/{law_update_id}", response_model=schemas.LawUpdateOut)
def get_law_update(law_update_id: int, db: Session = Depends(get_db)):
    from backend.models import LawUpdate
    from sqlalchemy import select as sa_select
    obj = db.scalars(sa_select(LawUpdate).where(LawUpdate.id == law_update_id)).first()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Закон-апдейт не найден")
    return schemas.LawUpdateOut.model_validate(obj)


@router.get("/admin/bootstrap/problems", response_model=list[schemas.ProblemPublicOut])
def get_admin_bootstrap_problems(db: Session = Depends(get_db)):
    """
    Временный endpoint для Flet админ-панели (MVP),
    чтобы можно было отрисовать списки до полной CRUD-интеграции UI.
    """
    return [schemas.ProblemPublicOut.model_validate(item) for item in list_problems_admin(db)]

