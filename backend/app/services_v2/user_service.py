import logging
import secrets
from collections import defaultdict
from datetime import datetime, timedelta, date
from math import ceil
from typing import Optional, Dict, Any, List

from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy import delete, func, cast, Date
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, aliased
from fastapi import HTTPException, status

from ..core.config import settings
from ..models.models_v2 import User, Course, Purchase, users_courses, WalletTxTypes, WalletTransaction, CartItem, Cart, \
    PurchaseSource, FreeCourseAccess, AbandonedCheckout, FreeCourseSource
from ..schemas_v2.user import TokenData, UserUpdateFull
from ..utils.email_sender import send_recovery_email

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, password: str) -> bool:
    return pwd_context.verify(plain_password, password)

def generate_random_password() -> str:
    """Генерирует короткий случайный пароль."""
    return secrets.token_urlsafe(8)

def generate_unique_referral_code(db: Session) -> str:
    """Базовое URL-safe кодирование — 8 символов хватит."""
    while True:
        code = secrets.token_urlsafe(6)[:8]
        if not db.query(User).filter(User.referral_code == code).first():
            return code

def credit_balance(
    db: Session, user_id: int,
    amount: float,
    tx_type: WalletTxTypes,
    meta: dict | None = None
) -> None:
    user = db.query(User).get(user_id)
    if not user:
        raise ValueError(f"User {user_id} not found for wallet credit")
    user.balance += amount
    db.add(
        WalletTransaction(
            user_id=user_id,
            amount=amount,
            type=tx_type,
            meta=meta or {}
        )
    )
    db.commit()

def create_user(
    db: Session,
    email: str,
    password: str,
    role: str = "user",
    invited_by: Optional[User] = None,
) -> User:
    # 1. создаём самого пользователя (ещё без commit’а)
    user = User(
        email=email,
        password=hash_password(password),
        role=role,
        invited_by_id=invited_by.id if invited_by else None,
    )
    user.referral_code = generate_unique_referral_code(db)
    db.add(user)

    # 2. сразу удаляем все «заброшенные» лиды по e-mail
    db.query(AbandonedCheckout) \
      .filter(AbandonedCheckout.email == email) \
      .delete(synchronize_session=False)

    # 3. один общий commit
    try:
        db.commit()
    except IntegrityError:                # если e-mail уже зарегистрирован
        db.rollback()
        raise ValueError("User with this email already exists")

    db.refresh(user)
    return user

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()

def create_access_token(data: dict, expires_delta: int = None) -> str:
    to_encode = data.copy()
    if expires_delta is not None:
        expire = datetime.utcnow() + timedelta(minutes=expires_delta)
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def decode_access_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise JWTError("No user_id in token")
        return TokenData(user_id=user_id)
    except JWTError as e:
        raise e

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    return user

def search_users_by_email(db: Session, email_query: str) -> list[User]:
    return db.query(User).filter(User.email.ilike(f"%{email_query}%")).all()

def update_user_role(db: Session, user_id: int, new_role: str) -> User:
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {
                "code": "USER_NOT_FOUND",
                "message": "User not found",
                "translation_key": "error.user_not_found",
                "params": {"user_id": user_id}
            }}
        )
    user.role = new_role
    db.commit()
    db.refresh(user)
    return user

def update_user_password(db: Session, user_id: int, new_password: str, region: str = "EN") -> User:
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {
                "code": "USER_NOT_FOUND",
                "message": "User not found",
                "translation_key": "error.user_not_found",
                "params": {"user_id": user_id}
            }}
        )
    user.password = hash_password(new_password)
    db.commit()
    db.refresh(user)
    send_recovery_email(user.email, new_password, region)
    return user

def add_course_to_user(db: Session, user_id: int, course_id: int) -> None:
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {
                "code": "USER_NOT_FOUND",
                "message": "User not found",
                "translation_key": "error.user_not_found",
                "params": {"user_id": user_id}
            }}
        )
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {
                "code": "COURSE_NOT_FOUND",
                "message": "Course not found",
                "translation_key": "error.course_not_found",
                "params": {"course_id": course_id}
            }}
        )
    if course not in user.courses:
        user.courses.append(course)
        db.commit()

