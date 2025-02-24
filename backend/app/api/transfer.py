import re

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import json
import logging

from ..db.database import get_async_db  # Функция для получения AsyncSession

router = APIRouter()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

@router.post("/migrate-data")
async def migrate_data(db: AsyncSession = Depends(get_async_db)):
    try:
        migrated_landings = 0
        migrated_courses = 0

        # 1. Отключаем проверки внешних ключей
        await db.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
        await db.commit()

        # 2. Миграция лендингов
        result = await db.execute(text("SELECT * FROM landings"))
        landings_rows = result.mappings().all()  # получаем записи как словари

        for row in landings_rows:
            landing_id = row["id"]
            page_name = row["page_name"] or ""
            course_name = row["course_name"] or ""
            try:
                old_price = float(row["old_price"]) if row["old_price"] and row["old_price"].strip() != "" else None
            except Exception:
                old_price = None
            try:
                new_price = float(row["new_price"]) if row["new_price"] and row["new_price"].strip() != "" else None
            except Exception:
                new_price = None
            course_program = row["course_program"] or ""
            lessons_info = row["lessons_info"] or "{}"
            lecturers_info = row["lecturers_info"] or "{}"
            linked_courses = row["linked_courses"] or "[]"
            preview_photo = row["preview_photo"] or ""

            # Вставляем лендинг (course_id временно 0)
            await db.execute(text("""
                INSERT INTO landing 
                  (id, language, course_id, title, slug, old_price, price, main_text, main_image, sales_count)
                VALUES 
                  (:id, :language, :course_id, :title, :slug, :old_price, :price, :main_text, :main_image, 0)
            """), {
                "id": landing_id,
                "language": "EN",
                "course_id": 0,
                "title": course_name,
                "slug": page_name,
                "old_price": old_price,
                "price": new_price,
                "main_text": course_program,
                "main_image": preview_photo
            })
            migrated_landings += 1

            # Обработка lessons_info – создаём дефолтную секцию и модули
            try:
                lessons_data = json.loads(lessons_info)
            except Exception as e:
                logger.error(f"Ошибка парсинга lessons_info для лендинга id={landing_id}: {e}")
                lessons_data = {}
            # lessons_data может быть dict или list
            if isinstance(lessons_data, dict):
                lessons_iterable = lessons_data.items()
            elif isinstance(lessons_data, list):
                lessons_iterable = enumerate(lessons_data)
            else:
                lessons_iterable = []
            if lessons_iterable:
                await db.execute(text("INSERT INTO sections (course_id, name) VALUES (0, :name)"), {"name": "Default Section"})
                sec_result = await db.execute(text("SELECT LAST_INSERT_ID() as sec_id"))
                sec_id = sec_result.scalar()
                for key, lesson in lessons_iterable:
                    if not isinstance(lesson, dict):
                        continue
                    video_link = lesson.get("link", "")
                    lesson_name = lesson.get("name") or lesson.get("lesson_name", "")
                    duration = lesson.get("duration", "")
                    program_text = lesson.get("program", "")
                    await db.execute(text("""
                        INSERT INTO modules (section_id, title, short_video_link, full_video_link, program_text, duration)
                        VALUES (:section_id, :title, :short_video_link, NULL, :program_text, :duration)
                    """), {
                        "section_id": sec_id,
                        "title": lesson_name,
                        "short_video_link": video_link,
                        "program_text": program_text,
                        "duration": duration
                    })

            # Обработка lecturers_info – вставляем авторов и связываем их с лендингом
            try:
                lecturers_data = json.loads(lecturers_info)
            except Exception as e:
                logger.error(f"Ошибка парсинга lecturers_info для лендинга id={landing_id}: {e}")
                lecturers_data = {}
            if isinstance(lecturers_data, dict):
                lecturers_iterable = lecturers_data.items()
            elif isinstance(lecturers_data, list):
                lecturers_iterable = enumerate(lecturers_data)
            else:
                lecturers_iterable = []
            for key, lecturer in lecturers_iterable:
                if not isinstance(lecturer, dict):
                    continue
                lecturer_name = lecturer.get("name", "")
                lecturer_desc = lecturer.get("description", "")
                if not lecturer_name:
                    continue
                # Проверяем, существует ли автор
                result_author = await db.execute(text("SELECT id FROM authors WHERE name = :name"), {"name": lecturer_name})
                author_id = result_author.scalar()
                if not author_id:
                    await db.execute(text("""
                        INSERT INTO authors (name, description, photo)
                        VALUES (:name, :description, '')
                    """), {"name": lecturer_name, "description": lecturer_desc})
                    result_author = await db.execute(text("SELECT LAST_INSERT_ID() as author_id"))
                    author_id = result_author.scalar()
                # Связываем автора с лендингом
                await db.execute(text("""
                    INSERT INTO landing_authors (landing_id, author_id)
                    VALUES (:landing_id, :author_id)
                """), {"landing_id": landing_id, "author_id": author_id})

            # Обработка linked_courses – если там ровно один элемент, обновляем course_id лендинга
            try:
                linked_list = json.loads(linked_courses)
                if isinstance(linked_list, list) and len(linked_list) == 1:
                    course_id_link = linked_list[0]
                    await db.execute(text("UPDATE landing SET course_id = :course_id WHERE id = :landing_id"), {
                        "course_id": course_id_link,
                        "landing_id": landing_id
                    })
            except Exception as e:
                logger.error(f"Ошибка обработки linked_courses для лендинга id={landing_id}: {e}")

        # 3. Миграция курсов
        result_course = await db.execute(text("SELECT * FROM course"))
        course_rows = result_course.mappings().all()
        for row in course_rows:
            course_id = row["id"]
            name = row["name"] or ""
            description = row["description"] or ""
            lessons_json = row["lessons"] or "{}"
            await db.execute(text("INSERT INTO courses (id, name, description) VALUES (:id, :name, :description)"),
                             {"id": course_id, "name": name, "description": description})
            migrated_courses += 1
            try:
                lessons_data = json.loads(lessons_json)
            except Exception as e:
                logger.error(f"Ошибка парсинга lessons для курса id={course_id}: {e}")
                lessons_data = {}
            if isinstance(lessons_data, dict):
                lessons_iterable = lessons_data.items()
            elif isinstance(lessons_data, list):
                lessons_iterable = enumerate(lessons_data)
            else:
                lessons_iterable = []
            for sec_key, sec in lessons_iterable:
                section_name = sec.get("section_name", "Default Section")
                await db.execute(text("INSERT INTO sections (course_id, name) VALUES (:course_id, :name)"),
                                 {"course_id": course_id, "name": section_name})
                sec_result = await db.execute(text("SELECT LAST_INSERT_ID() as sec_id"))
                sec_id = sec_result.scalar()
                lessons_arr = sec.get("lessons", [])
                for lesson in lessons_arr:
                    lesson_name = lesson.get("lesson_name", "")
                    video_link = lesson.get("video_link", "")
                    duration = lesson.get("duration", "")
                    program_text = lesson.get("program", "")
                    await db.execute(text("""
                        INSERT INTO modules (section_id, title, full_video_link, short_video_link, program_text, duration)
                        VALUES (:section_id, :title, :full_video_link, NULL, :program_text, :duration)
                    """), {
                        "section_id": sec_id,
                        "title": lesson_name,
                        "full_video_link": video_link,
                        "program_text": program_text,
                        "duration": duration
                    })
        await db.commit()

        # 4. Включаем проверки внешних ключей обратно
        await db.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
        await db.commit()

        return JSONResponse({
            "status": "Migration completed",
            "landings_migrated": migrated_landings,
            "courses_migrated": migrated_courses
        })
    except Exception as e:
        await db.rollback()
        logger.error(f"Ошибка миграции: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update-modules-duration")
