import datetime as _dt
import logging
from collections import Counter

from sqlalchemy import func, case
from sqlalchemy.orm import Session, selectinload

from .user_service import add_partial_course_to_user
from ..models.models_v2 import (
    User, SpecialOffer, Landing, landing_course, Tag, Course, Purchase
)


logger = logging.getLogger(__name__)

_OFFER_TTL_HOURS = 24
_INTERVAL_HOURS  = 48         # каждые 3 суток
_HISTORY_LIMIT = 5

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
        .order_by(Landing.new_price.cast(func.Float))
        .all()
    )

    # возьмём по одному лендингу на курс с минимальной ценой
    cheapest_by_course = {}
    for l in landings:
        for cid in l.course_ids:
            if cid in purchased_course_ids and cid not in cheapest_by_course:
                cheapest_by_course[cid] = l
    return list(cheapest_by_course.values())


def _pick_offer_landing(db: Session, user: User) -> tuple[Landing, Course] | None:
    """
    Алгоритм подбора:
    1. Собираем теги с «дешёвых» лендингов купленных курсов.
    2. Считаем веса (+3 за first_tag¹).
    3. Берём самый популярный тег, ищем ТОП-продаваемый лендинг с ним,
       на курс которого нет покупки/оффера.
    """
    cheapest = _cheapest_landings_for_purchased(db, user)
    if not cheapest:
        return None

    tag_weights: Counter[int] = Counter()
    for l in cheapest:
        if not l.tags:
            continue
        for i, t in enumerate(l.tags):
            tag_weights[t.id] += 3 if i == 0 else 1    # «­first_tag +2»
    if not tag_weights:
        return None

    best_tag_id, _ = tag_weights.most_common(1)[0]
    logger.debug("User %s → best tag %s", user.id, best_tag_id)

    # кандидаты-лендинги
    purchased = {p.course_id for p in user.purchases if p.course_id}
    recent_offer_ids = {
        so.course_id
        for so in sorted(user.special_offers, key=lambda so: so.created_at, reverse=True)[:_HISTORY_LIMIT]
    }
    denied = purchased | set(user.active_special_offer_ids) | recent_offer_ids

    candidate = (
        db.query(Landing)
        .join(Landing.tags)
        .filter(
            Tag.id == best_tag_id,
            Landing.is_hidden.is_(False),
        )
        .options(selectinload(Landing.courses))
        .order_by(Landing.sales_count.desc())          # «популярный»
        .first()
    )
    if not candidate:
        return None

    # ищем подходящий курс
    for c in candidate.courses:
        if c.id not in denied:
            return candidate, c
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
        add_partial_course_to_user(db, user.id, course.id)
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
    """Обходит всех пользователей и выдаёт офферы при необходимости."""
    users = db.query(User).options(selectinload(User.purchases), selectinload(User.special_offers)).all()
    for u in users:
        try:
            generate_offer_for_user(db, u)
        except Exception:            # не падаем на одном юзере
            logger.exception("Special-offer generation failed for user %s", u.id)

# --- добавить куда-нибудь после cleanup_expired_offers ---
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