def remove_course_from_user(db: Session, user_id: int, course_id: int) -> None:
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {
                "code": "USER_NOT_FOUND",
                "message": "User not found",
                "translation_key": "error.user_not_found",
                "params": {"user_id": user_id}
            }}
        )
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {
                "code": "COURSE_NOT_FOUND",
                "message": "Course not found",
                "translation_key": "error.course_not_found",
                "params": {"course_id": course_id}
            }}
        )
    if course in user.courses:
        user.courses.remove(course)
        db.commit()

# ──────────────────────────────────────────────────────────────
#  Бесплатный доступ к первому уроку
# ──────────────────────────────────────────────────────────────
def add_partial_course_to_user(db: Session, user_id: int, course_id: int, source: FreeCourseSource = FreeCourseSource.LANDING) -> None:
    """
    • Один free-курс на аккаунт.
    • Нельзя брать free, если курс уже куплен.
    • Нельзя дублировать уже полученный partial.
    Исключения → ValueError с кодом-строкой.
    """
    user = get_user_by_id(db, user_id)
    if not user:
        raise ValueError("user_not_found")

    # курс уже куплен полностью
    if any(c.id == course_id for c in user.courses):
        raise ValueError("course_already_purchased")

    # он же уже получен бесплатно
    exists = (
        db.query(FreeCourseAccess)
          .filter_by(user_id=user_id, course_id=course_id)
          .first()
    )
    if exists:
        raise ValueError("partial_already_granted")

    # бесплатный курс уже был, а просят другой
    if user.free_trial_used:
        raise ValueError("free_course_already_taken")

    # выдаём
    db.add(
        FreeCourseAccess(
            user_id=user_id,
            course_id=course_id,
            source=source,  # ← пишем источник
        )
    )
    user.free_trial_used = True
    db.commit()





def promote_course_to_full(db: Session, user_id: int, course_id: int) -> None:
    """
    После оплаты:
      • курс попадает в полную коллекцию,
      • запись FreeCourseAccess НЕ удаляется, а помечается как сконвертированная.
    """
    add_course_to_user(db, user_id, course_id)      # ← уже было

    fca = (
        db.query(FreeCourseAccess)
          .filter_by(user_id=user_id, course_id=course_id)
          .first()
    )
    if fca:
        fca.converted_to_full = True
        fca.converted_at = datetime.utcnow()
        logger.info(
            "Free course %s for user %s marked as converted_at %s",
            course_id, user_id, fca.converted_at.isoformat()
        )

    db.commit()


def delete_user(db: Session, user_id: int) -> None:
    # 1) получаем пользователя
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {
                "code": "USER_NOT_FOUND",
                "message": "User not found",
                "translation_key": "error.user_not_found",
                "params": {"user_id": user_id}
            }}
        )

    # 2) удаляем все покупки этого пользователя
    db.execute(
        delete(Purchase).
        where(Purchase.user_id == user_id)
    )

    # 3) удаляем все записи в users_courses для этого пользователя
    db.execute(
        delete(users_courses).
        where(users_courses.c.user_id == user_id)
    )

    # 4) удаляем все элементы корзины (cart_items) и саму корзину
    #    Проверяем, есть ли у пользователя связанная корзина
    if user.cart:
        # 4.1) удаляем все элементы из cart_items для этой корзины
        db.execute(
            delete(CartItem).
            where(CartItem.cart_id == user.cart.id)
        )
        # 4.2) удаляем саму корзину
        db.execute(
            delete(Cart).
            where(Cart.user_id == user_id)
        )

    # 5) удаляем самого пользователя
    db.delete(user)

    # 6) коммитим изменения разом
    db.commit()

