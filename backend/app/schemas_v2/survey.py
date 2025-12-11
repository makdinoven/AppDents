from pydantic import BaseModel
from ..models.models_v2 import QuestionType


# --- Output schemas ---

class SurveyBriefOut(BaseModel):
    """Краткая информация об опросе для списка pending."""
    slug: str
    title_key: str


class PendingSurveysOut(BaseModel):
    """Список непройденных опросов."""
    surveys: list[SurveyBriefOut]


class QuestionOut(BaseModel):
    """Вопрос опроса."""
    id: int
    order_index: int
    question_type: QuestionType
    text_key: str
    options_keys: list[str] | None = None
    is_required: bool

    class Config:
        from_attributes = True


class SurveyOut(BaseModel):
    """Полные данные опроса с вопросами."""
    slug: str
    title_key: str
    description_key: str | None = None
    questions: list[QuestionOut]

    class Config:
        from_attributes = True


# --- Input schemas ---

class AnswerIn(BaseModel):
    """Ответ на один вопрос."""
    question_id: int
    answer_choice: list[int] | None = None  # индексы выбранных вариантов
    answer_text: str | None = None


class SurveySubmitIn(BaseModel):
    """Отправка ответов на опрос."""
    answers: list[AnswerIn]


class SurveySubmitOut(BaseModel):
    """Результат отправки опроса."""
    status: str
    message_key: str

