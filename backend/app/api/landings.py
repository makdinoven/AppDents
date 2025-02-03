# api/landings.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ..dependencies.role_checker import require_roles
from ..models.models import User
from ..schemas.landing import LandingCreate, LandingCardResponse, LandingDetailResponse, LandingUpdate, LanguageEnum
from ..services.landing_service import create_landing, get_landing_cards, get_landing_by_id, update_landing, \
    delete_landing, get_landings_by_language, search_landings
from ..db.database import get_db
from typing import List

router = APIRouter()

@router.post(
    "/",
    response_model=LandingDetailResponse,
    summary="Добавить новый лендинг",
    description="Создает новый лендинг с указанными данными: название, цены, изображение, программу курса, модули, лекторов и привязку к курсу."
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
    summary="Получить карточки лендингов",
    description="Возвращает список лендингов с краткой информацией: тег, название, изображение и список авторов."
)
def list_landings(db: Session = Depends(get_db)):
    landings = get_landing_cards(db)
    return landings

@router.get(
    "/{language}",
    response_model=List[LandingCardResponse],
    summary="Получить лендинги по языку",
    description="Возвращает список лендингов, отфильтрованных по заданному языку (en, es, ru)."
)
def list_landings_by_language(language: LanguageEnum, db: Session = Depends(get_db)):
    landings = get_landings_by_language(db, language)
    return landings

@router.get(
    "/{landing_id}",
    response_model=LandingDetailResponse,
    summary="Получить информацию о лендинге",
    description="Возвращает полную информацию о лендинге по его идентификатору."
)
def get_landing(landing_id: int, db: Session = Depends(get_db)):
    try:
        landing = get_landing_by_id(db, landing_id)
        return landing
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

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
    summary="Поиск лендингов",
    description="Ищет лендинги по названию (регистронезависимый поиск)."
)
def search_landings_endpoint(query: str = Query(..., description="Строка для поиска лендингов по названию"), db: Session = Depends(get_db)):
    landings = search_landings(db, query)
    return landings