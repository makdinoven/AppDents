import datetime as _dt
import logging
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


def _pick_offer_landing(
    db: Session,
    user: User,
) -> Optional[Tuple[Landing, Course]]:
    """
    Возвращает (landing, course) для спец-предложения или None.

    Алгоритм
    --------
    1.  Если у пользователя уже есть покупки — собираем «дешёвые» лендинги
        по этим курсам и считаем веса тегов (`+3` за первый тег, `+1` за остальные).
        Берём до 20 самых продаваемых лендингов по самому популярному тегу
        и выбираем из них курс, который **не** входит в `denied`.

    2.  Если подходящего лендинга/курса по тегу нет или покупок вовсе нет —
        берём топ-50 лендингов по продажам и пытаемся выбрать курс из них.

    3.  Ротация.
        Чтобы спец-офферы не «залипали» на одном курсе, смещаем выбор
        на `shift = len(user.special_offers) % len(landings)`.
        Так каждый новый оффер проходит список лендингов по кругу.

    4.  Курс не должен быть в `denied` = куплен ∨ partial ∨ активный offer ∨ 5 последних offer-ов.
    """
    # ────────────────────── denied ──────────────────────
    purchased   = {p.course_id for p in user.purchases if p.course_id}
    partial_ids = set(user.partial_course_ids)
    active_ids  = set(user.active_special_offer_ids)
    recent_ids  = {
        so.course_id
        for so in sorted(user.special_offers, key=lambda so: so.created_at, reverse=True)[:_HISTORY_LIMIT]
    }
    denied: set[int] = purchased | partial_ids | active_ids | recent_ids

    # ───────── helper ─────────
    def _choose_from(landings: List[Landing]) -> Optional[Tuple[Landing, Course]]:
        if not landings:
            return None
        shift = len(user.special_offers) % len(landings)   # «смещение» для ротации
        for i in range(len(landings)):
            landing = landings[(i + shift) % len(landings)]
            for c in landing.courses:
                if c.id not in denied:
                    return landing, c
        return None

    # ───────── 1. поиск по тегам ─────────
    cheapest = _cheapest_landings_for_purchased(db, user)
    if cheapest:
        tag_weights: Counter[int] = Counter()
        for l in cheapest:
            for idx, t in enumerate(l.tags or []):
                tag_weights[t.id] += 3 if idx == 0 else 1

        if tag_weights:
            best_tag_id, _ = tag_weights.most_common(1)[0]
            tag_landings = (
                db.query(Landing)
                  .join(Landing.tags)
                  .filter(Tag.id == best_tag_id, Landing.is_hidden.is_(False))
                  .options(selectinload(Landing.courses))
                  .order_by(Landing.sales_count.desc())
                  .limit(20)
                  .all()
            )
            picked = _choose_from(tag_landings)
            if picked:
                logger.debug("User %s → tag %s landing %s course %s",
                             user.id, best_tag_id, picked[0].id, picked[1].id)
                return picked

    # ───────── 2. fallback ─────────
    top_landings = (
        db.query(Landing)
          .filter(Landing.is_hidden.is_(False))
          .options(selectinload(Landing.courses))
          .order_by(Landing.sales_count.desc())
          .limit(50)
          .all()
    )
    picked = _choose_from(top_landings)
    if picked:
        logger.debug("User %s → fallback landing %s course %s",
                     user.id, picked[0].id, picked[1].id)
    return picked


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
