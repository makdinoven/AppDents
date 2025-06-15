import copy
from datetime import datetime, timedelta, date
from math import ceil
import time
from typing import List, Optional

from sqlalchemy import (
    func, or_, desc, Date, cast, select,
)
from sqlalchemy.types import Float
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, Query
from fastapi import HTTPException

from .preview_service import get_or_schedule_preview
from ..models.models_v2 import (
    Landing,
    Author,
    Course,
    Tag,
    Purchase,
    AdVisit,
    users_courses,
)
from ..schemas_v2.landing import LandingCreate, LandingUpdate, LangEnum


# 1. Все курсы, которые уже принадлежат пользователю
def _user_course_ids(db: Session, user_id: int) -> list[int]:
    """Возвращает уникальные course_id, которыми владеет пользователь."""
    direct = db.query(users_courses.c.course_id).filter(
        users_courses.c.user_id == user_id
    )
    via_pur = (
        db.query(Purchase.course_id)
        .filter(Purchase.user_id == user_id, Purchase.course_id.isnot(None))
    )
    return list({row[0] for row in direct.union(via_pur).all()})

# 2. Превращаем ORM‑объект Landing → ответную «карточку»
def _landing_to_card(landing: Landing) -> dict:
    return {
        "id": landing.id,
        "first_tag": landing.tags[0].name if landing.tags else None,
        "landing_name": landing.landing_name,
        "authors": [
            {"id": a.id, "name": a.name, "photo": a.photo} for a in landing.authors
        ],
        "slug": landing.page_name,
        "lessons_count": landing.lessons_count,
        "main_image": landing.preview_photo,
        "old_price": landing.old_price,
        "new_price": landing.new_price,
        "course_ids": [c.id for c in landing.courses],
    }

# 3. Формула процента скидки, пригодная в ORDER BY
def _discount_expr():
    old = cast(Landing.__table__.c.old_price, Float())
    new = cast(Landing.__table__.c.new_price, Float())
    return ((old - new) / old) * 100

# 4. Базовый SELECT по лендингам + обнуление истёкших реклам
def reset_expired_ad_flags(db: Session):
    updated = (
        db.query(Landing)
        .filter(
            Landing.in_advertising.is_(True),
            Landing.ad_flag_expires_at < func.utc_timestamp(),
        )
        .update(
            {Landing.in_advertising: False, Landing.ad_flag_expires_at: None},
            synchronize_session=False,
        )
    )
    if updated:
        db.commit()

def _base_landing_query(db: Session) -> Query:
    """Общий базовый запрос: не скрытые лендинги."""
    reset_expired_ad_flags(db)
    return db.query(Landing).filter(Landing.is_hidden.is_(False))


# 5. Фильтры и сортировки, применяемые «конвейером»
def _apply_common_filters(
    query: Query,
    *,
    language: str | None = None,
    tags: List[str] | None = None,
    search_q: str | None = None,
) -> Query:
    if language:
        query = query.filter(Landing.language == language.upper().strip())
    if tags:
        query = query.join(Landing.tags).filter(Tag.name.in_(tags))
    if search_q:
        ilike_q = f"%{search_q}%"
        query = query.filter(
            or_(Landing.landing_name.ilike(ilike_q), Landing.page_name.ilike(ilike_q))
        )
    return query


_SORT_MAP = {
    "popular": Landing.sales_count.desc(),
    "discount": _discount_expr().desc(),
    "new": Landing.id.desc(),
}

def _apply_sort(query: Query, sort: str | None) -> Query:
    expr = _SORT_MAP.get((sort or "").lower())
    return query.order_by(expr) if expr is not None else query.order_by(Landing.id)



# 6. Исключение уже купленных курсов
def _exclude_bought(
    query: Query,
    bought_courses: list[int],
    bought_landings: set[int],
) -> Query:
    if bought_courses:
        query = query.filter(~Landing.courses.any(Course.id.in_(bought_courses)))
    if bought_landings:
        query = query.filter(~Landing.id.in_(bought_landings))
    return query


# -------------------- ПАГИНАЦИЯ ОБЩЕГО НАЗНАЧЕНИЯ ---------------------------

