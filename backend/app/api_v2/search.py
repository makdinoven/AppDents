from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..services_v2.search_service import search_everything
from ..schemas_v2.search import SearchResponse, SearchTypeEnum
from ..models.models_v2 import SearchQuery
from ..utils.ip_utils import get_client_ip

router = APIRouter()

MIN_LEN = 3               # минимальная длина запроса для логирования
MIN_DELAY_SECONDS = 15     # если меньше — обновляем последнюю запись


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

    # 2. Отсекаем совсем короткие запросы
    if len(q.strip()) < MIN_LEN:
        return result

    # 3. Идентификаторы пользователя
    user_id = getattr(getattr(request, "state", None), "user_id", None)
    ip_address = ip_address = get_client_ip(request)
    path = str(request.url.path)

    now = datetime.utcnow()

    # 4. Находим последнюю запись этого юзера/IP на этот path
    filters = [SearchQuery.path == path]
    id_filters = []
    if user_id is not None:
        id_filters.append(SearchQuery.user_id == user_id)
    if ip_address is not None:
        id_filters.append(SearchQuery.ip_address == ip_address)
    if id_filters:
        filters.append(or_(*id_filters))

    last_record = None
    if id_filters:
        last_record = (
            db.query(SearchQuery)
            .filter(*filters)
            .order_by(SearchQuery.created_at.desc())
            .first()
        )

    record = None

    if last_record is not None:
        delta = now - last_record.created_at.replace(tzinfo=None)

        if delta.total_seconds() < MIN_DELAY_SECONDS:
            # Быстрый набор: считаем это продолжением прошлой строки.
            # Обновляем текст запроса у последней записи на новый q.
            last_record.query = q
            record = last_record
        else:
            # Пауза достаточно большая — начинаем новую "сессию" запроса.
            record = SearchQuery(
                query=q,
                path=path,
                user_id=user_id,
                ip_address=ip_address,
            )
            db.add(record)
    else:
        # Первая запись для этого юзера/IP
        record = SearchQuery(
            query=q,
            path=path,
            user_id=user_id,
            ip_address=ip_address,
        )
        db.add(record)

    db.commit()
    db.refresh(record)

    return result
