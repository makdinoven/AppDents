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

MIN_LEN = 3               # минимальная длина запроса
MIN_DELAY_SECONDS = 5     # минимальная пауза между шагами набора

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

    # 2. Слишком короткие запросы не логируем вовсе
    if len(q.strip()) < MIN_LEN:
        return result

    # 3. Идентификаторы пользователя
    user_id = getattr(getattr(request, "state", None), "user_id", None)
    ip_address = request.client.host if request.client else None
    path = str(request.url.path)

    now = datetime.utcnow()
    two_minutes_ago = now - timedelta(minutes=2)

    # 4. Берём последний запрос этого же IP/юзера на этот же path
    last_filters = [SearchQuery.path == path]
    id_filters = []
    if user_id is not None:
        id_filters.append(SearchQuery.user_id == user_id)
    if ip_address is not None:
        id_filters.append(SearchQuery.ip_address == ip_address)
    if id_filters:
        last_filters.append(or_(*id_filters))

    last_query = None
    if id_filters:
        last_query = (
            db.query(SearchQuery)
            .filter(*last_filters)
            .order_by(SearchQuery.created_at.desc())
            .first()
        )

    should_skip = False

    if last_query is not None:
        delta = now - last_query.created_at.replace(tzinfo=None)

        # если новый запрос просто ДОПИСЫВАЕТ старый (старый префикс нового)
        if (
                delta.total_seconds() < MIN_DELAY_SECONDS
                and last_query.query.startswith(q)
        ):
            # это шаг "удаления" букв — возможно, пропустить
            should_skip = True

        # плюс старая защита от точных дублей за 2 минуты
        if (
            not should_skip
            and last_query.query == q
            and (now - last_query.created_at.replace(tzinfo=None)) < (now - two_minutes_ago)
        ):
            should_skip = True

    # 5. Если не решили пропустить — логируем и шлём в аналитику
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
            pass

    return result