def _paginate(query: Query, *, page: int, size: int) -> dict:
    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    return {
        "total": total,
        "total_pages": ceil(total / size) if total else 0,
        "page": page,
        "size": size,
        "items": items,
    }


# ------------------ PUBLIC LIST / SEARCH ЭНД‑ПОИНТЫ -------------------------

def list_landings_paginated(
    db: Session, *, language: Optional[LangEnum], page: int = 1, size: int = 10
) -> dict:
    q = db.query(Landing).order_by(desc(Landing.id))        # новые сверху
    if language:                                                # фильтр, если задан
        q = q.filter(Landing.language == language.value)
    return _paginate(q, page=page, size=size)


def search_landings_paginated(
    db: Session,
    *,
    q: str,
    language: Optional[LangEnum],
    page: int = 1,
    size: int = 10,
) -> dict:
    query = _apply_common_filters(
        _base_landing_query(db), language=language.value if language else None, search_q=q
    )
    query = _apply_sort(query, "new")
    return _paginate(query, page=page, size=size)


# --------------------- CRUD ОПЕРАЦИИ ДЛЯ АДМИНКИ ---------------------------

def get_landing_detail(db: Session, landing_id: int) -> Landing:
    landing = db.query(Landing).filter(Landing.id == landing_id).first()
    if not landing:
        raise HTTPException(status_code=404, detail="Landing not found")
    return landing

def create_landing(db: Session, landing_data: LandingCreate) -> Landing:
    new_landing = Landing(
        page_name = landing_data.page_name,
        language = landing_data.language,
        landing_name = landing_data.landing_name,
        old_price = landing_data.old_price,
        new_price = landing_data.new_price,
        course_program = landing_data.course_program,
        lessons_info = landing_data.lessons_info,
        preview_photo = landing_data.preview_photo,
        sales_count = landing_data.sales_count,
        duration = landing_data.duration,
        lessons_count = landing_data.lessons_count,
        is_hidden=landing_data.is_hidden or False,
    )
    db.add(new_landing)
    db.commit()
    db.refresh(new_landing)
    # Привязка авторов через ассоциативную таблицу landing_authors
    if landing_data.author_ids:
        authors = db.query(Author).filter(Author.id.in_(landing_data.author_ids)).all()
        new_landing.authors = authors
    # Привязка курсов через ассоциативную таблицу landing_course
    if landing_data.course_ids:
        courses = db.query(Course).filter(Course.id.in_(landing_data.course_ids)).all()
        new_landing.courses = courses
    db.commit()
    db.refresh(new_landing)
    if landing_data.tag_ids:
        tags = db.query(Tag).filter(Tag.id.in_(landing_data.tag_ids)).all()
        new_landing.tags = tags
    # Если landing_name не задано, обновляем его автоматически
    if not new_landing.landing_name:
        new_landing.landing_name = f"Landing name {new_landing.id}"
        db.commit()
        db.refresh(new_landing)
    return new_landing


def update_landing(db: Session, landing_id: int, update_data: LandingUpdate) -> Landing:
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Используем with_for_update() для явной блокировки строки
            landing = db.query(Landing).filter(Landing.id == landing_id).with_for_update().first()
            if not landing:
                raise HTTPException(status_code=404, detail="Landing not found")

            if update_data.page_name is not None:
                landing.page_name = update_data.page_name
            if update_data.landing_name is not None:
                landing.landing_name = update_data.landing_name
            if update_data.old_price is not None:
                landing.old_price = update_data.old_price
            if update_data.new_price is not None:
                landing.new_price = update_data.new_price
            if update_data.course_program is not None:
                landing.course_program = update_data.course_program
            if update_data.lessons_info is not None:
                landing.lessons_info = [
                    {k: v.dict() if hasattr(v, "dict") else v for k, v in lesson_item.items()}
                    for lesson_item in update_data.lessons_info
                ]
            if update_data.preview_photo is not None:
                landing.preview_photo = update_data.preview_photo
            if update_data.sales_count is not None:
                landing.sales_count = update_data.sales_count
            if update_data.language is not None:
                landing.language = update_data.language
            if update_data.author_ids is not None:
                authors = db.query(Author).filter(Author.id.in_(update_data.author_ids)).all()
                landing.authors = authors
            if update_data.course_ids is not None:
                courses = db.query(Course).filter(Course.id.in_(update_data.course_ids)).all()
                landing.courses = courses
            if update_data.tag_ids is not None:
                tags = db.query(Tag).filter(Tag.id.in_(update_data.tag_ids)).all()
                landing.tags = tags
            if update_data.duration is not None:
                landing.duration = update_data.duration
            if update_data.lessons_count is not None:
                landing.lessons_count = update_data.lessons_count
            if update_data.is_hidden is not None:
                landing.is_hidden = update_data.is_hidden
            db.commit()
            db.refresh(landing)
            return landing
        except OperationalError as e:
            db.rollback()
            if "Lock wait timeout exceeded" in str(e):
                if attempt < max_retries - 1:
                    time.sleep(1)  # небольшая задержка перед повторной попыткой
                    continue
            raise HTTPException(status_code=500, detail=f"Update failed: {e}")
    raise HTTPException(status_code=500, detail="Unable to update landing due to lock wait timeout")


