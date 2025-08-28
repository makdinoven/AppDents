from typing import List, Literal, Optional, Union
from pydantic import BaseModel
from enum import Enum

class SearchTypeEnum(str, Enum):
    authors = "authors"
    landings = "landings"
    book_landings = "book_landings"

class SearchAuthorItem(BaseModel):
    type: Literal["author"] = "author"
    id: int
    name: str
    photo: Optional[str] = None
    language: str

class SearchLandingItem(BaseModel):
    type: Literal["landing"] = "landing"
    id: int
    landing_name: Optional[str] = None
    page_name: str
    preview_photo: Optional[str] = None
    old_price: Optional[str] = None
    new_price: Optional[str] = None
    language: str
    authors: List[dict]

class SearchBookLandingItem(BaseModel):
    type: Literal["book_landing"] = "book_landing"
    id: int
    landing_name: Optional[str] = None
    page_name: str
    preview_photo: Optional[str] = None
    old_price: Optional[str] = None
    new_price: Optional[str] = None
    language: str
    book_title: Optional[str] = None
    cover_url: Optional[str] = None
    authors: List[dict]

class SearchCounts(BaseModel):
    authors: int
    landings: int
    book_landings: int

class SearchResponse(BaseModel):
    counts: SearchCounts          # найдено по каждому типу (после фильтров, до урезания по limit)
    total: int                    # сумма counts.*
    returned: int                 # сколько реально отдали (≤ limit)
    limit: int                    # применённый лимит
    truncated: bool               # были ли урезания по лимиту
    authors: List[SearchAuthorItem]
    landings: List[SearchLandingItem]
    book_landings: List[SearchBookLandingItem]
