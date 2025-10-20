from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field

from ..schemas_v2.common import AuthorCardResponse

class LandingInCart(BaseModel):
    id            : int
    slug          : str                       = Field(..., alias="page_name")
    landing_name  : str
    preview_photo : Optional[str]
    course_ids    : List[int]
    authors       : List[AuthorCardResponse]
    old_price     : str
    new_price     : str

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class BookInCart(BaseModel):
    id: int
    page_name: str
    landing_name: str
    preview_photo: Optional[str] = None
    book_ids: List[int] = []
    authors: List[AuthorCardResponse] = []
    old_price: Optional[str] = None
    new_price: Optional[str] = None
    # Дополнительная информация о книгах (агрегируется из всех книг лендинга)
    total_pages: Optional[int] = None  # сумма страниц всех книг
    publishers: List[str] = []  # уникальные издатели
    publication_years: List[str] = []  # года публикаций


class CartItemOut(BaseModel):
    id         : int
    item_type  : Literal["LANDING","BOOK"] = "LANDING"
    added_at   : datetime
    landing    : Optional[LandingInCart]
    book: Optional[BookInCart] = None

    class Config:
        orm_mode = True

class CartResponse(BaseModel):
    total_amount                       : float
    total_old_amount                   : float
    total_new_amount : float
    current_discount                   : float  # в процентах, например 15.0
    next_discount                      : float  # в процентах, например 17.5
    total_amount_with_balance_discount : float
    updated_at                         : datetime
    items                              : List[CartItemOut]

    class Config:
        orm_mode = True