def delete_landing(db: Session, landing_id: int) -> None:
    landing = db.query(Landing).filter(Landing.id == landing_id).first()
    if not landing:
        raise HTTPException(status_code=404, detail="Landing not found")
    # Очистка связей с курсами (через landing_course) и с авторами (через landing_authors)
    landing.courses = []
    landing.authors = []
    landing.tags = []
    db.delete(landing)
    db.commit()




def get_landing_cards(
    db: Session,
    *,
    skip: int = 0,
    limit: int = 20,
    tags: Optional[List[str]] = None,
    sort: Optional[str] = None,
    language: Optional[str] = None,
) -> dict:
    query = _apply_sort(
        _apply_common_filters(_base_landing_query(db), language=language, tags=tags),
        sort,
    )
    total = query.count()
    landings = query.offset(skip).limit(limit).all()
    return {"total": total, "cards": [_landing_to_card(l) for l in landings]}


def get_landing_cards_pagination(
    db: Session,
    *,
    page: int = 1,
    size: int = 20,
    tags: Optional[List[str]] = None,
    sort: Optional[str] = None,
    language: Optional[str] = None,
    q: Optional[str] = None,
    single_course: bool = False,
) -> dict:
    query = _apply_common_filters(
        _base_landing_query(db), language=language, tags=tags, search_q=q
    )
    query = query.join(Landing.courses).group_by(Landing.id)
    if single_course:
        query = query.having(func.count(Course.id) == 1)
    query = _apply_sort(query, sort)

    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    return {
        "total": total,
        "total_pages": ceil(total / size) if total else 0,
        "page": page,
        "size": size,
        "cards": [_landing_to_card(l) for l in items],
    }

def get_purchases_by_language(
    db: Session,
    start_dt: datetime,
    end_dt: datetime,
):
    """
    Возвращает список словарей:
      [ {"language": "EN", "count": 10}, "total_amount": 1234.56 ]
    за период [start_dt, end_dt).
    """
    query = (
        db.query(
            Landing.language.label("language"),
            func.count(Purchase.id).label("purchase_count"),
            func.coalesce(func.sum(Purchase.amount), 0).label("total_amount"),
        )
        .join(Purchase, Purchase.landing_id == Landing.id)
        .filter(
            Purchase.created_at >= start_dt,
            Purchase.created_at < end_dt,
        )
        .group_by(Landing.language)
    )
    results = query.all()

    return [
        {"language": row.language, "count": row.purchase_count, "total_amount": f"{row.total_amount:.2f} $"}
        for row in results
    ]

def check_and_reset_ad_flag(landing: Landing, db: Session):
    """
    Если у лендинга in_advertising=True, но ad_flag_expires_at < now,
    сбрасываем in_advertising в False.
    """
    if landing.in_advertising and landing.ad_flag_expires_at:
        now = datetime.utcnow()
        if landing.ad_flag_expires_at < now:
            landing.in_advertising = False
            landing.ad_flag_expires_at = None

