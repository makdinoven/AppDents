import datetime as _dt
import logging
import random
from collections import Counter
from typing import List, Optional, Tuple

from sqlalchemy import func, case, Float, cast
from sqlalchemy.orm import Session, selectinload

from .user_service import add_partial_course_to_user
from ..models.models_v2 import (
    User, SpecialOffer, Landing, landing_course, Tag, Course, Purchase, FreeCourseSource
)


logger = logging.getLogger(__name__)

_OFFER_TTL_HOURS = 24
_INTERVAL_HOURS  = 48         # каждые 3 суток
_HISTORY_LIMIT = 5
BATCH = 600


def _cheapest_landings_for_purchased(db: Session, user: User) -> list[Landing]:
    """Возвращает дешёвые лендинги по каждому купленному курсу."""
    purchased_course_ids = {p.course_id for p in user.purchases if p.course_id}
    if not purchased_course_ids:
        return []

    landings = (
        db.query(Landing)
        .join(landing_course, landing_course.c.landing_id == Landing.id)
        .filter(
            landing_course.c.course_id.in_(purchased_course_ids),
            Landing.is_hidden.is_(False),
        )
        .options(selectinload(Landing.tags))
        .order_by(cast(Landing.new_price, Float))
        .all()
    )

    # возьмём по одному лендингу на курс с минимальной ценой
    cheapest_by_course = {}
    for l in landings:
        for cid in l.course_ids:
            if cid in purchased_course_ids and cid not in cheapest_by_course:
                cheapest_by_course[cid] = l
    return list(cheapest_by_course.values())


def _preferred_lang(user: User) -> str | None:
    """
    Берём самый частый язык лендингов купленных курсов.
    Пустые/None не учитываются.
    """
    langs = Counter(
        p.landing.language
        for p in user.purchases
        if p.landing and p.landing.language
    )
    return langs.most_common(1)[0][0] if langs else None


def _pick_offer_landing(db: Session, user: User) -> Optional[Tuple[Landing, Course]]:
    """
    1.  Если есть покупки → подбираем лендинг по самым «весомым» тегам
        (cheapest-by-tag) и языку пользователя. Берём случайный лендинг
        из TOP-10 по продажам.
    2.  Если подходящих тегов нет → берём случайный лендинг из TOP-20
        по продажам.
    3.  Курс «отбрасывается», если уже:
        • куплен            • в partial-доступе
        • активный оффер    • когда-либо предлагался ранее
    """

    # ---------- 1.  «запрещённые» курсы ----------
    purchased     = {p.course_id for p in user.purchases if p.course_id}
    partial_ids   = set(user.partial_course_ids or [])
    active_ids    = set(user.active_special_offer_ids or [])
    # теперь учитываем *всю* историю спец-офферов
    offered_ids   = {so.course_id for so in user.special_offers}
    denied: set[int] = purchased | partial_ids | active_ids | offered_ids

    # ---------- 2.  язык, который пользователь покупал чаще всего ----------
    pref_lang = _preferred_lang(user)          # 'RU' / 'EN' / …  или None

    # вспомогательная функция: вернуть первый «не-denied» курс
    def _first_allowed(landing: Landing) -> Optional[Course]:
        for c in landing.courses:
            if c.id not in denied:
                return c
        return None

    # ---------- 3.  путь «по тегам» ----------
    cheapest = _cheapest_landings_for_purchased(db, user)
    if cheapest:
        # собираем веса тегов
        tag_weights: Counter[int] = Counter()
        for l in cheapest:
            for idx, t in enumerate(l.tags or []):
                tag_weights[t.id] += 3 if idx == 0 else 1

        if tag_weights:
            best_tag_id, _ = tag_weights.most_common(1)[0]

            q = (
                db.query(Landing)
                  .join(Landing.tags)
                  .filter(
                      Tag.id == best_tag_id,
                      Landing.is_hidden.is_(False),
                  )
                  .options(selectinload(Landing.courses))
                  .order_by(Landing.sales_count.desc())
                  .limit(10)
            )
            if pref_lang:
                q = q.filter(Landing.language == pref_lang)

            candidates = q.all()
            random.shuffle(candidates)          # случайный выбор из TOP-10
            for landing in candidates:
                course = _first_allowed(landing)
                if course:
                    return landing, course

    # ---------- 4.  общий «популярный» фолбэк ----------
    q = (
        db.query(Landing)
          .filter(Landing.is_hidden.is_(False))
          .options(selectinload(Landing.courses))
          .order_by(Landing.sales_count.desc())
          .limit(20)
    )
    if pref_lang:
        q = q.filter(Landing.language == pref_lang)

    top = q.all()
    random.shuffle(top)                         # случайный выбор из TOP-20
    for landing in top:
        course = _first_allowed(landing)
        if course:
            return landing, course

    # ничего не нашли
    return None



def _need_new_offer(user: User) -> bool:
    """
    Требуется ли выдавать новый оффер:
    • нет активных;
    • прошло ≥ 72 ч от created_at последнего оффера.
    """
    if not user.special_offers:
        return True
    last_offer = max(user.special_offers, key=lambda so: so.created_at)
    age = _dt.datetime.utcnow() - last_offer.created_at
    return age.total_seconds() >= _INTERVAL_HOURS * 3600


def generate_offer_for_user(db: Session, user: User) -> bool:
    """
    Если пора — создаёт спец-оффер.
    Возвращает True если оффер создан.
    """
    if not _need_new_offer(user):
        return False

    picked = _pick_offer_landing(db, user)
    if not picked:
        return False

    landing, course = picked
    expires_at = _dt.datetime.utcnow() + _dt.timedelta(hours=_OFFER_TTL_HOURS)
    offer = SpecialOffer(
        user_id=user.id,
        course_id=course.id,
        landing_id=landing.id,
        expires_at=expires_at,
    )
    db.add(offer)

    # открываем первый урок (как free-доступ, важно для фронта)
    try:
        add_partial_course_to_user(db, user.id, course.id, source=FreeCourseSource.SPECIAL_OFFER)
    except ValueError:
        # partial_already_granted и прочее игнорируем ­— оффер всё-равно остаётся
        logger.info("Partial already granted for user %s course %s", user.id, course.id)

    db.commit()
    logger.info("Special offer → user=%s course=%s until %s", user.id, course.id, expires_at)
    return True


def cleanup_expired_offers(db: Session) -> int:
    """Удаляет протухшие записи, возвращает кол-во."""
    now = _dt.datetime.utcnow()
    q = db.query(SpecialOffer).filter(SpecialOffer.expires_at <= now)
    count = q.count()
    if count:
        logger.debug("Cleaning %s expired special offers", count)
        q.delete(synchronize_session=False)
        db.commit()
    return count


def generate_offers_for_all_users(db: Session) -> None:
    q = (
        db.query(User)
          .options(selectinload(User.purchases),
                   selectinload(User.special_offers))
          .order_by(User.id)
    )
    offset = 0
    while True:
        chunk = q.limit(BATCH).offset(offset).all()
        if not chunk:
            break

        for u in chunk:
            try:
                generate_offer_for_user(db, u)
            except Exception:
                logger.exception("Special-offer generation failed for user %s", u.id)

        offset += BATCH

