"""
Сервис-слой слайдера главной страницы.
"""

import logging
from typing import List, Union, Dict

from sqlalchemy.orm import Session
from fastapi import HTTPException

from ..models.models_v2 import Slide, SlideType, Landing
from ..schemas_v2.slider import (
    SlideUpdatePayload, FreeSlidePayload, CourseSlidePayload,
)
from ..services_v2 import landing_service           # для _landing_to_card

log = logging.getLogger(__name__)


# ------------------ ПУБЛИЧНОЕ ОТОБРАЖЕНИЕ ------------------------------------
def _slide_to_dict(db: Session, slide: Slide) -> Dict:
    """
    Преобразует ORM Slide → словарь для ответа клиенту
    (schema-response соберёт сама pydantic).
    """
    if slide.type == SlideType.COURSE:
        # карточка лендинга
        if not slide.landing:
            raise HTTPException(status_code=500,
                                detail=f"Slide {slide.id}: landing not found")
        card = landing_service.landing_to_card(slide.landing)   # noqa
        return {
            "id": slide.id,
            "type": "COURSE",
            "order_index": slide.order_index,
            "landing": card,
        }

    # FREE / BOOK
    return {
        "id": slide.id,
        "type": slide.type.value,
        "order_index": slide.order_index,
        "bg_media_url": slide.bg_media_url,
        "title": slide.title,
        "description": slide.description,
        "target_url": slide.target_url,
    }


def get_slides(db: Session, language: str) -> List[Dict]:
    """
    Отдаёт активные слайды региона в нужном порядке.
    """
    slides = (db.query(Slide)
                .filter(Slide.language == language.upper(),
                        Slide.is_active.is_(True))
                .order_by(Slide.order_index)
                .all())
    return [_slide_to_dict(db, s) for s in slides]


# ------------------ АДМИН-ОБНОВЛЕНИЕ -----------------------------------------
def _resolve_landing(db: Session, payload: CourseSlidePayload) -> Landing:
    """
    Находит Landing по ID или slug (page_name).
    """
    if payload.landing_id:
        landing = db.query(Landing).get(payload.landing_id)
    else:
        landing = db.query(Landing).filter(
            Landing.page_name == payload.landing_slug).first()
    if not landing:
        raise HTTPException(status_code=404,
                            detail="Landing not found for COURSE-slide")
    return landing


def save_slides(
    db: Session,
    language: str,
    slides_payload: List[SlideUpdatePayload],
):
    """
    Полностью заменяет слайды региона списком,
    пришедшим с фронта - «клик по Save» в админ-панели.
    Делается транзакционно: либо все изменения, либо ничего.
    """
    language = language.upper()
    log.info("[SLIDER] Saving %d slides for %s", len(slides_payload), language)

    # 1. Деактивируем/удаляем старые
    db.query(Slide).filter(Slide.language == language).delete()
    db.flush()          # удаляем, чтобы индексы не конфликтовали

    # 2. Создаём заново в пришедшем порядке
    for idx, payload in enumerate(slides_payload, start=1):
        if payload.type == "FREE":
            p: FreeSlidePayload = payload          # для mypy
            slide = Slide(
                language    = language,
                order_index = idx,
                type        = SlideType.FREE,
                bg_media_url = p.bg_media_url,
                title        = p.title,
                description  = p.description,
                target_url   = p.target_url,
            )
        else:   # COURSE
            p: CourseSlidePayload = payload
            landing = _resolve_landing(db, p)
            slide = Slide(
                language    = language,
                order_index = idx,
                type        = SlideType.COURSE,
                landing_id  = landing.id,
            )
        db.add(slide)

    db.commit()
    log.info("[SLIDER] %s: saved successfully", language)
    # отдаём свежие данные
    return get_slides(db, language)