def get_top_landings_by_sales(
    db: Session,
    language: Optional[str] = None,
    limit: int = 10,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
):
    reset_expired_ad_flags(db)

    # если есть хотя бы одна дата — считаем реальный sales
    if start_date or end_date:
        subq = (
            db.query(
                Purchase.landing_id.label("landing_id"),
                func.count(Purchase.id).label("sales"),
            )
            .filter(Purchase.landing_id.isnot(None))
        )

        # приводим created_at → date и фильтруем
        if start_date:
            subq = subq.filter(
                cast(Purchase.created_at, Date) >= start_date
            )
        if end_date:
            subq = subq.filter(
                cast(Purchase.created_at, Date) <= end_date
            )

        subq = subq.group_by(Purchase.landing_id).subquery()

        q = (
            db.query(Landing, subq.c.sales)
            .join(subq, subq.c.landing_id == Landing.id)
            .filter(Landing.is_hidden.is_(False))
        )
        if language:
            q = q.filter(Landing.language == language)

        result = q.order_by(subq.c.sales.desc()).limit(limit).all()

    else:
        # старое поведение: агрегированное поле
        q = (
            db.query(Landing, Landing.sales_count.label("sales"))
            .filter(Landing.is_hidden.is_(False))
        )
        if language:
            q = q.filter(Landing.language == language)

        result = q.order_by(Landing.sales_count.desc()).limit(limit).all()

    db.commit()
    return result


AD_TTL = timedelta(hours=3)

def track_ad_visit(db: Session, landing_id: int, fbp: str | None, fbc: str | None, ip: str):
    visit = AdVisit(
        landing_id=landing_id,
        fbp=fbp,
        fbc=fbc,
        ip_address=ip,
    )
    db.add(visit)

    landing = db.query(Landing).filter(Landing.id == landing_id).first()
    if landing:
        landing.in_advertising = True
        landing.ad_flag_expires_at = datetime.utcnow() + AD_TTL
    db.commit()

def get_cheapest_landing_for_course(db: Session, course_id: int) -> Landing | None:
    """
    Возвращает объект Landing с минимальным new_price
    для заданного course_id. Скрытые лендинги (is_hidden=True)
    игнорируются.  new_price приводим к float для корректного сравнения.
    """
    rows = (
        db.query(Landing)
          .join(Landing.courses)
          .filter(
              Course.id == course_id,
              Landing.is_hidden == False,
          )
          .all()
    )
    if not rows:
        return None

    def _price(landing: Landing) -> float:
        try:
            return float(landing.new_price)
        except Exception:
            return float("inf")

    return min(rows, key=_price)

def _fallback_landing_cards(
    db: Session,
    user_id: int,
    skip: int,
    limit: int,
    language: str | None,
) -> dict:
    b_courses = _user_course_ids(db, user_id)
    b_landings = _user_landing_ids(db, user_id)

    query = _exclude_bought(_base_landing_query(db), b_courses, b_landings)
    query = _apply_common_filters(query, language=language)

    landings = (
        query.order_by(Landing.sales_count.desc()).offset(skip).limit(limit).all()
    )
    return {"total": len(landings), "cards": [_landing_to_card(l) for l in landings]}


# ---------------------------  COLLAB‑FILTER  --------------------------------

