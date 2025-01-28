# backend/app/api/users.py

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.user_service import (
    create_user, authenticate_user, create_access_token, decode_access_token
)
from app.schemas.user import UserCreate, UserLogin, UserRead, Token
from app.models.models import User

router = APIRouter()

@router.post("/register", response_model=UserRead)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter_by(email=user_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует"
        )
    # Создаём
    user = create_user(db, email=user_data.email, password=user_data.password)
    return user

@router.post("/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Генерируем JWT
    token = create_access_token({"user_id": user.id})
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me", response_model=UserRead)
def get_me(request: Request, db: Session = Depends(get_db)):
    """
    Пример простейшего способа извлечения JWT из заголовка Authorization.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    scheme, _, token = auth_header.partition(" ")
    if scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid auth scheme")

    try:
        token_data = decode_access_token(token)
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).get(token_data.user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user
