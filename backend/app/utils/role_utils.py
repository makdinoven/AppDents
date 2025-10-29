"""
Утилиты для работы с ролями пользователей
"""
from ..models.models_v2 import User


def is_admin(user: User) -> bool:
    """
    Проверяет, является ли пользователь администратором.
    
    Args:
        user: Объект пользователя
        
    Returns:
        bool: True если пользователь является администратором
    """
    return (user.role or "").lower() in {"admin", "superadmin", "owner"}


def is_admin_by_email(db, email: str) -> bool:
    """
    Проверяет, является ли пользователь с указанным email администратором.
    
    Args:
        db: Сессия базы данных
        email: Email пользователя
        
    Returns:
        bool: True если пользователь является администратором
    """
    from ..services_v2.user_service import get_user_by_email
    
    user = get_user_by_email(db, email)
    if not user:
        return False
    
    return is_admin(user)
