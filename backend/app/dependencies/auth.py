from typing import Optional

from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..services.user_service import decode_access_token

from ..core.config import settings
from ..models.models_v2 import User

# Добавляем схему для OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login",auto_error=False)


from fastapi import Depends, HTTPException

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        token_data = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def get_current_user_optional(
        db: Session = Depends(get_db),
        token: str = Depends(oauth2_scheme)
) -> Optional[User]:
    """
    Возвращает текущего пользователя, если токен передан и валиден,
    или None, если токена нет/некорректен.
    Не выбрасывает 401 Unauthorized.
    """
    if not token:
        return None  # Токен не передан

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            return None
    except JWTError:
        return None  # Ошибка при декодировании/проверке токена

    user = db.query(User).filter(User.id == user_id).first()
    return user