from typing import List, Optional, Union, Literal
from pydantic import BaseModel, validator

from .landing import LandingCardResponse      # карточка курса из лендинга

# ----- PAYLOAD от админ-панели ------------------------------------------------
class FreeSlidePayload(BaseModel):
    id: Optional[int] = None
    type: Literal["FREE"] = "FREE"
    order_index: int
    bg_media_url: str
    title: str
    description: str
    target_url: str

class CourseSlidePayload(BaseModel):
    id: Optional[int] = None
    type: Literal["COURSE"] = "COURSE"
    order_index: int
    landing_id: Optional[int] = None
    landing_slug: Optional[str] = None        # page_name

    @validator("landing_id", always=True)
    def _check_id_or_slug(cls, v, values):
        if not v and not values.get("landing_slug"):
            raise ValueError("Нужно передать landing_id или landing_slug")
        return v

SlideUpdatePayload = Union[FreeSlidePayload, CourseSlidePayload]

class SlidesUpdateRequest(BaseModel):
    slides: List[SlideUpdatePayload]

# ----- ОТВЕТ клиенту ----------------------------------------------------------
class FreeSlideResponse(BaseModel):
    id: int
    type: Literal["FREE"]
    order_index: int
    bg_media_url: str
    title: str
    description: str
    target_url: str

class CourseSlideResponse(BaseModel):
    id: int
    type: Literal["COURSE"]
    order_index: int
    landing: LandingCardResponse
    main_text: str | None = None

SlideResponse = Union[FreeSlideResponse, CourseSlideResponse]

class SlidesResponse(BaseModel):
    slides: List[SlideResponse]
