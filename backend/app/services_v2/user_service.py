import secrets
from datetime import datetime, timedelta
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
    PurchaseSource, FreeCourseAccess, AbandonedCheckout
from ..schemas_v2.user import TokenData, UserUpdateFull
from ..utils.email_sender import send_recovery_email

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
def add_partial_course_to_user(db: Session, user_id: int, course_id: int) -> None:
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
    db.add(FreeCourseAccess(user_id=user_id, course_id=course_id))
    user.free_trial_used = True
    db.commit()




def promote_course_to_full(db: Session, user_id: int, course_id: int) -> None:
    """
    После оплаты убираем частичный доступ и
    добавляем курс в полную коллекцию.
    """
    add_course_to_user(db, user_id, course_id)
    db.query(FreeCourseAccess).filter_by(
        user_id=user_id, course_id=course_id
    ).delete()
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
    """
    Возвращает:
      {
        "data": [
          {"date": "2025-06-01", "new_users": 35, "total_users": 10235},
          …
        ],
        "total_new_users": 120,
        "start_total_users": 10115,
        "end_total_users":   10235
      }
    • new_users   — количество регистраций за сутки;
    • total_users — общее число пользователей *на конец дня*.
    Гарантирует непрерывную шкалу дат (если в какой-то день нет
    регистраций, new_users = 0).
    """

    # 1) пользователи по дням внутри периода ------------------------------
    rows = (
        db.query(
            cast(User.created_at, Date).label("day"),
            func.count(User.id).label("cnt"),
        )
        .filter(
            User.created_at >= start_dt,
            User.created_at <  end_dt,
        )
        .group_by("day")
        .order_by("day")
        .all()
    )
    # rows: [(2025-06-01, 35), (2025-06-02, 85), …]

    # 2) приводим к словарю day → new_users
    per_day = {r.day: r.cnt for r in rows}

    # 3) формируем полный диапазон дат (чтобы не было «дыр»)
    days = []
    cur = start_dt.date()
    while cur < end_dt.date():
        days.append(cur)
        cur += timedelta(days=1)

    # 4) стартовое общее число пользователей до периода
    start_total_users: int = (
        db.query(func.count(User.id))
        .filter(User.created_at < start_dt)
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
