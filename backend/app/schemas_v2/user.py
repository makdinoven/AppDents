
from pydantic import BaseModel, EmailStr
from typing import Optional, List

from ..schemas_v2.course import CourseListResponse


class UserBase(BaseModel):
    email: EmailStr

# При регистрации пользователь НЕ вводит пароль:
class UserCreate(UserBase):
    pass

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserRead(BaseModel):
    id: int
    email: EmailStr
    role: str

    class Config:
        orm_mode = True

# JWT-часть
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[int] = None



class UserUpdateRole(BaseModel):
    role: str

class UserUpdatePassword(BaseModel):
    password: str

class UserAddCourse(BaseModel):
    course_id: int
    price_at_purchase: float

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class UserRegistrationResponse(UserRead):
    password: str

class UserCreateAdmin(BaseModel):
    email: EmailStr
    password: str
    role: str

class UserDetailedResponse(BaseModel):
    id: int
    email: EmailStr
    role: str
    courses: List["CourseListResponse"]  # "Forward reference" при необходимости

    class Config:
        orm_mode = True

class UserShortResponse(BaseModel):
    id: int
    email: EmailStr

    class Config:
        orm_mode = True

class UserDetailResponse(BaseModel):
    """
    Схема для возврата полной информации о пользователе:
    - Основные поля (id, email, role)
    - Список курсов (как объектов с полями id, title и т.д.)
    """
    id: int
    email: EmailStr
    role: str
    courses: Optional[List[CourseListResponse]] = None

    class Config:
        orm_mode = True


class UserUpdateFull(BaseModel):
    """
    Схема для обновления пользователя одним запросом.
    Можно расширять при необходимости.
    """
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    # Если нужно менять пароль в этом же запросе, можно добавить:
    password: Optional[str] = None
    # Чтобы полностью переопределять купленные курсы:
    course_ids: Optional[List[int]] = None
