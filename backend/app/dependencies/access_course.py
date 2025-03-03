from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..dependencies.auth import get_current_user
from ..models.models_v2 import Course, User

def get_course_detail_with_access(course_id: int,
                                  db: Session = Depends(get_db),
                                  current_user: User = Depends(get_current_user)
                                 ) -> Course:
    """
    Возвращает курс, если:
      - пользователь является администратором, либо
      - пользователь купил этот курс (курс присутствует в current_user.courses)
    Если курс не найден – возвращает 404,
    если нет доступа – возвращает 403.
    """
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if current_user.role == "admin":
        return course

    # Для обычного пользователя проверяем наличие курса среди купленных
    purchased_course_ids = [c.id for c in current_user.courses]  # предполагается, что отношение настроено
    if course.id not in purchased_course_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You did not purchase this course."
        )
    return course