async def update_modules_duration(db: AsyncSession = Depends(get_async_db)):
    """
    Обновляет поле duration для всех записей в таблице modules, где duration пустое.
    Пытаемся извлечь значение длительности из program_text по шаблону (например, 'duration: 1h 1min').
    Если не удаётся, устанавливаем 'N/A'.
    """
    try:
        result = await db.execute(text("SELECT id, program_text, duration FROM modules"))
        modules = result.mappings().all()
        updated = 0

        for module in modules:
            mod_id = module["id"]
            current_duration = module["duration"]
            if current_duration and current_duration.strip():
                continue  # если уже заполнено, пропускаем

            program_text = module["program_text"] or ""
            # Пробуем найти шаблон "duration:" (без учета регистра)
            match = re.search(r"duration[:\s-]+([\d\w\s]+)", program_text, re.IGNORECASE)
            if match:
                new_duration = match.group(1).strip()
            else:
                new_duration = "N/A"

            await db.execute(text("UPDATE modules SET duration = :duration WHERE id = :id"),
                             {"duration": new_duration, "id": mod_id})
            updated += 1

        await db.commit()
        return JSONResponse({"status": "Modules duration updated", "modules_updated": updated})
    except Exception as e:
        await db.rollback()
        logger.error(f"Ошибка обновления длительности модулей: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update-landings-courseid")