def update_user_full(db: Session, user_id: int, data: UserUpdateFull, region: str = "EN") -> User:
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {
                "code": "USER_NOT_FOUND",
                "message": "User not found",
                "params": {"user_id": user_id}
            }}
        )

    # Обновляем email, если значение передано, не пустое и отличается от текущего
    if data.email is not None and data.email.strip() and data.email != user.email:
        user.email = data.email

    # Обновляем роль, если значение передано, не пустое и отличается
    if data.role is not None and data.role.strip() and data.role != user.role:
        user.role = data.role

    # Обновляем пароль, если значение передано, не пустое и отличается от текущего
    # Для проверки пароля нужно сравнить, например, через функцию verify_password
    if data.password is not None and data.password.strip():
        send_recovery_email(data.email, data.password, region)
        # Если новый пароль не совпадает с текущим (в терминах верификации)
        if not verify_password(data.password, user.password):
            user.password = hash_password(data.password)

    # Обновляем список курсов, если course_ids переданы и отличаются от текущего списка
    if data.courses is not None:
        # Получаем текущие course_ids
        current_course_ids = {course.id for course in user.courses} if user.courses else set()
        new_course_ids = set(data.courses)
        if new_course_ids != current_course_ids:
            courses = db.query(Course).filter(Course.id.in_(data.courses)).all()
            user.courses = courses

    db.commit()
    db.refresh(user)
    return user

def list_users_paginated(
    db: Session,
    *,
    page: int = 1,
    size: int = 10
) -> dict:
    # 1) Общее число пользователей
    total = db.query(func.count(User.id)).scalar()
    # 2) Смещение
    offset = (page - 1) * size
    # 3) Выборка
    users = db.query(User).order_by(User.id.desc()).offset(offset).limit(size).all()
    # 4) Подсчёт страниц
    total_pages = ceil(total / size) if total else 0

    return {
        "total": total,
        "total_pages": total_pages,
        "page": page,
        "size": size,
        "items": users,
    }


def search_users_paginated(
    db: Session,
    *,
    q: str,
    page: int = 1,
    size: int = 10
) -> dict:
    # 1) Базовый фильтр по подстроке в email
    base_q = db.query(User).filter(User.email.ilike(f"%{q}%"))
    # 2) Общее число
    total = base_q.count()
    # 3) Смещение и лимит
    offset = (page - 1) * size
    users = base_q.offset(offset).limit(size).all()
    # 4) Подсчёт страниц
    total_pages = ceil(total / size) if total else 0

    return {
        "total": total,
        "total_pages": total_pages,
        "page": page,
        "size": size,
        "items": users,
    }

def get_referral_analytics(
    db: Session,
    start_dt: datetime,
    end_dt: datetime,
) -> dict:
    """
    Формирует словарь:
      {
        "inviters": [...],
        "referrals": [...],
        "total_referrals": int
      }

    • В выборку попадают только те рефералы, чья дата регистрации
      попадает в [start_dt, end_dt).
    • Сумма `total_credited` — агрегат всех транзакций по кошельку
      (WalletTransaction.amount) конкретного пригласителя **за всё время**
      -- так обычно понимают «все деньги, которые были на балансе».
      Если нужно ограничить суммирование тем же периодом —
      добавьте фильтр по `WalletTransaction.created_at`.
    """

    # --- 1. пригласители + счётчик рефералов (subquery) --------------------
    ref_count_subq = (
        db.query(
            User.invited_by_id.label("inviter_id"),
            func.count(User.id).label("ref_count"),
        )
        .filter(
            User.invited_by_id.is_not(None),
            User.created_at >= start_dt,
            User.created_at < end_dt,
        )
        .group_by(User.invited_by_id)
        .subquery()
    )

    # --- 2. итоговый запрос по пригласителям ------------------------------
    inviter_rows = (
        db.query(
            User.id.label("inviter_id"),
            User.email,
            User.balance,
            func.coalesce(func.sum(func.abs(WalletTransaction.amount)), 0).label("total_credited"),
            ref_count_subq.c.ref_count,
        )
        .join(ref_count_subq, ref_count_subq.c.inviter_id == User.id)
        .outerjoin(WalletTransaction, WalletTransaction.user_id == User.id)
        .group_by(User.id, ref_count_subq.c.ref_count)
        .all()
    )

    inviters_data = [
        {
            "inviter_id": r.inviter_id,
            "email":     r.email,
            "referrals": r.ref_count,
            "balance":   f"{r.balance:.2f} $",
            "total_credited": f"{r.total_credited:.2f} $",
        }
        for r in inviter_rows
    ]

    total_referrals = sum(r.ref_count for r in inviter_rows)

    # --- 3. подробный список рефералов ------------------------------------
    inviter_alias = aliased(User)

    referral_rows = (
        db.query(
            inviter_alias.email.label("inviter_email"),
            inviter_alias.id.label("inviter_id"),
            User.id.label("referral_id"),
            User.email.label("referral_email"),
            User.created_at.label("registered_at"),
        )
        .join(inviter_alias, inviter_alias.id == User.invited_by_id)
        .filter(
            User.invited_by_id.is_not(None),
            User.created_at >= start_dt,
            User.created_at < end_dt,
        )
        .order_by(User.created_at.desc())
        .all()
    )

    referrals_data = [
        {
            "inviter_id": r.inviter_id,
            "inviter_email":  r.inviter_email,
            "referral_id": r.referral_id,
            "referral_email": r.referral_email,
            "registered_at":  r.registered_at.isoformat() + "Z",
        }
        for r in referral_rows
    ]

    return {
        "inviters": inviters_data,
        "referrals": referrals_data,
        "total_referrals": total_referrals,
    }

