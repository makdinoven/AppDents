from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from ..db.database import get_db
from ..services_v2.landing_service  import list_landings, get_landing_detail, create_landing, update_landing
from ..schemas_v2.landing import LandingListResponse, LandingDetailResponse, LandingCreate, LandingUpdate

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
    # Для вывода добавляем массивы id авторов и курсов из ассоциаций
    author_ids = [author.id for author in landing.authors] if landing.authors else []
    course_ids = [course.id for course in landing.courses] if landing.courses else []
    # Можно сконструировать итоговый словарь, добавив эти поля
    landing_data = {
        "id": landing.id,
        "page_name": landing.page_name,
        "landing_name": landing.landing_name,
        "old_price": landing.old_price,
        "new_price": landing.new_price,
        "course_program": landing.course_program,
        "lessons_info": landing.lessons_info,
        "preview_photo": landing.preview_photo,
        "tag_id": landing.tag_id,
        "sales_count": landing.sales_count,
        "author_ids": author_ids,
        "course_ids": course_ids
    }
    return landing_data

@router.post("/", response_model=LandingListResponse)
def create_new_landing(
    landing_data: LandingCreate,
    db: Session = Depends(get_db)
):
    new_landing = create_landing(db, landing_data)
    return new_landing

@router.put("/{landing_id}", response_model=LandingDetailResponse)
def update_landing_full(
    landing_id: int,
    update_data: LandingUpdate,
    db: Session = Depends(get_db)
):
    updated_landing = update_landing(db, landing_id, update_data)
    author_ids = [author.id for author in updated_landing.authors] if updated_landing.authors else []
    course_ids = [course.id for course in updated_landing.courses] if updated_landing.courses else []
    landing_data = {
        "id": updated_landing.id,
        "page_name": updated_landing.page_name,
        "landing_name": updated_landing.landing_name,
        "old_price": updated_landing.old_price,
        "new_price": updated_landing.new_price,
        "course_program": updated_landing.course_program,
        "lessons_info": updated_landing.lessons_info,
        "preview_photo": updated_landing.preview_photo,
        "tag_id": updated_landing.tag_id,
        "sales_count": updated_landing.sales_count,
        "author_ids": author_ids,
        "course_ids": course_ids
    }
    return landing_data