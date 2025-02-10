# app/dependencies/auth.py
from fastapi import HTTPException, Request, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.user_service import decode_access_token
from app.models.models import User

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """
    Извлекает JWT из заголовка Authorization, валидирует его
    и возвращает объект пользователя. Если данные некорректны, выбрасывает 401.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    scheme, _, token = auth_header.partition(" ")
    if scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid auth scheme")
    try:
        token_data = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).get(token_data.user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
