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


# ─── core ───────────────────────────────────────────────────────────────────
def _pick_offer_landing(db: Session, user: User) -> tuple[Landing, Course] | None:
    """
    1.  Если у пользователя есть покупки – ищем лендинг по тегам
        («cheap-by-tag» путь). Берём случайный лендинг из TOP-10,
        который ещё не предлагался.
    2.  Если подходящих тегов нет – берём случайный лендинг из TOP-20
        по продажам.
    3.  В обоих случаях отбрасываем курсы из `denied`
        (куплены, partial, active-offer, recent-offer≤5).
    """

    # ---------- denied ----------
    purchased        = {p.course_id for p in user.purchases if p.course_id}
    recent_offer_ids = {
        so.course_id
        for so in sorted(
            user.special_offers, key=lambda so: so.created_at, reverse=True
        )[:_HISTORY_LIMIT]
    }
    partial_ids = set(user.partial_course_ids)
    active_ids  = set(user.active_special_offer_ids)
    denied: set[int] = purchased | recent_offer_ids | partial_ids | active_ids

    # ---------- основной язык ----------
    pref_lang = _preferred_lang(user)          # может быть None

    # --- helper: взять первый курс, который не в denied -------------------
    def _first_allowed(landing: Landing) -> Optional[Course]:
        for c in landing.courses:
            if c.id not in denied:
                return c
        return None

    # ---------- 1) путь «по тегам» ----------
    cheapest = _cheapest_landings_for_purchased(db, user)
    if cheapest:
        tag_weights: Counter[int] = Counter()
        for l in cheapest:
            for i, t in enumerate(l.tags or []):
                tag_weights[t.id] += 3 if i == 0 else 1

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

            cand = q.all()
            random.shuffle(cand)                    # ← ключевая разница
            for landing in cand:
                course = _first_allowed(landing)
                if course:
                    return landing, course

    # ---------- 2) общий fallback ----------
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
    random.shuffle(top)
    for landing in top:
        course = _first_allowed(landing)
        if course:
            return landing, course

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
    _trim_offer_history(db, user)
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



def _trim_offer_history(db: Session, user: User, limit: int = _HISTORY_LIMIT) -> None:
    """
    Сохраняет не более `limit` последних записей SpecialOffer.
    Старые записи удаляются, чтобы позже могли повторно попасть в оффер.
    """
    offers_sorted = sorted(user.special_offers, key=lambda so: so.created_at, reverse=True)
    excess = offers_sorted[limit:]
    for so in excess:
        db.delete(so)
    if excess:
        logger.debug("Trimmed %s old offers for user %s", len(excess), user.id)
        db.commit()
