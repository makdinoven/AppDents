from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field

# импортим ответ авторов из landing-схем
from ..schemas_v2.landing import AuthorCardResponse

class LandingInCart(BaseModel):
    id           : int
    slug         : str                       = Field(..., alias="page_name")
    landing_name : str
    preview_photo: Optional[str]
    course_ids   : List[int]
    authors      : List[AuthorCardResponse]
    old_price : str
    new_price : str

    class Config:
        orm_mode = True
        allow_population_by_field_name = True

class CartItemOut(BaseModel):
    id          : int
    item_type   : Literal["LANDING","BOOK"]
    landing_id  : Optional[int]
    book_id     : Optional[int]
    added_at    : datetime
    # ← новое поле со всей информацией о лендинге
    landing     : Optional[LandingInCart]

    class Config:
        orm_mode = True

class CartResponse(BaseModel):
    total_amount : float
    updated_at   : datetime
    items        : List[CartItemOut]

    class Config:
        orm_mode = True
