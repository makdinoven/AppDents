
from pydantic import BaseModel, EmailStr
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None

# При регистрации пользователь НЕ вводит пароль:
class UserCreate(UserBase):
    pass

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserRead(BaseModel):
    id: int
    email: EmailStr
    name: Optional[str] = None
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

class UserUpdateName(BaseModel):
    name: str

class UserUpdatePassword(BaseModel):
    password: str

class UserAddCourse(BaseModel):
    course_id: int
    price_at_purchase: float

class ForgotPasswordRequest(BaseModel):
    email: EmailStr