def get_user_growth_stats(
    db: Session,
    start_dt: datetime,
    end_dt: datetime,
) -> dict:
    # 1) пользователи по дням внутри периода (исключаем balance == 5)
    rows = (
        db.query(
            cast(User.created_at, Date).label("day"),
            func.count(User.id).label("cnt"),
        )
        .filter(
            User.created_at >= start_dt,
            User.created_at <  end_dt,
            User.balance != 5,          # ← исключаем
        )
        .group_by("day")
        .order_by("day")
        .all()
    )

    # 2) day → new_users
    per_day = {r.day: r.cnt for r in rows}

    # 3) полный диапазон дат
    days = []
    cur = start_dt.date()
    while cur < end_dt.date():
        days.append(cur)
        cur += timedelta(days=1)

    # 4) стартовое общее число пользователей до периода (также исключаем balance == 5)
    start_total_users: int = (
        db.query(func.count(User.id))
        .filter(
            User.created_at < start_dt,
            User.balance != 5,          # ← исключаем
        )
        .scalar()
    )

    # 5) формируем результат + кумулятив
    data = []
    running_total = start_total_users
    for d in days:
        new_users = per_day.get(d, 0)
        running_total += new_users
        data.append(
            {
                "date": d.isoformat(),
                "new_users": new_users,
                "total_users": running_total,
            }
        )

    return {
        "data": data,
        "total_new_users": running_total - start_total_users,
        "start_total_users": start_total_users,
        "end_total_users":   running_total,
    }


def get_purchase_analytics(
    db: Session,
    start_dt: datetime,
    end_dt: datetime,
    *,
    page: int | None = None,
    size: int | None = None,
    source_filter: str | None = None,        # ← Фильтр по source
) -> Dict[str, Any]:
    """
    Аналитика покупок.

    Если page/size не заданы — возвращаем все записи без пагинации.
    При source_filter принимаем строку-значение enum (LANDING, CART …)
    и оставляем только такие покупки.
    """

    base_q = (
        db.query(
            Purchase,
            User.email.label("email"),
        )
        .join(User, User.id == Purchase.user_id)
        .filter(
            Purchase.created_at >= start_dt,
            Purchase.created_at <  end_dt,
        )
    )

    # ── фильтр по source --------------------------------------------------
    if source_filter:
        try:
            src_enum = PurchaseSource[source_filter.upper()]
        except KeyError:
            # неизвестное значение — сразу отдаём «пустой» результат
            return {
                "total": 0,
                "total_amount": "0.00 $",
                "items": [],
            }
        base_q = base_q.filter(Purchase.source == src_enum)

    # сортировка по дате ↓
    base_q = base_q.order_by(Purchase.created_at.desc())

    total = base_q.count()

    total_amount_val: float | None = (
        db.query(func.coalesce(func.sum(Purchase.amount), 0))
        .filter(
            Purchase.created_at >= start_dt,
            Purchase.created_at <  end_dt,
            *( [Purchase.source == src_enum] if source_filter else [] )
        )
        .scalar()
    )

    # ── пагинация ---------------------------------------------------------
    if page and size:
        offset = (page - 1) * size
        rows = base_q.offset(offset).limit(size).all()
        total_pages = (total + size - 1) // size
    else:
        rows = base_q.all()
        total_pages = None

    items: List[dict] = [
        {
            "user_id":   p.user_id,
            "email":     email,
            "amount":    f"{(p.amount or 0):.2f} $",
            "source":    p.source.value,
            "from_ad":   p.from_ad,
            "paid_at":   p.created_at.isoformat(),
        }
        for p, email in rows
    ]

    result: Dict[str, Any] = {
        "total": total,
        "total_amount": f"{(total_amount_val or 0):.2f} $",
        "items": items,
    }
    if page and size:
        result.update({
            "total_pages": total_pages,
            "page": page,
            "size": size,
        })
    return result

