
from pydantic import BaseModel, EmailStr
from typing import Optional, List

from AppDents.backend.app.schemas_v2.course import CourseListResponse


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