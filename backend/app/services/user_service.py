from sqlalchemy.orm import Session
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt, JWTError

from app.core.config import settings
from app.models.models import User, UserCourses, Course
from app.schemas.user import TokenData

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_user(db: Session, email: str, password: str, name: str = "", role: str = "user") -> User:
    user = User(
        email=email,
        hashed_password=hash_password(password),
        name=name,
        role=role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter_by(email=email).first()

def get_user_by_id(db: Session, user_id: int) -> User | None:
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
        user_id: int | None = payload.get("user_id")
        if user_id is None:
            raise JWTError("No user_id in token")
        return TokenData(user_id=user_id)
    except JWTError:
        raise

def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

# Новые функции для управления пользователями:

def search_users_by_email(db: Session, email_query: str) -> list[User]:
    return db.query(User).filter(User.email.ilike(f"%{email_query}%")).all()

def update_user_role(db: Session, user_id: int, new_role: str) -> User:
    user = get_user_by_id(db, user_id)
    if not user:
        raise ValueError("User not found")
    user.role = new_role
    db.commit()
    db.refresh(user)
    return user

def update_user_name(db: Session, user_id: int, new_name: str) -> User:
    user = get_user_by_id(db, user_id)
    if not user:
        raise ValueError("User not found")
    user.name = new_name
    db.commit()
    db.refresh(user)
    return user

def update_user_password(db: Session, user_id: int, new_password: str) -> User:
    user = get_user_by_id(db, user_id)
    if not user:
        raise ValueError("User not found")
    user.hashed_password = hash_password(new_password)
    db.commit()
    db.refresh(user)
    return user

def add_course_to_user(db: Session, user_id: int, course_id: int, price_at_purchase: float) -> UserCourses:
    user = get_user_by_id(db, user_id)
    if not user:
        raise ValueError("User not found")
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise ValueError("Course not found")
    user_course = UserCourses(user_id=user_id, course_id=course_id, price_at_purchase=price_at_purchase)
    db.add(user_course)
    db.commit()
    db.refresh(user_course)
    return user_course
