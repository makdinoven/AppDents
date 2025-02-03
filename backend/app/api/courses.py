# api/courses.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from ..dependencies.role_checker import require_roles
from ..models.models import User
from ..schemas.course import (
    CourseCreate,
    CourseUpdate,
    CourseResponse,
    SectionCreate,
    SectionUpdate,
    SectionResponse,
    ModuleCreate,
    ModuleUpdate,
    # Модель ответа для модуля переиспользуется из schemas.landing (ModuleResponse)
)
from ..schemas.landing import ModuleResponse
from ..services.course_service import create_course, update_course, delete_course, get_course, list_courses, \
    search_courses
from ..services.section_service import create_section, update_section, delete_section
from ..services.module_service import create_module, update_module, delete_module, search_modules
from ..db.database import get_db

router = APIRouter()

# --- Эндпоинты для Курсов ---
@router.post("/", response_model=CourseResponse, summary="Создать курс")
def create_course_endpoint(course: CourseCreate, db: Session = Depends(get_db),current_admin: User = Depends(require_roles("admin"))):
    try:
        new_course = create_course(db, course)
        return new_course
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/", response_model=List[CourseResponse], summary="Список курсов")
def list_courses_endpoint(db: Session = Depends(get_db)):
    courses = list_courses(db)
    return courses

@router.get("/{course_id}", response_model=CourseResponse, summary="Получить курс")
def get_course_endpoint(course_id: int, db: Session = Depends(get_db)):
    try:
        course = get_course(db, course_id)
        return course
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.put("/{course_id}", response_model=CourseResponse, summary="Обновить курс")
def update_course_endpoint(course_id: int, course: CourseUpdate, db: Session = Depends(get_db),current_admin: User = Depends(require_roles("admin"))):
    try:
        updated_course = update_course(db, course_id, course)
        return updated_course
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/{course_id}", response_model=CourseResponse, summary="Удалить курс")
def delete_course_endpoint(course_id: int, db: Session = Depends(get_db),current_admin: User = Depends(require_roles("admin"))):
    try:
        deleted_course = delete_course(db, course_id)
        return deleted_course
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

# --- Эндпоинты для Секций ---
@router.post("/{course_id}/sections", response_model=SectionResponse, summary="Создать секцию курса")
def create_section_endpoint(course_id: int, section: SectionCreate, db: Session = Depends(get_db),current_admin: User = Depends(require_roles("admin"))):
    try:
        new_section = create_section(db, course_id, section)
        return new_section
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.put("/{course_id}/sections/{section_id}", response_model=SectionResponse, summary="Обновить секцию курса")
def update_section_endpoint(course_id: int, section_id: int, section: SectionUpdate, db: Session = Depends(get_db),current_admin: User = Depends(require_roles("admin"))):
    try:
        updated_section = update_section(db, section_id, section)
        return updated_section
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/{course_id}/sections/{section_id}", response_model=SectionResponse, summary="Удалить секцию курса")
def delete_section_endpoint(course_id: int, section_id: int, db: Session = Depends(get_db),current_admin: User = Depends(require_roles("admin"))):
    try:
        deleted_section = delete_section(db, section_id)
        return deleted_section
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

# --- Эндпоинты для Модулей (вложенные в секцию) ---
@router.post("/{course_id}/sections/{section_id}/modules", response_model=dict, summary="Создать модуль в секции")
def create_module_endpoint(course_id: int, section_id: int, module: ModuleCreate, db: Session = Depends(get_db),current_admin: User = Depends(require_roles("admin"))):
    try:
        new_module = create_module(db, section_id, module)
        # Для ответа можно вернуть словарь или использовать схему ответа, если она уже есть
        return {
            "id": new_module.id,
            "title": new_module.title,
            "short_video_link": new_module.short_video_link,
            "full_video_link": new_module.full_video_link,
            "program_text": new_module.program_text,
            "duration": new_module.duration
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.put("/{course_id}/sections/{section_id}/modules/{module_id}", response_model=dict, summary="Обновить модуль")
def update_module_endpoint(course_id: int, section_id: int, module_id: int, module: ModuleUpdate, db: Session = Depends(get_db),current_admin: User = Depends(require_roles("admin"))):
    try:
        updated_module = update_module(db, module_id, module)
        return {
            "id": updated_module.id,
            "title": updated_module.title,
            "short_video_link": updated_module.short_video_link,
            "full_video_link": updated_module.full_video_link,
            "program_text": updated_module.program_text,
            "duration": updated_module.duration
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/{course_id}/sections/{section_id}/modules/{module_id}", response_model=dict, summary="Удалить модуль")
def delete_module_endpoint(course_id: int, section_id: int, module_id: int, db: Session = Depends(get_db),current_admin: User = Depends(require_roles("admin"))):
    try:
        deleted_module = delete_module(db, module_id)
        return {
            "id": deleted_module.id,
            "title": deleted_module.title,
            "short_video_link": deleted_module.short_video_link,
            "full_video_link": deleted_module.full_video_link,
            "program_text": deleted_module.program_text,
            "duration": deleted_module.duration
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/search_modules",
    response_model=List[ModuleResponse],
    summary="Поиск модулей",
    description="Ищет модули по названию (регистронезависимый поиск)."
)
def search_modules_endpoint(query: str = Query(..., description="Строка для поиска модулей по названию"), db: Session = Depends(get_db)):
    modules = search_modules(db, query)
    return modules

@router.get(
    "/search_courses",
    response_model=List[CourseResponse],
    summary="Поиск курсов",
    description="Ищет курсы по названию (регистронезависимый поиск)."
)
def search_courses_endpoint(query: str = Query(..., description="Строка для поиска курсов по названию"), db: Session = Depends(get_db)):
    courses = search_courses(db, query)
    return courses