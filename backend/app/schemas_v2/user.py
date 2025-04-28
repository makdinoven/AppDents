from datetime import datetime

from pydantic import BaseModel, EmailStr, validator, root_validator
from typing import Optional, List, Any

from ..schemas_v2.course import CourseListResponseShort


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

    @validator("courses", pre=True)
    def convert_courses_to_ids(cls, value):
        if value is None:
            return []
        # Если это список ORM объектов, извлекаем их ID
        return [course.id for course in value]

class UserShortResponse(BaseModel):
    id: int
    email: str  # вместо EmailStr, чтобы можно было подставлять строку-заменитель

    @validator('email', pre=True, always=True)
    def validate_email(cls, v: Any) -> str:
        try:
            return EmailStr.validate(v)
        except Exception:
            return f"invalid_email: {v}"

    class Config:
        orm_mode = True

class UserListPageResponse(BaseModel):
    total: int
    total_pages: int
    page: int
    size: int
    items: List[UserShortResponse]

class UserDetailResponse(BaseModel):
    """
    Схема для возврата полной информации о пользователе:
    - Основные поля (id, email, role)
    - Список курсов (как объектов с полями id, title и т.д.)
    """
    id: int
    email: EmailStr
    role: str
    courses: Optional[List[CourseListResponseShort]] = None

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
    courses: Optional[List[int]] = None

class PurchaseResponse(BaseModel):
    id: int
    course_id: Optional[int]               # если покупка была курса
    landing_slug: Optional[str]            # вместо landing_id
    landing_name: Optional[str]            # название лендинга
    created_at: datetime
    from_ad: bool
    amount: float

    class Config:
        orm_mode = True

    @root_validator(pre=True)
    def extract_landing_fields(cls, values):
        landing = values.get("landing")
        if landing:
            values["landing_slug"] = landing.page_name
            values["landing_name"] = landing.landing_name
        else:
            values["landing_slug"] = None
            values["landing_name"] = None
        return values

class UserDetailedResponse(BaseModel):
    id: int
    email: EmailStr
    role: str
    courses: List[int]
    purchases: List[PurchaseResponse]

    class Config:
        orm_mode = True