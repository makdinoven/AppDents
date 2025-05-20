from datetime import datetime
from pydantic import BaseModel
from typing import List, Literal, Optional

class CartItemOut(BaseModel):
    id         : int
    item_type  : Literal["LANDING", "BOOK"]
    landing_id : Optional[int]
    book_id    : Optional[int]
    price      : float
    added_at   : datetime

    class Config:
        orm_mode = True

class CartResponse(BaseModel):
    total_amount : float
    updated_at   : datetime
    items        : List[CartItemOut]
