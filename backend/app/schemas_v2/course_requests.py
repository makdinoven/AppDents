from pydantic import BaseModel, Field

class CourseRequestIn(BaseModel):
    user_id: int = Field(..., description="ID пользователя")
    text: str = Field(..., description="Текст заявки на курс")

class CourseRequestOut(BaseModel):
    status: str
    sent_to: str
    user_email: str | None = None