# services_v2/user_service.py
from sqlalchemy import case, distinct

def get_free_course_stats(        # полностью заменяет старую версию
    db: Session,
    *,
    start_date: date | None = None,
    end_date:   date | None = None,
    limit: int | None = None,
) -> dict:
    """
    Аналитика рекламных free-курсов.

    Возвращает:
        summary:
            active_free_users – пользователи, у которых СЕЙЧАС есть неоплаченные free-курсы
            freebie_users     – пользователи, взявшие free-курсы в указанный период
        courses – массив словарей по каждому курсу

    Период задаётся [start_date, end_date] включительно.
    Если обе даты None – берём «за всё время».
    """
    # ──────────────────── 1. Диапазон дат UTC ────────────────────────────────
    now = datetime.utcnow()

    if start_date is None and end_date is None:
        start_dt, end_dt = datetime.min, now
    elif start_date and not end_date:
        start_dt, end_dt = datetime.combine(start_date, datetime.min.time()), now
    elif start_date and end_date:
        end_inclusive = end_date + timedelta(days=1)   # +1 день, чтобы включить end_date
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt   = datetime.combine(end_inclusive, datetime.min.time())
    else:
        raise ValueError("end_date без start_date недопустим")

    logger.debug(
        "Free-course stats | %s – %s | limit=%s",
        start_dt.isoformat(), end_dt.isoformat(), limit
    )

    # ──────────────────── 2. Free-курсы периода (только LANDING) ─────────────
    fca_period = (
        db.query(FreeCourseAccess)
          .filter(
              FreeCourseAccess.source == FreeCourseSource.LANDING,
              FreeCourseAccess.granted_at >= start_dt,
              FreeCourseAccess.granted_at <  end_dt,
          )
          .subquery()
    )

    # ──────────────────── 3. Агрегация по каждому курсу ─────────────────────
    base = (
        db.query(
            fca_period.c.course_id.label("cid"),
            func.count(distinct(fca_period.c.user_id)).label("free_taken"),
            func.sum(
                case((fca_period.c.converted_to_full, 1), else_=0)
            ).label("converted_to_course"),
        )
        .group_by(fca_period.c.course_id)
        .subquery()
    )

    q = (
        db.query(
            Course.id,
            Course.name,
            base.c.free_taken,
            base.c.converted_to_course,
        )
        .join(base, Course.id == base.c.cid)
        .order_by(base.c.free_taken.desc())            # сортировка по umолчанию
    )
    if limit:
        q = q.limit(limit)

    rows = q.all()

    # ──────────────────── 4. Глобальные цифры ───────────────────────────────
    active_free_users = (
        db.query(func.count(distinct(FreeCourseAccess.user_id)))
          .filter(
              FreeCourseAccess.source == FreeCourseSource.LANDING,
              FreeCourseAccess.converted_to_full.is_(False)
          )
          .scalar()
    )

    freebie_users = db.query(func.count(distinct(fca_period.c.user_id))).scalar()

    # ──────────────────── 5. Детализация по курсам ───────────────────────────
    result_per_course: list[dict] = []
    for cid, name, taken, conv_same in rows:
        # сколько из взявших купили что-нибудь
        conv_any = (
            db.query(func.count(distinct(Purchase.user_id)))
              .join(fca_period,
                    Purchase.user_id == fca_period.c.user_id)
              .filter(fca_period.c.course_id == cid)
              .scalar()
        )

        result_per_course.append({
            "course_id": cid,
            "course_name": name,
            "free_taken": taken,
            "converted_to_course": conv_same or 0,
            "converted_to_course_rate":
                f"{(conv_same or 0) / taken * 100:.1f}%" if taken else "0%",
            "converted_to_any_course": conv_any or 0,
            "converted_to_any_course_rate":
                f"{(conv_any or 0) / taken * 100:.1f}%" if taken else "0%",
        })

    # ──────────────────── 6. Финальный ответ ────────────────────────────────
    return {
        "summary": {
            "active_free_users": active_free_users,
            "freebie_users":     freebie_users,
        },
        "courses": result_per_course,
    }

