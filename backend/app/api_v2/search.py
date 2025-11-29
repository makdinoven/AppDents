from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..services_v2.search_service import search_everything
from ..schemas_v2.search import SearchResponse, SearchTypeEnum

router = APIRouter()

@router.get(
    "/v2",
    response_model=SearchResponse,
    summary="Глобальный поиск: авторы, курсы (лендинги), книги (книжные лендинги)"
)
def search_v2(
    q: str = Query(..., min_length=1, max_length=200, description="Поисковая строка"),
    types: Optional[List[SearchTypeEnum]] = Query(
        None,
        description="Фильтр типов: authors, landings, book_landings (мультивыбор)"
    ),
    languages: Optional[List[str]] = Query(
        None,
        description="Фильтр по языкам (мультивыбор): EN, RU, ES, PT, AR, IT"
    ),
    db: Session = Depends(get_db),
):
    return search_everything(
        db,
        q=q,
        types=[t.value for t in types] if types else None,
        languages=languages,
    )