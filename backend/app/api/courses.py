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
    ModuleUpdate, CourseFullResponse, CourseFullData,
    # Модель ответа для модуля переиспользуется из schemas.landing (ModuleResponse)
)
from ..schemas.landing import ModuleResponse, LandingCreate
from ..services.course_service import create_course, update_course, delete_course, get_course, list_courses, \
    search_courses
from ..services.landing_service import create_landing, update_landing
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

@router.post(
    "/full",
    response_model=CourseFullResponse,
    summary="Создать курс с лендингом, секциями и модулями",
    description=(
        "Создает новый курс и автоматически генерирует для него лендинг, секции и модули. "
        "Также привязывает авторов к лендингу (если передан список id) и устанавливает остальные поля лендинга, "
        "такие как тег, изображение, описание, цены и т.д. Все данные передаются агрегированно."
    )
)
def create_full_course(
    full_data: CourseFullData,
    db: Session = Depends(get_db),
    current_admin: any = Depends(require_roles("admin"))
):
    try:
        # 1. Создаем курс
        new_course = create_course(
            db,
            CourseCreate(name=full_data.name, description=full_data.description)
        )
        if not new_course or not new_course.id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": {
                        "code": "COURSE_CREATE_ERROR",
                        "message": "Не удалось создать курс",
                        "translation_key": "error.course_create_error",
                        "params": {}
                    }
                }
            )

        # Если по каким-либо причинам у нового курса уже есть лендинг, удаляем его
        if new_course.landing:
            db.delete(new_course.landing)
            db.flush()

        # 2. Создаем лендинг с установкой course_id
        from ..schemas.landing import LandingCreate  # входящая схема для лендинга
        landing_create_dict = full_data.landing.dict()
        landing_create_dict["course_id"] = new_course.id
        new_landing = create_landing(db, LandingCreate(**landing_create_dict))
        if not new_landing or not new_landing.id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": {
                        "code": "LANDING_CREATE_ERROR",
                        "message": "Не удалось создать лендинг",
                        "translation_key": "error.landing_create_error",
                        "params": {"course_id": new_course.id}
                    }
                }
            )
        new_course.landing = new_landing

        # 3. Создаем секции и модули
        from ..schemas.course import SectionCreate, ModuleCreate
        for section_data in full_data.sections or []:
            new_section = create_section(db, new_course.id, SectionCreate(name=section_data.name))
            if not new_section or not new_section.id:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "error": {
                            "code": "SECTION_CREATE_ERROR",
                            "message": f"Не удалось создать секцию '{section_data.name}'",
                            "translation_key": "error.section_create_error",
                            "params": {"course_id": new_course.id}
                        }
                    }
                )
            for module_data in section_data.modules or []:
                new_module = create_module(
                    db,
                    new_section.id,
                    ModuleCreate(
                        title=module_data.title,
                        short_video_link=module_data.short_video_link,
                        full_video_link=module_data.full_video_link,
                        program_text=module_data.program_text,
                        duration=module_data.duration
                    )
                )
                if not new_module or not new_module.id:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail={
                            "error": {
                                "code": "MODULE_CREATE_ERROR",
                                "message": f"Не удалось создать модуль '{module_data.title}'",
                                "translation_key": "error.module_create_error",
                                "params": {"section_id": new_section.id}
                            }
                        }
                    )

        db.commit()
        db.refresh(new_course)

        # Формируем ответ по схеме CourseFullResponse
        response = CourseFullResponse(
            id=new_course.id,
            name=new_course.name,
            description=new_course.description,
            landing={
                "title": new_course.landing.title,
                "old_price": new_course.landing.old_price,
                "price": new_course.landing.price,
                "main_image": new_course.landing.main_image,
                "main_text": new_course.landing.main_text,
                "language": new_course.landing.language,
                "tag_id": new_course.landing.tag_id,
                "authors": [author.id for author in new_course.landing.authors] if new_course.landing.authors else [],
                "sales_count": new_course.landing.sales_count,
            },
            sections=[
                {
                    "id": section.id,
                    "name": section.name,
                    "modules": [
                        {
                            "id": module.id,
                            "title": module.title,
                            "short_video_link": module.short_video_link,
                            "full_video_link": module.full_video_link,
                            "program_text": module.program_text,
                            "duration": module.duration,
                        }
                        for module in section.modules
                    ]
                }
                for section in new_course.sections
            ]
        )
        return response
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "COURSE_FULL_CREATE_ERROR",
                    "message": str(e),
                    "translation_key": "error.course_full_create_error",
                    "params": {}
                }
            }
        )

