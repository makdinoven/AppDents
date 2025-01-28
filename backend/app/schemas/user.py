from pydantic import BaseModel, EmailStr, constr
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: constr(min_length=8)

class UserLogin(UserBase):
    password: str

class UserRead(BaseModel):
    id: int
    email: EmailStr
    name: Optional[str] = None

    class Config:
        orm_mode = True

# JWT-часть:
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[int] = None
