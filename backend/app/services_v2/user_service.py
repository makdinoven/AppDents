import secrets
from datetime import datetime, timedelta
from typing import Optional

from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..core.config import settings
from ..models.models_v2 import User, Course
from ..schemas_v2.user import TokenData

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, password: str) -> bool:
    return pwd_context.verify(plain_password, password)

def generate_random_password() -> str:
    """Генерирует короткий случайный пароль."""
    return secrets.token_urlsafe(8)

def create_user(db: Session, email: str, password: str, role: str = "user") -> User:
    user = User(
        email=email,
        password=hash_password(password),
        role=role
    )
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

def update_user_password(db: Session, user_id: int, new_password: str) -> User:
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
    db.delete(user)
    db.commit()