@router.put(
    "/full/{course_id}",
    response_model=CourseFullResponse,
    summary="Полное обновление курса с лендингом, секциями и модулями",
    description=(
        "Обновляет данные курса, лендинга (включая привязку авторов), секций и модулей за один запрос. "
        "Если в теле запроса передан id секции или модуля, происходит обновление, иначе создаются новые записи. "
        "Объекты, отсутствующие в запросе, будут удалены."
    )
)
def update_full_course(
    course_id: int,
    full_data: CourseFullData,
    db: Session = Depends(get_db),
    current_admin: any = Depends(require_roles("admin"))
):
    try:
        # Обновляем основные поля курса
        course = get_course(db, course_id)
        course.name = full_data.name
        course.description = full_data.description

        # Обновляем лендинг
        if course.landing:
            from ..schemas.landing import LandingUpdate
            landing_update_data = full_data.landing.dict()
            landing_update_data["course_id"] = course.id
            update_landing(db, course.landing.id, LandingUpdate(**landing_update_data))
        else:
            from ..schemas.landing import LandingCreate
            landing_create_dict = full_data.landing.dict()
            landing_create_dict["course_id"] = course.id
            new_landing = create_landing(db, LandingCreate(**landing_create_dict))
            course.landing = new_landing

        # Обработка секций и модулей
        input_section_ids = set()
        for section_data in full_data.sections or []:
            if hasattr(section_data, "id") and section_data.id:
                input_section_ids.add(section_data.id)
                section = db.query(Section).filter(
                    Section.id == section_data.id, Section.course_id == course_id
                ).first()
                if section:
                    section.name = section_data.name
                    input_module_ids = set()
                    for module_data in section_data.modules or []:
                        if hasattr(module_data, "id") and module_data.id:
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
                            new_module = Module(
                                section_id=section.id,
                                title=module_data.title,
                                short_video_link=module_data.short_video_link,
                                full_video_link=module_data.full_video_link,
                                program_text=module_data.program_text,
                                duration=module_data.duration
                            )
                            db.add(new_module)
                    # Удаляем модули, отсутствующие в обновлении
                    for module in list(section.modules):
                        if module.id not in input_module_ids:
                            db.delete(module)
                else:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Секция с id {section_data.id} не найдена"
                    )
            else:
                # Создаем новую секцию
                new_section = Section(
                    course_id=course.id,
                    name=section_data.name
                )
                db.add(new_section)
                db.flush()  # чтобы получить new_section.id
                for module_data in section_data.modules or []:
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
        for section in list(course.sections):
            if section.id not in input_section_ids:
                db.delete(section)

        db.commit()
        db.refresh(course)

        # Формируем ответ по схеме CourseFullResponse
        response = CourseFullResponse(
            id=course.id,
            name=course.name,
            description=course.description,
            landing={
                "title": course.landing.title,
                "old_price": course.landing.old_price,
                "price": course.landing.price,
                "main_image": course.landing.main_image,
                "main_text": course.landing.main_text,
                "language": course.landing.language,
                "tag_id": course.landing.tag_id,
                "authors": [author.id for author in course.landing.authors] if course.landing and course.landing.authors else [],
                "sales_count": course.landing.sales_count,
            },
            sections=[
                {
                    "id": section.id,
                    "name": section.name,
                    "modules": [
                        {
                            "id": module.id,
                            "title": module.title,
                            "short_video_link": module.short_video_link,
                            "full_video_link": module.full_video_link,
                            "program_text": module.program_text,
                            "duration": module.duration,
                        }
                        for module in section.modules
                    ]
                }
                for section in course.sections
            ]
        )
        return response
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "COURSE_FULL_UPDATE_ERROR",
                    "message": str(e),
                    "translation_key": "error.course_full_update_error",
                    "params": {}
                }
            }
        )