async def update_landings_courseid(db: AsyncSession = Depends(get_async_db)):
    """
    Обновляет поле course_id в таблице landing,
    беря значение из столбца linked_courses таблицы landings.
    Для каждой записи мы извлекаем первый элемент JSON-массива linked_courses
    (если он существует) и устанавливаем его как course_id в таблице landing.
    """
    try:
        # Выполняем запрос, который обновляет landing, объединяя с таблицей landings по id
        update_query = text("""
            UPDATE landing l
            JOIN landings ls ON ls.id = l.id
            SET l.course_id = CAST(JSON_UNQUOTE(JSON_EXTRACT(ls.linked_courses, '$[0]')) AS UNSIGNED)
            WHERE l.course_id = 0;
        """)
        await db.execute(update_query)
        await db.commit()
        return JSONResponse({"status": "Updated course_id in landing using linked_courses from landings"})
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating landing course_id: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update-modules-full-video-link")
async def update_modules_full_video_link(db: AsyncSession = Depends(get_async_db)):
    """
    Для каждого курса извлекает JSON из столбца lessons (таблица course).
    В этом JSON находятся секции, а в каждой секции – список уроков с полями
    "video_link" (или "link") и "lesson_name" (или "name"). Для каждого урока
    обновляет поле full_video_link в таблице modules, где title совпадает с lesson_name
    и модуль принадлежит секции с нужным course_id.
    """
    try:
        updated_count = 0
        result = await db.execute(text("SELECT id, lessons FROM course"))
        courses = result.mappings().all()
        logger.info("Найдено курсов: %d", len(courses))
        for course in courses:
            course_id = course["id"]
            lessons_json = course["lessons"]
            if not lessons_json:
                continue
            try:
                lessons_data = json.loads(lessons_json)
            except Exception as e:
                logger.error(f"Ошибка парсинга JSON для курса id={course_id}: {e}")
                continue

            # Если lessons_data – словарь, берём значения, если список – итерация напрямую
            if isinstance(lessons_data, dict):
                sections = lessons_data.values()
            elif isinstance(lessons_data, list):
                sections = lessons_data
            else:
                logger.error(f"Неожиданный тип lessons для курса id={course_id}: {type(lessons_data)}")
                continue

            for section in sections:
                if not isinstance(section, dict):
                    continue
                lessons_list = section.get("lessons", [])
                for lesson in lessons_list:
                    if not isinstance(lesson, dict):
                        continue
                    # Пытаемся взять ссылку из video_link, если отсутствует – из link
                    video_link = (lesson.get("video_link") or lesson.get("link") or "").strip()
                    # Аналогично, берем название урока
                    lesson_name = (lesson.get("lesson_name") or lesson.get("name") or "").strip()
                    if not video_link or not lesson_name:
                        continue

                    update_query = text("""
                        UPDATE modules
                        SET full_video_link = :video_link
                        WHERE title = :lesson_name
                          AND section_id IN (
                              SELECT id FROM sections WHERE course_id = :course_id
                          )
                    """)
                    res = await db.execute(update_query, {
                        "video_link": video_link,
                        "lesson_name": lesson_name,
                        "course_id": course_id
                    })
                    # Суммируем количество затронутых строк
                    updated_count += res.rowcount if res.rowcount is not None else 0

        await db.commit()
        return JSONResponse({
            "status": "Modules full_video_link updated",
            "updated_count": updated_count
        })
    except Exception as e:
        await db.rollback()
        logger.error(f"Ошибка обновления full_video_link: {e}")
        raise HTTPException(status_code=500, detail=str(e))