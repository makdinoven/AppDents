# api/courses.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from ..dependencies.role_checker import require_roles
from ..models.models import User, Section, Module
from ..schemas.course import (
    CourseCreate,
    CourseUpdate,
    CourseResponse,
    SectionCreate,
    SectionUpdate,
    SectionResponse,
    ModuleCreate,
    ModuleUpdate, CourseFullUpdate,
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
@router.post("/", response_model=CourseResponse, summary="Create course")
def create_course_endpoint(course: CourseCreate, db: Session = Depends(get_db),current_admin: User = Depends(require_roles("admin"))):
    try:
        new_course = create_course(db, course)
        return new_course
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/", response_model=List[CourseResponse], summary="List courses")
def list_courses_endpoint(db: Session = Depends(get_db)):
    courses = list_courses(db)
    return courses

@router.get("/{course_id}", response_model=CourseResponse, summary="Get course")
def get_course_endpoint(course_id: int, db: Session = Depends(get_db)):
    try:
        course = get_course(db, course_id)
        return course
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.put("/{course_id}", response_model=CourseResponse, summary="Update course")
def update_course_endpoint(course_id: int, course: CourseUpdate, db: Session = Depends(get_db),current_admin: User = Depends(require_roles("admin"))):
    try:
        updated_course = update_course(db, course_id, course)
        return updated_course
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/{course_id}", response_model=CourseResponse, summary="Delete course")
def delete_course_endpoint(course_id: int, db: Session = Depends(get_db),current_admin: User = Depends(require_roles("admin"))):
    try:
        deleted_course = delete_course(db, course_id)
        return deleted_course
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

# --- Эндпоинты для Секций ---
@router.post("/{course_id}/sections", response_model=SectionResponse, summary="Create section")
def create_section_endpoint(course_id: int, section: SectionCreate, db: Session = Depends(get_db),current_admin: User = Depends(require_roles("admin"))):
    try:
        new_section = create_section(db, course_id, section)
        return new_section
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.put("/{course_id}/sections/{section_id}", response_model=SectionResponse, summary="Update section")
def update_section_endpoint(course_id: int, section_id: int, section: SectionUpdate, db: Session = Depends(get_db),current_admin: User = Depends(require_roles("admin"))):
    try:
        updated_section = update_section(db, section_id, section)
        return updated_section
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/{course_id}/sections/{section_id}", response_model=SectionResponse, summary="Delete section")
def delete_section_endpoint(course_id: int, section_id: int, db: Session = Depends(get_db),current_admin: User = Depends(require_roles("admin"))):
    try:
        deleted_section = delete_section(db, section_id)
        return deleted_section
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

# --- Эндпоинты для Модулей (вложенные в секцию) ---
@router.post("/{course_id}/sections/{section_id}/modules", response_model=dict, summary="Create section in course")
def create_module_endpoint(course_id: int, section_id: int, module: ModuleCreate, db: Session = Depends(get_db),current_admin: User = Depends(require_roles("admin"))):
    try:
        new_module = create_module(db, section_id, module)
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

@router.put("/{course_id}/sections/{section_id}/modules/{module_id}", response_model=dict, summary="Update module")
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

@router.delete("/{course_id}/sections/{section_id}/modules/{module_id}", response_model=dict, summary="Delete module")
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
    summary="Search modules",
    description="Searching modules by name"
)
def search_modules_endpoint(query: str = Query(..., description="Строка для поиска модулей по названию"), db: Session = Depends(get_db)):
    modules = search_modules(db, query)
    return modules

@router.get(
    "/search_courses",
    response_model=List[CourseResponse],
    summary="Search courses",
    description="Searching courses by name"
)
def search_courses_endpoint(
    query: str = Query(..., description="Search string for courses by name"),
    db: Session = Depends(get_db)
):
    courses = search_courses(db, query)
    if not courses:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "COURSES_NOT_FOUND",
                    "message": "No courses found matching the query",
                    "translation_key": "error.courses_not_found",
                    "params": {"query": query}
                }
            }
        )
    return courses

@router.put("/full/{course_id}", response_model=CourseResponse, summary="Полное обновление курса",description=(
        "Этот эндпоинт обновляет данные курса, включая его секции и модули. "
        "Если в теле запроса передан `id` секции или модуля, происходит обновление, "
        "иначе создаются новые записи. Объекты, отсутствующие в запросе, будут удалены."
    ))
def update_full_course(
    course_id: int,
    course_data: CourseFullUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin"))
):
    try:
        course = get_course(db, course_id)
        # Обновляем основные поля курса
        course.name = course_data.name
        course.description = course_data.description

        # Для контроля секций, которые пришли в обновлении
        input_section_ids = set()

        # Обработка секций
        for section_data in course_data.sections:
            if section_data.id:
                input_section_ids.add(section_data.id)
                # Найти существующую секцию
                section = db.query(Section).filter(
                    Section.id == section_data.id, Section.course_id == course_id
                ).first()
                if section:
                    section.name = section_data.name

                    # Обработка модулей внутри секции
                    input_module_ids = set()
                    for module_data in section_data.modules:
                        if module_data.id:
                            input_module_ids.add(module_data.id)
                            module = db.query(Module).filter(
                                Module.id == module_data.id, Module.section_id == section.id
                            ).first()
                            if module:
                                module.title = module_data.title
                                module.short_video_link = module_data.short_video_link
                                module.full_video_link = module_data.full_video_link
                                module.program_text = module_data.program_text
                                module.duration = module_data.duration
                        else:
                            # Создание нового модуля
                            new_module = Module(
                                section_id=section.id,
                                title=module_data.title,
                                short_video_link=module_data.short_video_link,
                                full_video_link=module_data.full_video_link,
                                program_text=module_data.program_text,
                                duration=module_data.duration
                            )
                            db.add(new_module)

                    # Удаляем модули, которых нет в обновлении
                    for module in section.modules:
                        if module.id not in input_module_ids:
                            db.delete(module)
                else:
                    raise HTTPException(status_code=404, detail=f"Секция с id {section_data.id} не найдена")
            else:
                # Создание новой секции
                new_section = Section(
                    course_id=course.id,
                    name=section_data.name
                )
                db.add(new_section)
                db.flush()  # Для получения new_section.id

                # Создание модулей для новой секции
                for module_data in section_data.modules:
                    new_module = Module(
                        section_id=new_section.id,
                        title=module_data.title,
                        short_video_link=module_data.short_video_link,
                        full_video_link=module_data.full_video_link,
                        program_text=module_data.program_text,
                        duration=module_data.duration
                    )
                    db.add(new_module)

        # Удаляем секции, которых нет в обновлении
        for section in course.sections:
            if section.id not in input_section_ids:
                db.delete(section)

        db.commit()
        db.refresh(course)
        return course
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))