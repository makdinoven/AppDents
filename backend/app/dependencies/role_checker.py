from fastapi import Depends, HTTPException, status
from .auth import get_current_user
from app.models.models import User

def require_roles(*allowed_roles: str):
    """
    Универсальный dependency для проверки, что текущий пользователь имеет одну из указанных ролей.
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient privileges. Required role(s): " + ", ".join(allowed_roles)
            )
        return current_user

    return role_checker