def get_purchases_by_source_timeseries(
    db: Session,
    start_dt: date,
    end_dt: date,
    *,
    source: str | None = None,        # "CART", "LANDING", "HOMEPAGE", ...
    mode: str = "count",              # "count" | "amount"
) -> dict:
    """
    Возвращает динамику по дням. Если source=None -> по всем источникам, иначе только выбранный.
    mode:
      - "count"  -> число покупок
      - "amount" -> сумма покупок
    Формат:
    {
      "mode": "count",
      "source": "ALL"|"CART"|...,
      "data": [
        {
          "date": "2025-08-01",
          "series": [
            {"source": "CART", "value": 5},
            {"source": "LANDING", "value": 2},
            ...
          ]
        },
        ...
      ],
      "total": 123,              # итого по периоду
      "total_amount": "456.00 $" # итоговая сумма по периоду
    }
    """
    # столбец "день" без времени
    day_col = cast(Purchase.created_at, Date)  # эквивалент DATE(created_at)

    base = db.query(
        day_col.label("day"),
        Purchase.source.label("source"),
        func.count(Purchase.id).label("cnt"),
        func.coalesce(func.sum(Purchase.amount), 0.0).label("amt"),
    ).filter(
        Purchase.created_at >= start_dt,
        Purchase.created_at <  end_dt,
    )

    # фильтр по конкретному источнику, если он выбран
    src_enum = None
    if source:
        try:
            src_enum = PurchaseSource[source.upper()]
        except KeyError:
            # неизвестный source -> пустой ответ корректной формы
            days = []
            cur = start_dt.date()
            while cur < end_dt.date():
                days.append(cur.isoformat())
                cur += timedelta(days=1)
            return {
                "mode": mode,
                "source": source.upper(),
                "data": [{"date": d, "series": []} for d in days],
                "total": 0,
                "total_amount": "0.00 $",
            }
        base = base.filter(Purchase.source == src_enum)

    rows = (base.group_by(day_col, Purchase.source)
                 .order_by(day_col)
                 .all())

    # сводим в stats[day][source] -> value
    stats = defaultdict(dict)
    total_cnt = 0
    total_amt = 0.0

    for r in rows:
        val = int(r.cnt) if mode == "count" else float(r.amt or 0.0)
        stats[r.day][r.source.value] = val
        total_cnt += int(r.cnt)
        total_amt += float(r.amt or 0.0)

    # полный диапазон дней без дыр
    data = []
    cur = start_dt.date()
    last = end_dt.date()
    while cur < last:
        by_src = stats.get(cur, {})
        # если source не задан -> возвращаем все источники как серии,
        # если задан -> только одну серию (или пусто)
        if src_enum is None:
            series = [{"source": s, "value": (by_src.get(s, 0) if mode == "count" else float(by_src.get(s, 0)))} for s in sorted(by_src.keys())]
        else:
            sname = src_enum.value
            val = by_src.get(sname, 0)
            series = [{"source": sname, "value": (val if mode == "count" else float(val))}]
        data.append({
            "date": cur.isoformat(),
            "series": series,
        })
        cur += timedelta(days=1)

    return {
        "mode": "count" if mode == "count" else "amount",
        "source": "ALL" if src_enum is None else src_enum.value,
        "data": data,
        "total": total_cnt,
        "total_amount": f"{total_amt:.2f} $",
    }