# ---------------------------  COLLAB-FILTER  --------------------------------
def get_recommended_landing_cards(
    db: Session,
    *,
    user_id: int,
    skip: int = 0,
    limit: int = 20,
    language: str | None = None,
) -> dict:
    # --- 0.  что пользователь уже купил -----------------------------------
    b_courses  = _user_course_ids(db, user_id)    # список course_id
    b_landings = _user_landing_ids(db, user_id)   # set   landing_id

    # если нет ни одного купленного курса — отдаём fallback
    if not b_courses:
        return _fallback_landing_cards(db, user_id, skip, limit, language)

    # --- 1.  ищем похожих пользователей, считаем score --------------------
    similar_users = (
        db.query(users_courses.c.user_id)
          .filter(users_courses.c.course_id.in_(b_courses),
                  users_courses.c.user_id != user_id)
          .distinct()
          .subquery()
    )

    overlap = func.count(func.distinct(users_courses.c.user_id))
    score   = (cast(func.count(), Float) / func.nullif(overlap, 0)).label("score")

    rec_q = (
        db.query(users_courses.c.course_id.label("cid"), score)
          .filter(users_courses.c.user_id.in_(select(similar_users)),
                  ~users_courses.c.course_id.in_(b_courses))
          .group_by(users_courses.c.course_id)
          .order_by(score.desc())
    )

    # --- 2.  отбираем уникальные лендинги с учётом skip/limit -------------
    unique_ids: set[int] = set()
    cards: list[dict] = []
    passed = 0          # сколько уникальных лендингов «пропустили» для skip

    for row in rec_q.yield_per(200):
        landing = get_cheapest_landing_for_course(db, row.cid)
        if not landing or (language and landing.language != language.upper()):
            continue
        if landing.id in unique_ids:
            continue
        unique_ids.add(landing.id)

        if passed < skip:          # фаза пропуска
            passed += 1
            continue

        cards.append(_landing_to_card(landing))
        if len(cards) == limit:
            break

    # --- 3.  добираем fallback, если нужно --------------------------------
    if len(cards) < limit:
        extra = _fallback_landing_cards(
            db, user_id, skip=0, limit=limit - len(cards), language=language
        )["cards"]
        cards.extend(extra)

    # --- 4.  total: все НЕкупленные лендинги ------------------------------
    total_q = _exclude_bought(_base_landing_query(db), b_courses, b_landings)
    if language:
        total_q = total_q.filter(Landing.language == language.upper())
    total = total_q.count()

    return {"total": total, "cards": cards}




# -------------------------  ОБЩИЙ ЭНД‑ПОИНТ  --------------------------------

def get_personalized_landing_cards(
    db: Session,
    *,
    user_id: int,
    skip: int = 0,
    limit: int = 20,
    tags: Optional[List[str]] = None,
    sort: str = "popular",  # popular | new | discount | recommend
    language: Optional[str] = None,
) -> dict:
    if sort.lower() == "recommend":
        return get_recommended_landing_cards(
            db, user_id=user_id, skip=skip, limit=limit, language=language
        )

    b_courses = _user_course_ids(db, user_id)
    b_landings = _user_landing_ids(db, user_id)

    query = _exclude_bought(
        _apply_common_filters(_base_landing_query(db), language=language, tags=tags),
        b_courses,
        b_landings,
    )

    query = _apply_sort(query, sort)

    total = query.count()
    landings = query.offset(skip).limit(limit).all()
    return {"total": total, "cards": [_landing_to_card(l) for l in landings]}

def get_landing_detail_with_previews(db: Session, landing_id: int) -> dict:
    """
    Возвращает словарь с полной информацией о лендинге,
    где в lessons_info каждому уроку добавлено поле preview.
    """
    landing: Landing | None = (
        db.query(Landing).filter(Landing.id == landing_id).first()
    )
    if not landing:
        raise HTTPException(status_code=404, detail="Landing not found")

    # ------- копируем lessons_info и вставляем превью --------
    lessons_src = landing.lessons_info or []          # JSON → list[dict]
    lessons_out = []

    for item in lessons_src:
        key, lesson = next(iter(item.items()))
        lesson_copy = copy.deepcopy(lesson)

        video_link = lesson_copy.get("link") or lesson_copy.get("video_link")
        # если ссылки нет — просто передаём как есть
        if video_link:
            lesson_copy["preview"] = get_or_schedule_preview(db, video_link)

        lessons_out.append({key: lesson_copy})

    # ------- собираем финальный ответ --------
    return {
        "id": landing.id,
        "page_name": landing.page_name,
        "landing_name": landing.landing_name,
        "old_price": landing.old_price,
        "new_price": landing.new_price,
        "course_program": landing.course_program,
        "lessons_info": lessons_out,
        "preview_photo": landing.preview_photo,
        "sales_count": landing.sales_count,
        "duration": landing.duration,
        "lessons_count": landing.lessons_count,
        "authors": [a.name for a in landing.authors],
        "course_ids": landing.course_ids,
        "tag_ids": [t.id for t in landing.tags],
        "language": landing.language,
        "in_advertising": landing.in_advertising,
    }

def _user_landing_ids(db: Session, user_id: int) -> set[int]:
    """Все landing.id, которые пользователь купил напрямую."""
    rows = (
        db.query(Purchase.landing_id)
          .filter(Purchase.user_id == user_id,
                  Purchase.landing_id.isnot(None))
          .all()
    )
    return {r[0] for r in rows}
