from http.client import HTTPException

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..db.database import get_db
from ..dependencies.role_checker import require_roles
from ..models.models_v2 import User, Tag, Landing
from ..schemas_v2 import landing
from ..services_v2.landing_service import list_landings, get_landing_detail, create_landing, update_landing, \
    delete_landing, get_landing_cards
from ..schemas_v2.landing import LandingListResponse, LandingDetailResponse, LandingCreate, LandingUpdate, TagResponse, \
    LandingCardResponse, LandingSearchResponse

router = APIRouter()

@router.get("/list", response_model=List[LandingListResponse])
def get_landing_listing(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, gt=0),
    db: Session = Depends(get_db)
):
    landings = list_landings(db, skip=skip, limit=limit)
    return landings

@router.get("/detail/{landing_id}", response_model=LandingDetailResponse)
def get_landing_by_id(landing_id: int, db: Session = Depends(get_db)):
    landing = get_landing_detail(db, landing_id)
    # Если lessons_info хранится как словарь, преобразуем его в список
    lessons = landing.lessons_info
    if isinstance(lessons, dict):
        lessons_list = [{k: v} for k, v in lessons.items()]
    elif isinstance(lessons, list):
        lessons_list = lessons
    else:
        lessons_list = []
    authors_list = [
        {"id": author.id, "name": author.name, "description": author.description, "photo": author.photo}
        for author in landing.authors
    ] if landing.authors else []
    tags_list = [
        {"id": tag.id, "name": tag.name}
        for tag in landing.tags
    ] if landing.tags else []
    # Собираем итоговый ответ
    return {
        "id": landing.id,
        "page_name": landing.page_name,
        "language": landing.language,
        "landing_name": landing.landing_name,
        "old_price": landing.old_price,
        "new_price": landing.new_price,
        "course_program": landing.course_program,
        "lessons_info": lessons_list,
        "preview_photo": landing.preview_photo,
        "sales_count": landing.sales_count,
        "author_ids": [author.id for author in landing.authors] if landing.authors else [],
        "course_ids": [course.id for course in landing.courses] if landing.courses else [],
        "tag_ids": [tag.id for tag in landing.tags] if landing.tags else [],
        "authors": authors_list,  # Новое поле с подробностями об авторах
        "tags": tags_list,  # Новое поле с подробностями о тегах
        "duration": landing.duration,
        "lessons_count": landing.lessons_count,
    }

@router.get("/detail/by-page/{page_name}", response_model=LandingDetailResponse)
def get_landing_by_page(page_name: str, db: Session = Depends(get_db)):
    landing = db.query(Landing).filter(Landing.page_name == page_name).first()
    if not landing:
        raise HTTPException(status_code=404, detail="Landing not found")
    lessons = landing.lessons_info
    if isinstance(lessons, dict):
        lessons_list = [{k: v} for k, v in lessons.items()]
    elif isinstance(lessons, list):
        lessons_list = lessons
    else:
        lessons_list = []
    authors_list = [
        {"id": author.id, "name": author.name, "description": author.description, "photo": author.photo}
        for author in landing.authors
    ] if landing.authors else []
    tags_list = [
        {"id": tag.id, "name": tag.name}
        for tag in landing.tags
    ] if landing.tags else []
    return {
        "id": landing.id,
        "page_name": landing.page_name,
        "language": landing.language,
        "landing_name": landing.landing_name,
        "old_price": landing.old_price,
        "new_price": landing.new_price,
        "course_program": landing.course_program,
        "lessons_info": lessons_list,
        "preview_photo": landing.preview_photo,
        "sales_count": landing.sales_count,
        "author_ids": [author.id for author in landing.authors] if landing.authors else [],
        "course_ids": [course.id for course in landing.courses] if landing.courses else [],
        "tag_ids": [tag.id for tag in landing.tags] if landing.tags else [],
        "authors": authors_list,
        "tags": tags_list,
        "duration": landing.duration,
        "lessons_count": landing.lessons_count,
    }

@router.post("/", response_model=LandingListResponse)
def create_new_landing(
    landing_data: LandingCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin"))
):
    new_landing = create_landing(db, landing_data)
    return {
        "id": new_landing.id,
        "landing_name": new_landing.landing_name,
        "page_name": new_landing.page_name,
        "language": new_landing.language
    }

@router.put("/{landing_id}", response_model=LandingDetailResponse)
def update_landing_full(
    landing_id: int,
    update_data: LandingUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin"))
):
    updated_landing = update_landing(db, landing_id, update_data)
    lessons = updated_landing.lessons_info
    if isinstance(lessons, dict):
        lessons_list = [{k: v} for k, v in lessons.items()]
    elif isinstance(lessons, list):
        lessons_list = lessons
    else:
        lessons_list = []
    return {
        "id": updated_landing.id,
        "page_name": updated_landing.page_name,
        "language": updated_landing.language,
        "landing_name": updated_landing.landing_name,
        "old_price": updated_landing.old_price,
        "new_price": updated_landing.new_price,
        "course_program": updated_landing.course_program,
        "lessons_info": lessons_list,
        "preview_photo": updated_landing.preview_photo,
        "sales_count": updated_landing.sales_count,
        "author_ids": [author.id for author in updated_landing.authors] if updated_landing.authors else [],
        "course_ids": [course.id for course in updated_landing.courses] if updated_landing.courses else [],
        "tag_ids": [tag.id for tag in updated_landing.tags] if updated_landing.tags else [],
        "duration": updated_landing.duration,
        "lessons_count": updated_landing.lessons_count,
    }

@router.get("/tags", response_model=List[TagResponse])
def get_all_tags(db: Session = Depends(get_db)):
    tags = db.query(Tag).all()
    return tags

@router.delete("/{landing_id}", response_model=dict)
def delete_landing_route(landing_id: int, db: Session = Depends(get_db),current_admin: User = Depends(require_roles("admin"))):
    delete_landing(db, landing_id)
    return {"detail": "Landing deleted successfully"}

@router.get("/cards", response_model=List[LandingCardResponse])
def get_cards(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, gt=0),
    tags: Optional[List[str]] = Query(None, description="Список тегов для фильтрации"),
    sort: Optional[str] = Query(None, description="Фильтр: popular, discount, new"),
    language: Optional[str] = Query(None, description="Язык лендинга: ES, EN, RU"),
    db: Session = Depends(get_db)
):
    """
    Получение карточек лендингов с пагинацией, фильтрацией по тегам и сортировкой.
    В карточке возвращаются:
      - Первый тег
      - Название лендинга
      - Все авторы (имена и фотографии)
      - Slug (page_name)
      - Основное изображение
      - Старая цена и новая цена
    """
    cards = get_landing_cards(db, skip, limit, tags, sort, language)
    return cards

@router.get("/search", response_model=List[LandingSearchResponse])
def search_landings(
    q: str = Query(..., min_length=1, description="Поисковый запрос по названию лендинга"),
    db: Session = Depends(get_db)
):
    """
    Поиск лендингов по названию.
    В ответе возвращаются только id и название лендинга.
    """
    landings = db.query(Landing).filter(Landing.landing_name.ilike(f"%{q}%")).all()
    if not landings:
        raise HTTPException(status_code=404, detail="Нет лендингов, соответствующих запросу")
    return landings