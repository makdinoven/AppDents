from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from ..db.database import get_db
from ..models.models_v2 import TermsOfUse, PrivacyPolicy, CookiePolicy
from ..schemas_v2.policy import (
    TermsOfUseResponse, 
    PrivacyPolicyResponse, 
    CookiePolicyResponse
)

router = APIRouter()


@router.get(
    "/terms-of-use",
    response_model=TermsOfUseResponse,
    summary="Получить условия использования"
)
def get_terms_of_use(
    language: str = Query("ru", description="Язык политики (ru, en, es, it, ar, pt)"),
    db: Session = Depends(get_db)
):
    """Получить условия использования на указанном языке."""
    terms = db.query(TermsOfUse).filter(TermsOfUse.language == language).first()
    
    if not terms:
        raise HTTPException(
            status_code=404, 
            detail=f"Условия использования на языке '{language}' не найдены"
        )
    
    return terms


@router.get(
    "/privacy-policy",
    response_model=PrivacyPolicyResponse,
    summary="Получить политику конфиденциальности"
)
def get_privacy_policy(
    language: str = Query("ru", description="Язык политики (ru, en, es, it, ar, pt)"),
    db: Session = Depends(get_db)
):
    """Получить политику конфиденциальности на указанном языке."""
    policy = db.query(PrivacyPolicy).filter(PrivacyPolicy.language == language).first()
    
    if not policy:
        raise HTTPException(
            status_code=404, 
            detail=f"Политика конфиденциальности на языке '{language}' не найдена"
        )
    
    return policy


@router.get(
    "/cookie-policy",
    response_model=CookiePolicyResponse,
    summary="Получить политику использования файлов cookie"
)
def get_cookie_policy(
    language: str = Query("ru", description="Язык политики (ru, en, es, it, ar, pt)"),
    db: Session = Depends(get_db)
):
    """Получить политику использования файлов cookie на указанном языке."""
    policy = db.query(CookiePolicy).filter(CookiePolicy.language == language).first()
    
    if not policy:
        raise HTTPException(
            status_code=404, 
            detail=f"Политика использования файлов cookie на языке '{language}' не найдена"
        )
    
    return policy