@router.get(
    "/full/{course_id}",
    response_model=CourseFullResponse,
    summary="Получить полный курс с лендингом, секциями и модулями",
    description=(
        "Возвращает полный объект курса, включающий лендинг, секции и модули, "
        "со структурой, соответствующей агрегированным данным для обновления (PUT)."
    )
)
def get_full_course(
    course_id: int,
    db: Session = Depends(get_db)
):
    try:
        course = get_course(db, course_id)
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "COURSE_NOT_FOUND",
                        "message": "Курс не найден",
                        "translation_key": "error.course_not_found",
                        "params": {"course_id": course_id}
                    }
                }
            )

        # Формируем ответ согласно схеме CourseFullResponse
        response = {
            "id": course.id,
            "name": course.name,
            "description": course.description,
            "landing": {
                "title": course.landing.title if course.landing else None,
                "old_price": course.landing.old_price if course.landing else None,
                "price": course.landing.price if course.landing else None,
                "main_image": course.landing.main_image if course.landing else None,
                "main_text": course.landing.main_text if course.landing else None,
                "language": course.landing.language if course.landing else None,
                "tag_id": course.landing.tag_id if course.landing else None,
                "authors": [author.id for author in course.landing.authors] if course.landing and course.landing.authors else [],
                "sales_count": course.landing.sales_count if course.landing else 0,
            },
            "sections": [
                {
                    "id": section.id,
                    "name": section.name,
                    "modules": [
                        {
                            "id": module.id,
                            "title": module.title,
                            "short_video_link": module.short_video_link,
                            "full_video_link": module.full_video_link,
                            "program_text": module.program_text,
                            "duration": module.duration,
                        }
                        for module in section.modules
                    ]
                }
                for section in course.sections
            ]
        }
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "COURSE_FULL_GET_ERROR",
                    "message": str(e),
                    "translation_key": "error.course_full_get_error",
                    "params": {"course_id": course_id}
                }
            }
        )

@router.delete(
    "/full/{course_id}",
    response_model=CourseFullResponse,
    summary="Полное удаление курса с лендингом, секциями и модулями",
    description=(
        "Удаляет курс и все связанные с ним объекты: лендинг, секции, модули, а также "
        "привязки лендинга к курсу и авторов к лендингу."
    )
)
def delete_full_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_admin: any = Depends(require_roles("admin"))
):
    try:
        # Находим курс по идентификатору
        course = get_course(db, course_id)
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "COURSE_NOT_FOUND",
                        "message": "Курс не найден",
                        "translation_key": "error.course_not_found",
                        "params": {"course_id": course_id}
                    }
                }
            )

        # Сохраняем данные курса для формирования ответа до удаления
        response_data = {
            "id": course.id,
            "name": course.name,
            "description": course.description,
            "landing": {
                "title": course.landing.title if course.landing else None,
                "old_price": course.landing.old_price if course.landing else None,
                "price": course.landing.price if course.landing else None,
                "main_image": course.landing.main_image if course.landing else None,
                "main_text": course.landing.main_text if course.landing else None,
                "language": course.landing.language if course.landing else None,
                "tag_id": course.landing.tag_id if course.landing else None,
                "authors": [author.id for author in course.landing.authors] if course.landing and course.landing.authors else [],
                "sales_count": course.landing.sales_count if course.landing else 0,
            },
            "sections": [
                {
                    "id": section.id,
                    "name": section.name,
                    "modules": [
                        {
                            "id": module.id,
                            "title": module.title,
                            "short_video_link": module.short_video_link,
                            "full_video_link": module.full_video_link,
                            "program_text": module.program_text,
                            "duration": module.duration,
                        }
                        for module in section.modules
                    ]
                }
                for section in course.sections
            ]
        }

        # Если у курса есть лендинг, сначала удаляем привязку авторов и сам лендинг
        if course.landing:
            course.landing.authors = []  # очищаем связь many-to-many
            db.delete(course.landing)

        # Удаляем секции и модули
        for section in course.sections:
            for module in section.modules:
                db.delete(module)
            db.delete(section)

        # Удаляем сам курс
        db.delete(course)
        db.commit()

        return response_data
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "COURSE_FULL_DELETE_ERROR",
                    "message": str(e),
                    "translation_key": "error.course_full_delete_error",
                    "params": {"course_id": course_id}
                }
            }
        )