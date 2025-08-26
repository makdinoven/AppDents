from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field

from ..schemas_v2.landing import AuthorCardResponse

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
    title: str
    slug: str
    cover_url: Optional[str] = None
    class Config:
        orm_mode = True

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
