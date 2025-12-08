"""
Сервис для работы с опросами пользователей.
"""
from sqlalchemy.orm import Session
from sqlalchemy import exists, and_
from typing import List
import logging

from ..models.models_v2 import Survey, SurveyQuestion, SurveyResponse, SurveyStatus
from ..schemas_v2.survey import AnswerIn

logger = logging.getLogger(__name__)


def get_pending_surveys_for_user(db: Session, user_id: int) -> List[Survey]:
    """
    Получить список активных опросов, которые пользователь ещё не проходил.
    """
    # Подзапрос: ID опросов, на которые пользователь уже ответил
    completed_survey_ids = (
        db.query(SurveyResponse.survey_id)
        .filter(SurveyResponse.user_id == user_id)
        .distinct()
        .subquery()
    )
    
    # Активные опросы, которых нет в списке пройденных
    surveys = (
        db.query(Survey)
        .filter(
            Survey.status == SurveyStatus.ACTIVE,
            ~Survey.id.in_(completed_survey_ids)
        )
        .all()
    )
    
    return surveys


def get_active_survey_by_slug(db: Session, slug: str) -> Survey | None:
    """
    Получить активный опрос по slug.
    """
    return (
        db.query(Survey)
        .filter(
            Survey.slug == slug,
            Survey.status == SurveyStatus.ACTIVE
        )
        .first()
    )


def check_user_completed_survey(db: Session, survey_id: int, user_id: int) -> bool:
    """
    Проверить, проходил ли пользователь данный опрос.
    """
    return db.query(
        exists().where(
            and_(
                SurveyResponse.survey_id == survey_id,
                SurveyResponse.user_id == user_id
            )
        )
    ).scalar()


def submit_survey_responses(
    db: Session,
    survey: Survey,
    user_id: int,
    answers: List[AnswerIn]
) -> None:
    """
    Сохранить ответы пользователя на опрос.
    
    Raises:
        ValueError: если пользователь уже проходил опрос или ответы невалидны
    """
    # Проверяем, не проходил ли уже
    if check_user_completed_survey(db, survey.id, user_id):
        raise ValueError("User has already completed this survey")
    
    # Собираем ID вопросов опроса
    question_ids = {q.id for q in survey.questions}
    required_question_ids = {q.id for q in survey.questions if q.is_required}
    
    # Проверяем, что все required вопросы имеют ответы
    answered_question_ids = set()
    for answer in answers:
        if answer.question_id not in question_ids:
            raise ValueError(f"Question {answer.question_id} does not belong to this survey")
        
        # Проверяем, что есть хоть какой-то ответ
        has_answer = (
            (answer.answer_choice is not None and len(answer.answer_choice) > 0) or
            (answer.answer_text is not None and answer.answer_text.strip() != "")
        )
        if has_answer:
            answered_question_ids.add(answer.question_id)
    
    # Проверяем required вопросы
    missing_required = required_question_ids - answered_question_ids
    if missing_required:
        raise ValueError(f"Required questions not answered: {missing_required}")
    
    # Сохраняем ответы
    for answer in answers:
        # Пропускаем пустые ответы для необязательных вопросов
        has_answer = (
            (answer.answer_choice is not None and len(answer.answer_choice) > 0) or
            (answer.answer_text is not None and answer.answer_text.strip() != "")
        )
        if not has_answer:
            continue
            
        response = SurveyResponse(
            survey_id=survey.id,
            user_id=user_id,
            question_id=answer.question_id,
            answer_choice=answer.answer_choice,
            answer_text=answer.answer_text.strip() if answer.answer_text else None
        )
        db.add(response)
    
    db.commit()
    logger.info(f"User {user_id} completed survey {survey.slug}")

