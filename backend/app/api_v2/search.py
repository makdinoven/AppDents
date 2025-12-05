from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..services_v2.search_service import search_everything
from ..schemas_v2.search import SearchResponse, SearchTypeEnum

from ..models.models_v2 import SearchQuery
from ..core.search_analytics import send_search_to_analytics  # см. ниже, заглушка

router = APIRouter()


@router.get(
    "/v2",
    response_model=SearchResponse,
    summary="Глобальный поиск: авторы, курсы (лендинги), книги (книжные лендинги)",
)
def search_v2(
    request: Request,
    q: str = Query(
        ...,
        min_length=1,
        max_length=200,
        description="Поисковая строка",
    ),
    types: Optional[List[SearchTypeEnum]] = Query(
        None,
        description="Фильтр типов: authors, landings, book_landings (мультивыбор)",
    ),
    languages: Optional[List[str]] = Query(
        None,
        description="Фильтр по языкам (мультивыбор): EN, RU, ES, PT, AR, IT",
    ),

    db: Session = Depends(get_db),
):
    # 1. Обычный поиск, как и раньше
    result = search_everything(
        db,
        q=q,
        types=[t.value for t in types] if types else None,
        languages=languages,
    )

    # 2. Логируем запрос (БЕЗ user_id и ip, только текст и путь)
    record = SearchQuery(
        query=q,
        path=str(request.url.path),
    )
    db.add(record)
    db.commit()
    # можно не делать refresh, если created_at тебе здесь не нужен
    db.refresh(record)

    # 3. (Опционально) сразу отправить в внешнюю аналитику
    try:
        send_search_to_analytics(
            query=record.query,
            path=record.path,
            created_at=record.created_at,
        )
    except Exception:
        # чтобы любая проблема с аналитикой не ломала поиск
        pass

    return result
