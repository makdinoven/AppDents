"""
Утилита для определения предпочитаемого языка пользователя
на основе его покупок и курсов.
"""
from collections import Counter
from sqlalchemy.orm import Session
from typing import Optional

from ..models.models_v2 import User, Purchase, Landing


def get_user_preferred_language(user: User, db: Session) -> str:
    """
    Определяет предпочитаемый язык пользователя на основе языков
    лендингов, с которых он покупал курсы.
    
    Логика:
    1. Берём все покупки пользователя (Purchase)
    2. Для каждой покупки смотрим на landing_id
    3. Получаем язык лендинга
    4. Выбираем самый популярный язык
    5. Если покупок/лендингов нет -> возвращаем "EN"
    
    Args:
        user: Объект пользователя
        db: Сессия базы данных
        
    Returns:
        Код языка: "EN", "RU", "ES", "PT", "AR", или "IT"
    """
    # Получаем все покупки пользователя с лендингами
    purchases = (
        db.query(Purchase)
        .filter(
            Purchase.user_id == user.id,
            Purchase.landing_id.isnot(None)
        )
        .all()
    )
    
    # Если покупок нет, возвращаем английский по умолчанию
    if not purchases:
        return "EN"
    
    # Собираем языки из лендингов
    languages = []
    for purchase in purchases:
        if purchase.landing_id:
            landing = db.query(Landing).filter(Landing.id == purchase.landing_id).first()
            if landing and landing.language:
                languages.append(landing.language)
    
    # Если не нашли ни одного языка, возвращаем английский
    if not languages:
        return "EN"
    
    # Находим самый популярный язык
    language_counter = Counter(languages)
    most_common_language = language_counter.most_common(1)[0][0]
    
    return most_common_language


def get_user_preferred_language_simple(user: User) -> str:
    """
    Упрощённая версия без дополнительного запроса к БД.
    Использует уже загруженные relationship'ы.
    
    Если у пользователя нет покупок - возвращает "EN".
    
    Args:
        user: Объект пользователя (с загруженным backref purchases)
        
    Returns:
        Код языка: "EN", "RU", "ES", "PT", "AR", или "IT"
    """
    if not hasattr(user, 'purchases') or not user.purchases:
        return "EN"
    
    # Собираем языки из лендингов покупок
    languages = []
    for purchase in user.purchases:
        if purchase.landing and hasattr(purchase.landing, 'language'):
            languages.append(purchase.landing.language)
    
    # Если не нашли ни одного языка, возвращаем английский
    if not languages:
        return "EN"
    
    # Находим самый популярный язык
    language_counter = Counter(languages)
    most_common_language = language_counter.most_common(1)[0][0]
    
    return most_common_language

