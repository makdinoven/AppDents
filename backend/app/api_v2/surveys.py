"""
API эндпоинты для системы опросов.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..dependencies.auth import get_current_user
from ..models.models_v2 import User
from ..schemas_v2.survey import (
    PendingSurveysOut,
    SurveyBriefOut,
    SurveyOut,
    QuestionOut,
    SurveySubmitIn,
    SurveySubmitOut,
)
from ..services_v2.survey_service import (
    get_pending_surveys_for_user,
    get_active_survey_by_slug,
    check_user_completed_survey,
    submit_survey_responses,
    record_survey_view,
)

router = APIRouter()


@router.get("/pending", response_model=PendingSurveysOut)
def get_pending_surveys(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Получить список активных опросов, которые текущий пользователь ещё не проходил.
    Фронтенд вызывает этот эндпоинт при загрузке приложения.
    """
    surveys = get_pending_surveys_for_user(db, current_user.id)
    
    return PendingSurveysOut(
        surveys=[
            SurveyBriefOut(slug=s.slug, title_key=s.title_key)
            for s in surveys
        ]
    )


@router.get("/{slug}", response_model=SurveyOut)
def get_survey(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Получить опрос по slug с вопросами.
    Возвращает 404, если опрос не найден или не активен.
    """
    survey = get_active_survey_by_slug(db, slug)
    
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    
    # Проверяем, не проходил ли уже
    if check_user_completed_survey(db, survey.id, current_user.id):
        raise HTTPException(
            status_code=400,
            detail="survey.alreadyCompleted"
        )
    
    return SurveyOut(
        slug=survey.slug,
        title_key=survey.title_key,
        description_key=survey.description_key,
        questions=[
            QuestionOut(
                id=q.id,
                order_index=q.order_index,
                question_type=q.question_type,
                text_key=q.text_key,
                options_keys=q.options_keys,
                is_required=q.is_required
            )
            for q in sorted(survey.questions, key=lambda x: x.order_index)
        ]
    )


@router.post("/{slug}/submit", response_model=SurveySubmitOut)
def submit_survey(
    slug: str,
    payload: SurveySubmitIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Отправить ответы на опрос.
    """
    survey = get_active_survey_by_slug(db, slug)
    
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    
    try:
        submit_survey_responses(db, survey, current_user.id, payload.answers)
    except ValueError as e:
        error_msg = str(e)
        if "already completed" in error_msg.lower():
            raise HTTPException(status_code=400, detail="survey.alreadyCompleted")
        raise HTTPException(status_code=400, detail=str(e))
    
    return SurveySubmitOut(
        status="ok",
        message_key="survey.thankYou"
    )


@router.post("/{slug}/view")
def track_survey_view(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Записать факт открытия модалки опроса (для аналитики конверсии).
    Фронтенд вызывает этот эндпоинт при показе модалки пользователю.
    """
    survey = get_active_survey_by_slug(db, slug)
    
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    
    record_survey_view(db, survey.id, current_user.id)
    
    return {"status": "ok"}
