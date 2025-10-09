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
    balance: float
    cart_items_count: int = 0

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
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    password: Optional[str] = None
    courses: Optional[List[int]] = None
    books: Optional[List[int]] = None

class PurchaseResponse(BaseModel):
    id: int
    course_id: Optional[int]               # если покупка была курса
    landing_slug: Optional[str]            # вместо landing_id
    landing_name: Optional[str]            # название лендинга
    created_at: datetime
    from_ad: bool
    amount: Optional[float] = 0.0

    class Config:
        orm_mode = True

    @root_validator(pre=True)
    def extract_landing_fields(cls, values):
        data = dict(values)
        landing = data.get("landing")
        if landing:
            data["landing_slug"] = landing.page_name
            data["landing_name"] = landing.landing_name
        else:
            data["landing_slug"] = None
            data["landing_name"] = None
        return data

    @validator("amount", pre=True, always=True)
    def set_default_amount(cls, v):
        # если из БД пришло None — возвращаем 0.0
        return 0.0 if v is None else v

class UserDetailedResponse(BaseModel):
    id: int
    email: EmailStr
    role: str
    courses: List[int]
    books: List[int]
    purchases: List[PurchaseResponse]
    balance : str

    @validator("courses", pre=True)
    def convert_courses_to_ids(cls, value):
        if value is None:
            return []
        return [course.id for course in value]

    @validator("books", pre=True)  # ⟵ конверсия в список ID
    def convert_books_to_ids(cls, value):
        if value is None:
            return []
        return [b.id for b in value]

    class Config:
        orm_mode = True