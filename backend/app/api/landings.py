# api/landings.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ..dependencies.role_checker import require_roles
from ..models.models import User, Tag, Landing
from ..schemas.landing import LandingCreate, LandingCardResponse, LandingDetailResponse, LandingUpdate, LanguageEnum, \
    TagResponse, LandingMinimalResponse
from ..services.landing_service import create_landing, get_landing_cards, get_landing_by_id, update_landing, \
    delete_landing, get_landings_by_language, search_landings
from ..db.database import get_db
from typing import List

router = APIRouter()

@router.get(
    "/tags",
    response_model=List[TagResponse],
    summary="Получить список тегов",
    description="Возвращает список всех тегов"
)
def list_tags(db: Session = Depends(get_db)):
    tags = db.query(Tag).all()
    return tags

@router.post(
    "/",
    response_model=LandingDetailResponse,
    summary="Add new landing",
    description="Create a new landing with input data",
)
def add_landing(landing: LandingCreate, db: Session = Depends(get_db),current_admin: User = Depends(require_roles("admin"))):
    try:
        new_landing = create_landing(db, landing)
        return new_landing
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get(
    "/",
    response_model=List[LandingCardResponse],
    summary="Get all landings cards",
    description="Возвращает список лендингов с краткой информацией: тег, название, изображение и список авторов."
)
def list_landings(db: Session = Depends(get_db)):
    landings = get_landing_cards(db)
    return landings

@router.get(
    "/language/{language}",
    response_model=List[LandingCardResponse],
    summary="Получить лендинги по языку",
    description=(
        "Возвращает список лендингов, отфильтрованных по заданному языку (en, es, ru). "
        "Параметры skip и limit позволяют реализовать пагинацию. "
        "Например, при limit=30 и skip=0 возвращаются первые 30 записей, "
        "а при skip=30 — следующие 30, и т.д."
    )
)
def list_landings_by_language(
    language: LanguageEnum,
    skip: int = Query(0, ge=0, description="Количество пропускаемых записей для пагинации"),
    limit: int = Query(30, ge=1, description="Количество записей на страницу"),
    db: Session = Depends(get_db)
):
    landings = get_landings_by_language(db, language, skip=skip, limit=limit)
    return landings

@router.get(
    "/detail/{landing_id}",
    response_model=LandingDetailResponse,
    summary="Get landing details",
    description="Returns full information about the landing page by its identifier."
)
def get_landing(landing_id: int, db: Session = Depends(get_db)):
    try:
        landing = get_landing_by_id(db, landing_id)
        return landing
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "LANDING_NOT_FOUND",
                    "message": "Landing page not found",
                    "translation_key": "error.landing_not_found",
                    "params": {"landing_id": landing_id}
                }
            }
        )

@router.put(
    "/{landing_id}",
    response_model=LandingDetailResponse,
    summary="Обновить лендинг",
    description="Обновляет данные существующего лендинга. Можно обновить основные поля, а также заменить модули и список авторов."
)
def update_landing_endpoint(landing_id: int, landing: LandingUpdate, db: Session = Depends(get_db),current_admin: User = Depends(require_roles("admin"))):
    try:
        updated_landing = update_landing(db, landing_id, landing)
        return updated_landing
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete(
    "/{landing_id}",
    response_model=LandingDetailResponse,
    summary="Удалить лендинг",
    description="Удаляет лендинг по его идентификатору."
)
def delete_landing_endpoint(landing_id: int, db: Session = Depends(get_db),current_admin: User = Depends(require_roles("admin"))):
    try:
        deleted_landing = delete_landing(db, landing_id)
        return deleted_landing
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get(
    "/search",
    response_model=List[LandingCardResponse],
    summary="Search landings",
    description="Searching landing pages by name (case-insensitive search)."
)
def search_landings_endpoint(
    query: str = Query(..., description="Search string for landing pages by name"),
    db: Session = Depends(get_db)
):
    landings = search_landings(db, query)
    if not landings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "LANDINGS_NOT_FOUND",
                    "message": "No landing pages found matching the query",
                    "translation_key": "error.landings_not_found",
                    "params": {"query": query}
                }
            }
        )
    return landings

@router.get(
    "/minimal",
    response_model=List[LandingMinimalResponse],
    summary="Получить список лендингов (id и название)",
    description="Возвращает список всех лендингов с их идентификаторами и названиями."
)
def list_minimal_landings(db: Session = Depends(get_db)):
    # Получаем только поля id и title
    landings = db.query(Landing).with_entities(Landing.id, Landing.title).all()
    # Преобразуем результат в список словарей (если нужно)
    return [{"id": landing.id, "title": landing.title} for landing in landings]