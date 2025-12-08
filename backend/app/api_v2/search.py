from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..services_v2.search_service import search_everything
from ..schemas_v2.search import SearchResponse, SearchTypeEnum
from ..models.models_v2 import SearchQuery
from ..core.search_analytics import send_search_to_analytics

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
    # 1. Поиск
    result = search_everything(
        db,
        q=q,
        types=[t.value for t in types] if types else None,
        languages=languages,
    )

    # 2. Идентификаторы пользователя
    # здесь подставь свою логику получения текущего пользователя
    user_id = getattr(getattr(request, "state", None), "user_id", None)
    ip_address = request.client.host if request.client else None
    path = str(request.url.path)

    # 3. Проверка дубля за последние 2 минуты для этого же user_id/IP
    now = datetime.utcnow()
    two_minutes_ago = now - timedelta(minutes=2)

    should_skip = False
    id_filters = []
    if user_id is not None:
        id_filters.append(SearchQuery.user_id == user_id)
    if ip_address is not None:
        id_filters.append(SearchQuery.ip_address == ip_address)

    if id_filters:
        existing = (
            db.query(SearchQuery)
            .filter(
                SearchQuery.query == q,
                SearchQuery.path == path,
                SearchQuery.created_at >= two_minutes_ago,
                or_(*id_filters),
            )
            .first()
        )
        if existing:
            should_skip = True

    # 4. Если дубля нет — пишем запрос и шлём в аналитику
    if not should_skip:
        record = SearchQuery(
            query=q,
            path=path,
            user_id=user_id,
            ip_address=ip_address,
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        try:
            send_search_to_analytics(
                query=record.query,
                path=record.path,
                created_at=record.created_at,
            )
        except Exception:
            # ошибки внешней аналитики не ломают поиск
            pass

    return result
