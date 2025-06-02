import secrets
from datetime import datetime, timedelta
from math import ceil
from typing import Optional

from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy import delete, func
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..core.config import settings
from ..models.models_v2 import User, Course, Purchase, users_courses, WalletTxTypes, WalletTransaction
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

def create_user(db: Session, email: str, password: str, role: str = "user", invited_by: Optional[User] = None) -> User:
    user = User(
        email=email,
        password=hash_password(password),
        role=role,
        invited_by_id=invited_by.id if invited_by else None,
    )
    user.referral_code = generate_unique_referral_code(db)
    db.add(user)
    db.commit()
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
