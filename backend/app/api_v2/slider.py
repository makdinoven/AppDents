from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..dependencies.role_checker import require_roles
from ..models.models_v2 import User
from ..schemas_v2.landing import LangEnum
from ..schemas_v2.slider import (
    SlidesResponse, SlidesUpdateRequest,
)
from ..services_v2 import slider_service

router = APIRouter()


@router.get("/{language}", response_model=SlidesResponse)
def api_get_slides(language: LangEnum, db: Session = Depends(get_db)):
    """
    Публичный эндпоинт – слайды главной страницы для региона.
    Кешировать можно смело.
    """
    slides = slider_service.get_slides(db, language.value)
    return {"slides": slides}


@router.put("/admin/{language}",
            response_model=SlidesResponse)
def api_save_slides(language: LangEnum,
                    req: SlidesUpdateRequest,
                    db: Session = Depends(get_db),
                    current_admin: User = Depends(require_roles("admin"))):
    """
    Админ-эндпоинт: принимает массив, полностью заменяя
    слайды данного региона (языка).
    """
    slides = slider_service.save_slides(db, language.value, req.slides)
    return {"slides": slides}
