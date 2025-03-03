# import re
#
# from fastapi import APIRouter, Depends, HTTPException
# from fastapi.responses import JSONResponse
# from sqlalchemy import text
# from sqlalchemy.ext.asyncio import AsyncSession
# import json
# import logging
#
# from ..db.database import get_async_db  # Функция для получения AsyncSession
#
# router = APIRouter()
# logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)
#
# @router.post("/migrate-data")
# async def migrate_data(db: AsyncSession = Depends(get_async_db)):
#     try:
#         migrated_landings = 0
#         migrated_courses = 0
#
#         # 1. Отключаем проверки внешних ключей
#         await db.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
#         await db.commit()
#
#         # 2. Миграция лендингов
#         result = await db.execute(text("SELECT * FROM landings"))
#         landings_rows = result.mappings().all()  # получаем записи как словари
#
#         for row in landings_rows:
#             landing_id = row["id"]
#             page_name = row["page_name"] or ""
#             course_name = row["course_name"] or ""
#             try:
#                 old_price = float(row["old_price"]) if row["old_price"] and row["old_price"].strip() != "" else None
#             except Exception:
#                 old_price = None
#             try:
#                 new_price = float(row["new_price"]) if row["new_price"] and row["new_price"].strip() != "" else None
#             except Exception:
#                 new_price = None
#             course_program = row["course_program"] or ""
#             lessons_info = row["lessons_info"] or "{}"
#             lecturers_info = row["lecturers_info"] or "{}"
#             linked_courses = row["linked_courses"] or "[]"
#             preview_photo = row["preview_photo"] or ""
#
#             # Вставляем лендинг (course_id временно 0)
#             await db.execute(text("""
#                 INSERT INTO landing
#                   (id, language, course_id, title, slug, old_price, price, main_text, main_image, sales_count)
#                 VALUES
#                   (:id, :language, :course_id, :title, :slug, :old_price, :price, :main_text, :main_image, 0)
#             """), {
#                 "id": landing_id,
#                 "language": "EN",
#                 "course_id": 0,
#                 "title": course_name,
#                 "slug": page_name,
#                 "old_price": old_price,
#                 "price": new_price,
#                 "main_text": course_program,
#                 "main_image": preview_photo
#             })
#             migrated_landings += 1
#
#             # Обработка lessons_info – создаём дефолтную секцию и модули
#             try:
#                 lessons_data = json.loads(lessons_info)
#             except Exception as e:
#                 logger.error(f"Ошибка парсинга lessons_info для лендинга id={landing_id}: {e}")
#                 lessons_data = {}
#             # lessons_data может быть dict или list
#             if isinstance(lessons_data, dict):
#                 lessons_iterable = lessons_data.items()
#             elif isinstance(lessons_data, list):
#                 lessons_iterable = enumerate(lessons_data)
#             else:
#                 lessons_iterable = []
#             if lessons_iterable:
#                 await db.execute(text("INSERT INTO sections (course_id, name) VALUES (0, :name)"), {"name": "Default Section"})
#                 sec_result = await db.execute(text("SELECT LAST_INSERT_ID() as sec_id"))
#                 sec_id = sec_result.scalar()
#                 for key, lesson in lessons_iterable:
#                     if not isinstance(lesson, dict):
#                         continue
#                     video_link = lesson.get("link", "")
#                     lesson_name = lesson.get("name") or lesson.get("lesson_name", "")
#                     duration = lesson.get("duration", "")
#                     program_text = lesson.get("program", "")
#                     await db.execute(text("""
#                         INSERT INTO modules (section_id, title, short_video_link, full_video_link, program_text, duration)
#                         VALUES (:section_id, :title, :short_video_link, NULL, :program_text, :duration)
#                     """), {
#                         "section_id": sec_id,
#                         "title": lesson_name,
#                         "short_video_link": video_link,
#                         "program_text": program_text,
#                         "duration": duration
#                     })
#
#             # Обработка lecturers_info – вставляем авторов и связываем их с лендингом
#             try:
#                 lecturers_data = json.loads(lecturers_info)
#             except Exception as e:
#                 logger.error(f"Ошибка парсинга lecturers_info для лендинга id={landing_id}: {e}")
#                 lecturers_data = {}
#             if isinstance(lecturers_data, dict):
#                 lecturers_iterable = lecturers_data.items()
#             elif isinstance(lecturers_data, list):
#                 lecturers_iterable = enumerate(lecturers_data)
#             else:
#                 lecturers_iterable = []
#             for key, lecturer in lecturers_iterable:
#                 if not isinstance(lecturer, dict):
#                     continue
#                 lecturer_name = lecturer.get("name", "")
#                 lecturer_desc = lecturer.get("description", "")
#                 if not lecturer_name:
#                     continue
#                 # Проверяем, существует ли автор
#                 result_author = await db.execute(text("SELECT id FROM authors WHERE name = :name"), {"name": lecturer_name})
#                 author_id = result_author.scalar()
#                 if not author_id:
#                     await db.execute(text("""
#                         INSERT INTO authors (name, description, photo)
#                         VALUES (:name, :description, '')
#                     """), {"name": lecturer_name, "description": lecturer_desc})
#                     result_author = await db.execute(text("SELECT LAST_INSERT_ID() as author_id"))
#                     author_id = result_author.scalar()
#                 # Связываем автора с лендингом
#                 await db.execute(text("""
#                     INSERT INTO landing_authors (landing_id, author_id)
#                     VALUES (:landing_id, :author_id)
#                 """), {"landing_id": landing_id, "author_id": author_id})
#
#             # Обработка linked_courses – если там ровно один элемент, обновляем course_id лендинга
#             try:
#                 linked_list = json.loads(linked_courses)
#                 if isinstance(linked_list, list) and len(linked_list) == 1:
#                     course_id_link = linked_list[0]
#                     await db.execute(text("UPDATE landing SET course_id = :course_id WHERE id = :landing_id"), {
#                         "course_id": course_id_link,
#                         "landing_id": landing_id
#                     })
#             except Exception as e:
#                 logger.error(f"Ошибка обработки linked_courses для лендинга id={landing_id}: {e}")
#
#         # 3. Миграция курсов
#         result_course = await db.execute(text("SELECT * FROM course"))
#         course_rows = result_course.mappings().all()
#         for row in course_rows:
#             course_id = row["id"]
#             name = row["name"] or ""
#             description = row["description"] or ""
#             lessons_json = row["lessons"] or "{}"
#             await db.execute(text("INSERT INTO courses (id, name, description) VALUES (:id, :name, :description)"),
#                              {"id": course_id, "name": name, "description": description})
#             migrated_courses += 1
#             try:
#                 lessons_data = json.loads(lessons_json)
#             except Exception as e:
#                 logger.error(f"Ошибка парсинга lessons для курса id={course_id}: {e}")
#                 lessons_data = {}
#             if isinstance(lessons_data, dict):
#                 lessons_iterable = lessons_data.items()
#             elif isinstance(lessons_data, list):
#                 lessons_iterable = enumerate(lessons_data)
#             else:
#                 lessons_iterable = []
#             for sec_key, sec in lessons_iterable:
#                 section_name = sec.get("section_name", "Default Section")
#                 await db.execute(text("INSERT INTO sections (course_id, name) VALUES (:course_id, :name)"),
#                                  {"course_id": course_id, "name": section_name})
#                 sec_result = await db.execute(text("SELECT LAST_INSERT_ID() as sec_id"))
#                 sec_id = sec_result.scalar()
#                 lessons_arr = sec.get("lessons", [])
#                 for lesson in lessons_arr:
#                     lesson_name = lesson.get("lesson_name", "")
#                     video_link = lesson.get("video_link", "")
#                     duration = lesson.get("duration", "")
#                     program_text = lesson.get("program", "")
#                     await db.execute(text("""
#                         INSERT INTO modules (section_id, title, full_video_link, short_video_link, program_text, duration)
#                         VALUES (:section_id, :title, :full_video_link, NULL, :program_text, :duration)
#                     """), {
#                         "section_id": sec_id,
#                         "title": lesson_name,
#                         "full_video_link": video_link,
#                         "program_text": program_text,
#                         "duration": duration
#                     })
#         await db.commit()
#
#         # 4. Включаем проверки внешних ключей обратно
#         await db.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
#         await db.commit()
#
#         return JSONResponse({
#             "status": "Migration completed",
#             "landings_migrated": migrated_landings,
#             "courses_migrated": migrated_courses
#         })
#     except Exception as e:
#         await db.rollback()
#         logger.error(f"Ошибка миграции: {e}")
#         raise HTTPException(status_code=500, detail=str(e))
#
# @router.post("/update-modules-duration")
# async def update_modules_duration(db: AsyncSession = Depends(get_async_db)):
#     """
#     Обновляет поле duration для всех записей в таблице modules, где duration пустое.
#     Пытаемся извлечь значение длительности из program_text по шаблону (например, 'duration: 1h 1min').
#     Если не удаётся, устанавливаем 'N/A'.
#     """
#     try:
#         result = await db.execute(text("SELECT id, program_text, duration FROM modules"))
#         modules = result.mappings().all()
#         updated = 0
#
#         for module in modules:
#             mod_id = module["id"]
#             current_duration = module["duration"]
#             if current_duration and current_duration.strip():
#                 continue  # если уже заполнено, пропускаем
#
#             program_text = module["program_text"] or ""
#             # Пробуем найти шаблон "duration:" (без учета регистра)
#             match = re.search(r"duration[:\s-]+([\d\w\s]+)", program_text, re.IGNORECASE)
#             if match:
#                 new_duration = match.group(1).strip()
#             else:
#                 new_duration = "N/A"
#
#             await db.execute(text("UPDATE modules SET duration = :duration WHERE id = :id"),
#                              {"duration": new_duration, "id": mod_id})
#             updated += 1
#
#         await db.commit()
#         return JSONResponse({"status": "Modules duration updated", "modules_updated": updated})
#     except Exception as e:
#         await db.rollback()
#         logger.error(f"Ошибка обновления длительности модулей: {e}")
#         raise HTTPException(status_code=500, detail=str(e))
#
# @router.post("/update-landings-courseid")
# async def update_landings_courseid(db: AsyncSession = Depends(get_async_db)):
#     """
#     Обновляет поле course_id в таблице landing,
#     беря значение из столбца linked_courses таблицы landings.
#     Для каждой записи мы извлекаем первый элемент JSON-массива linked_courses
#     (если он существует) и устанавливаем его как course_id в таблице landing.
#     """
#     try:
#         # Выполняем запрос, который обновляет landing, объединяя с таблицей landings по id
#         update_query = text("""
#             UPDATE landing l
#             JOIN landings ls ON ls.id = l.id
#             SET l.course_id = CAST(JSON_UNQUOTE(JSON_EXTRACT(ls.linked_courses, '$[0]')) AS UNSIGNED)
#             WHERE l.course_id = 0;
#         """)
#         await db.execute(update_query)
#         await db.commit()
#         return JSONResponse({"status": "Updated course_id in landing using linked_courses from landings"})
#     except Exception as e:
#         await db.rollback()
#         logger.error(f"Error updating landing course_id: {e}")
#         raise HTTPException(status_code=500, detail=str(e))
#
#
# @router.post("/update-course-modules-full-video-link")
# async def update_course_modules_full_video_link(db: AsyncSession = Depends(get_async_db)):
#     """
#     Для каждого курса из таблицы course:
#       - Извлекает JSON из поля lessons.
#       - Обрабатывает различные структуры JSON:
#            • Если JSON – словарь, то итерация по его значениям;
#            • Если JSON – список, итерация по элементам.
#       - Для каждого секционного объекта извлекает имя секции (ключ "section_name", по умолчанию "Default Section").
#       - Ищет в таблице sections запись с course_id = текущему курсу и TRIM(name)=section_name.
#       - Для каждого урока (ключ "lessons" – массив) извлекает:
#             • название урока (ключ "lesson_name" или "name"),
#             • ссылку (ключ "video_link" или "link").
#       - Затем обновляет в таблице modules для найденной секции (section_id), где TRIM(title)=названию урока, поле full_video_link.
#     Если модуль не найден или данные отсутствуют, выводит предупреждение в лог.
#     Возвращает JSON с количеством обновлённых модулей.
#     """
#     try:
#         updated_total = 0
#         result = await db.execute(text("SELECT id, lessons FROM course"))
#         courses = result.mappings().all()
#         logger.info("Найдено курсов: %d", len(courses))
#
#         for course in courses:
#             course_id = course["id"]
#             lessons_json = course.get("lessons")
#             if not lessons_json:
#                 logger.info(f"Курс id={course_id} не содержит данных в lessons")
#                 continue
#
#             try:
#                 lessons_data = json.loads(lessons_json)
#             except Exception as e:
#                 logger.error(f"Ошибка парсинга lessons для курса id={course_id}: {e}")
#                 continue
#
#             # Определяем, по какому объекту итерировать секции
#             if isinstance(lessons_data, dict):
#                 sections_iter = lessons_data.values()
#             elif isinstance(lessons_data, list):
#                 sections_iter = lessons_data
#             else:
#                 logger.warning(f"Неожиданный тип lessons для курса id={course_id}: {type(lessons_data)}")
#                 continue
#
#             for sec in sections_iter:
#                 if not isinstance(sec, dict):
#                     continue
#                 section_name = (sec.get("section_name") or "Default Section").strip()
#                 # Ищем секцию в таблице sections по course_id и TRIM(name)
#                 sec_result = await db.execute(
#                     text("SELECT id FROM sections WHERE course_id = :course_id AND TRIM(name) = :section_name"),
#                     {"course_id": course_id, "section_name": section_name}
#                 )
#                 sec_row = sec_result.fetchone()
#                 if not sec_row:
#                     logger.warning(f"Секция '{section_name}' не найдена для курса id={course_id}")
#                     continue
#                 section_id = sec_row[0]
#
#                 lessons_arr = sec.get("lessons", [])
#                 if not isinstance(lessons_arr, list):
#                     logger.warning(f"Уроки в секции '{section_name}' курса id={course_id} не являются списком")
#                     continue
#
#                 for lesson in lessons_arr:
#                     if not isinstance(lesson, dict):
#                         continue
#                     lesson_name = (lesson.get("lesson_name") or lesson.get("name") or "").strip()
#                     if not lesson_name:
#                         logger.warning(f"Пустое название урока в курсе id={course_id}, секция '{section_name}'")
#                         continue
#                     # Получаем ссылку: проверяем сначала "video_link", затем "link"
#                     video_link = (lesson.get("video_link") or lesson.get("link") or "").strip()
#                     if not video_link:
#                         logger.warning(
#                             f"Пустая ссылка для урока '{lesson_name}' в курсе id={course_id}, секция '{section_name}'")
#                         continue
#
#                     update_query = text("""
#                         UPDATE modules
#                         SET full_video_link = :video_link
#                         WHERE section_id = :section_id AND TRIM(title) = :lesson_name
#                     """)
#                     res = await db.execute(update_query, {
#                         "video_link": video_link,
#                         "section_id": section_id,
#                         "lesson_name": lesson_name
#                     })
#                     rowcount = res.rowcount if res.rowcount is not None else 0
#                     if rowcount == 0:
#                         logger.warning(
#                             f"Модуль не найден для урока '{lesson_name}' (курс id={course_id}, секция '{section_name}')")
#                     else:
#                         logger.info(
#                             f"Обновлён модуль для урока '{lesson_name}' (курс id={course_id}, секция '{section_name}')")
#                     updated_total += rowcount
#
#         await db.commit()
#         return JSONResponse({
#             "status": "Course modules full_video_link updated",
#             "updated_count": updated_total
#         })
#     except Exception as e:
#         await db.rollback()
#         logger.error(f"Ошибка обновления course modules full_video_link: {e}")
#         raise HTTPException(status_code=500, detail=str(e))
#
#
# @router.post("/verify-landing-modules-short-video-link")
# async def verify_landing_modules_short_video_link(db: AsyncSession = Depends(get_async_db)):
#     """
#     Проходит по всем лендингам (из целевой таблицы landing), для которых course_id != 0,
#     извлекает исходное поле lessons_info из таблицы landings (через JOIN по id)
#     и для каждого урока ищет соответствующий модуль (сравнивая TRIM(title) с именем урока).
#     Если значение short_video_link в модуле не совпадает с ожидаемым (из JSON: "video_link" или "link"),
#     то фиксирует несовпадение.
#
#     Возвращает JSON с количеством проверенных модулей, числом несовпадений и списком несовпадений.
#     """
#     try:
#         mismatches = []
#         total_modules_checked = 0
#
#         # Получаем данные из целевой таблицы landing с данными из исходной таблицы landings
#         query = text("""
#             SELECT l.id, l.course_id, ls.lessons_info
#             FROM landing l
#             JOIN landings ls ON ls.id = l.id
#             WHERE l.course_id != 0;
#         """)
#         result = await db.execute(query)
#         records = result.mappings().all()
#         logger.info("Найдено лендингов для проверки: %d", len(records))
#
#         for record in records:
#             landing_id = record["id"]
#             course_id = record["course_id"]
#             lessons_info = record.get("lessons_info") or "{}"
#             try:
#                 lessons_data = json.loads(lessons_info)
#             except Exception as e:
#                 logger.error(f"Ошибка парсинга lessons_info для лендинга id={landing_id}: {e}")
#                 continue
#
#             # lessons_data может быть dict или list
#             if isinstance(lessons_data, dict):
#                 lessons_iterable = lessons_data.values()
#             elif isinstance(lessons_data, list):
#                 lessons_iterable = lessons_data
#             else:
#                 lessons_iterable = []
#
#             for lesson in lessons_iterable:
#                 if not isinstance(lesson, dict):
#                     continue
#                 expected_link = (lesson.get("video_link") or lesson.get("link") or "").strip()
#                 lesson_name = (lesson.get("lesson_name") or lesson.get("name") or "").strip()
#                 if not lesson_name:
#                     logger.warning(f"Пустое название урока в лендинге id={landing_id}")
#                     continue
#
#                 # Ищем модуль, принадлежащий секциям данного курса, где TRIM(title) = lesson_name
#                 mod_query = text("""
#                     SELECT id, short_video_link, title
#                     FROM modules
#                     WHERE section_id IN (
#                         SELECT id FROM sections WHERE course_id = :course_id
#                     )
#                     AND TRIM(title) = :lesson_name
#                 """)
#                 mod_result = await db.execute(mod_query, {"course_id": course_id, "lesson_name": lesson_name})
#                 modules = mod_result.mappings().all()
#                 total_modules_checked += len(modules)
#                 for mod in modules:
#                     actual_link = (mod.get("short_video_link") or "").strip()
#                     if actual_link != expected_link:
#                         mismatches.append({
#                             "landing_id": landing_id,
#                             "course_id": course_id,
#                             "module_id": mod["id"],
#                             "lesson_name": lesson_name,
#                             "expected_link": expected_link,
#                             "actual_link": actual_link
#                         })
#
#         return JSONResponse({
#             "status": "Verification completed",
#             "total_modules_checked": total_modules_checked,
#             "mismatches_found": len(mismatches),
#             "mismatches": mismatches
#         })
#
#     except Exception as e:
#         await db.rollback()
#         logger.error(f"Ошибка проверки landing modules short_video_link: {e}")
#         raise HTTPException(status_code=500, detail=str(e))
#
# @router.get("/check-migration")
# async def check_migration(db: AsyncSession = Depends(get_async_db)):
#     """
#     Сверяет количество секций и модулей, ожидаемых исходя из данных в таблице course (поле lessons),
#     с фактическими значениями в целевых таблицах courses, sections и modules.
#     Дополнительно считает, сколько курсов имеют нулевые ожидаемые или фактические значения.
#     Возвращает JSON со сравнением по каждому курсу и сводной статистикой.
#     """
#     try:
#         # 1. Извлекаем исходные данные из таблицы course
#         result_source = await db.execute(text("SELECT id, lessons FROM course"))
#         source_courses = result_source.mappings().all()
#
#         expected = {}
#         for row in source_courses:
#             course_id = row["id"]
#             lessons_json = row["lessons"] or "{}"
#             try:
#                 lessons_data = json.loads(lessons_json)
#             except Exception as e:
#                 logger.error(f"Ошибка парсинга lessons для курса id={course_id}: {e}")
#                 lessons_data = {}
#
#             expected_section_count = 0
#             expected_module_count = 0
#             if isinstance(lessons_data, dict):
#                 for sec in lessons_data.values():
#                     expected_section_count += 1
#                     lessons_arr = sec.get("lessons", [])
#                     if isinstance(lessons_arr, list):
#                         expected_module_count += len(lessons_arr)
#             elif isinstance(lessons_data, list):
#                 expected_section_count = len(lessons_data)
#                 for sec in lessons_data:
#                     lessons_arr = sec.get("lessons", [])
#                     if isinstance(lessons_arr, list):
#                         expected_module_count += len(lessons_arr)
#             else:
#                 logger.warning(f"Неожиданный тип lessons для курса id={course_id}: {type(lessons_data)}")
#
#             expected[course_id] = {
#                 "expected_sections": expected_section_count,
#                 "expected_modules": expected_module_count
#             }
#
#         # 2. Извлекаем фактические данные из целевых таблиц
#         result_target = await db.execute(text("""
#             SELECT c.id AS course_id,
#                    COUNT(DISTINCT s.id) AS section_count,
#                    COUNT(m.id) AS module_count
#             FROM courses c
#             LEFT JOIN sections s ON s.course_id = c.id
#             LEFT JOIN modules m ON m.section_id = s.id
#             GROUP BY c.id
#         """))
#         target_counts = result_target.mappings().all()
#         actual = {}
#         for row in target_counts:
#             course_id = row["course_id"]
#             actual[course_id] = {
#                 "actual_sections": row["section_count"],
#                 "actual_modules": row["module_count"]
#             }
#
#         # 3. Формируем сравнение для каждого курса и одновременно считаем курсы с нулевыми значениями
#         comparison = []
#         zero_expected_sections = 0
#         zero_expected_modules = 0
#         zero_actual_sections = 0
#         zero_actual_modules = 0
#
#         for course_id, exp in expected.items():
#             act = actual.get(course_id, {"actual_sections": 0, "actual_modules": 0})
#             if exp["expected_sections"] == 0:
#                 zero_expected_sections += 1
#             if exp["expected_modules"] == 0:
#                 zero_expected_modules += 1
#             if act["actual_sections"] == 0:
#                 zero_actual_sections += 1
#             if act["actual_modules"] == 0:
#                 zero_actual_modules += 1
#
#             comparison.append({
#                 "course_id": course_id,
#                 "expected_sections": exp["expected_sections"],
#                 "expected_modules": exp["expected_modules"],
#                 "actual_sections": act["actual_sections"],
#                 "actual_modules": act["actual_modules"]
#             })
#
#         summary = {
#             "total_courses": len(expected),
#             "courses_with_zero_expected_sections": zero_expected_sections,
#             "courses_with_zero_expected_modules": zero_expected_modules,
#             "courses_with_zero_actual_sections": zero_actual_sections,
#             "courses_with_zero_actual_modules": zero_actual_modules
#         }
#
#         return JSONResponse({
#             "comparison": comparison,
#             "summary": summary
#         })
#     except Exception as e:
#         logger.error(f"Ошибка в check_migration: {e}")
#         raise HTTPException(status_code=500, detail=str(e))
#
#
# @router.post("/update-sections-from-course")
# async def update_sections_from_course(db: AsyncSession = Depends(get_async_db)):
#     """
#     Для каждого курса (из таблицы course) извлекает JSON из столбца lessons,
#     затем для каждой секции (ключ "section_name") проверяет, существует ли запись в таблице sections с
#     соответствующим course_id и именем (TRIM(name)). Если такой записи нет – вставляет новую.
#
#     Возвращает сводную информацию по количеству обработанных курсов и добавленных секций.
#     """
#     try:
#         total_courses = 0
#         new_sections_added = 0
#
#         # Извлекаем все курсы с полем lessons из исходной таблицы course
#         result = await db.execute(text("SELECT id, lessons FROM course"))
#         courses = result.mappings().all()
#         total_courses = len(courses)
#         logger.info("Найдено курсов: %d", total_courses)
#
#         for course in courses:
#             course_id = course["id"]
#             lessons_json = course.get("lessons")
#             if not lessons_json:
#                 logger.info(f"Курс id={course_id} не содержит данных в lessons")
#                 continue
#
#             try:
#                 lessons_data = json.loads(lessons_json)
#             except Exception as e:
#                 logger.error(f"Ошибка парсинга lessons для курса id={course_id}: {e}")
#                 continue
#
#             # lessons_data может быть либо dict, либо list
#             if isinstance(lessons_data, dict):
#                 sections_iterable = lessons_data.values()
#             elif isinstance(lessons_data, list):
#                 sections_iterable = lessons_data
#             else:
#                 logger.warning(f"Неожиданный тип lessons для курса id={course_id}: {type(lessons_data)}")
#                 continue
#
#             for sec in sections_iterable:
#                 if not isinstance(sec, dict):
#                     continue
#                 section_name = (sec.get("section_name") or "Default Section").strip()
#                 # Проверяем наличие секции в целевой таблице sections для данного курса
#                 check_query = text("""
#                     SELECT id FROM sections
#                     WHERE course_id = :course_id AND TRIM(name) = :section_name
#                 """)
#                 res = await db.execute(check_query, {"course_id": course_id, "section_name": section_name})
#                 existing_section = res.scalar()
#                 if not existing_section:
#                     # Если секция не найдена – вставляем новую запись
#                     insert_query = text("""
#                         INSERT INTO sections (course_id, name)
#                         VALUES (:course_id, :section_name)
#                     """)
#                     await db.execute(insert_query, {"course_id": course_id, "section_name": section_name})
#                     new_sections_added += 1
#                     logger.info(f"Добавлена новая секция '{section_name}' для курса id={course_id}")
#
#         await db.commit()
#         return JSONResponse({
#             "status": "Sections update completed",
#             "total_courses_processed": total_courses,
#             "new_sections_added": new_sections_added
#         })
#
#     except Exception as e:
#         await db.rollback()
#         logger.error(f"Ошибка обновления секций: {e}")
#         raise HTTPException(status_code=500, detail=str(e))
#
#
# @router.post("/update-landing-modules-short-video-link-from-mismatches")
# async def update_landing_modules_short_video_link_from_mismatches(db: AsyncSession = Depends(get_async_db)):
#     """
#     Обновляет поле short_video_link для модулей, используя ожидаемые ссылки из JSON‑поля lessons_info
#     лендингов. Для каждого лендинга (где course_id != 0) извлекается lessons_info из исходной таблицы landings
#     (через JOIN с таблицей landing), затем для каждого урока ищется соответствующий модуль (по совпадению TRIM(title)
#     с именем урока, принадлежащего секциям данного курса). Если значение short_video_link в модуле не соответствует
#     ожидаемому, выполняется обновление.
#
#     Возвращает JSON с количеством обновлённых модулей.
#     """
#     try:
#         updated_total = 0
#
#         # Извлекаем лендинги с course_id != 0, объединяя данные из таблицы landing и исходной таблицы landings
#         query = text("""
#             SELECT l.id AS landing_id, l.course_id, ls.lessons_info
#             FROM landing l
#             JOIN landings ls ON ls.id = l.id
#             WHERE l.course_id != 0;
#         """)
#         result = await db.execute(query)
#         records = result.mappings().all()
#         logger.info("Найдено лендингов для проверки: %d", len(records))
#
#         for record in records:
#             landing_id = record["landing_id"]
#             course_id = record["course_id"]
#             lessons_info = record.get("lessons_info") or "{}"
#             try:
#                 lessons_data = json.loads(lessons_info)
#             except Exception as e:
#                 logger.error(f"Ошибка парсинга lessons_info для лендинга id={landing_id}: {e}")
#                 continue
#
#             # lessons_data может быть словарём или списком
#             if isinstance(lessons_data, dict):
#                 lessons_iterable = lessons_data.values()
#             elif isinstance(lessons_data, list):
#                 lessons_iterable = lessons_data
#             else:
#                 logger.warning(f"Неожиданный тип lessons_info для лендинга id={landing_id}: {type(lessons_data)}")
#                 continue
#
#             for lesson in lessons_iterable:
#                 if not isinstance(lesson, dict):
#                     continue
#                 lesson_name = (lesson.get("lesson_name") or lesson.get("name") or "").strip()
#                 expected_link = (lesson.get("video_link") or lesson.get("link") or "").strip()
#                 if not lesson_name:
#                     logger.warning(f"Пустое название урока в лендинге id={landing_id}")
#                     continue
#                 if not expected_link:
#                     logger.warning(f"Пустая ссылка для урока '{lesson_name}' в лендинге id={landing_id}")
#                     continue
#
#                 # Обновляем соответствующий модуль:
#                 # Ищем модуль, принадлежащий секциям данного курса, где TRIM(title) совпадает с lesson_name
#                 update_query = text("""
#                     UPDATE modules
#                     SET short_video_link = :expected_link
#                     WHERE section_id IN (
#                         SELECT id FROM sections WHERE course_id = :course_id
#                     )
#                     AND TRIM(title) = :lesson_name
#                 """)
#                 res = await db.execute(update_query, {
#                     "expected_link": expected_link,
#                     "course_id": course_id,
#                     "lesson_name": lesson_name
#                 })
#                 if res.rowcount and res.rowcount > 0:
#                     logger.info(f"Обновлён модуль для урока '{lesson_name}' (landing id={landing_id})")
#                     updated_total += res.rowcount
#                 else:
#                     logger.warning(f"Модуль не найден для урока '{lesson_name}' (landing id={landing_id})")
#
#         await db.commit()
#         return JSONResponse({
#             "status": "Modules short_video_link updated from mismatches",
#             "updated_count": updated_total
#         })
#
#     except Exception as e:
#         await db.rollback()
#         logger.error(f"Ошибка обновления short_video_link: {e}")
#         raise HTTPException(status_code=500, detail=str(e))
#
# @router.post("/update-landing-modules-program-text")
# async def update_landing_modules_program_text(db: AsyncSession = Depends(get_async_db)):
#     """
#     Для каждого лендинга с ненулевым course_id:
#       - Извлекаем lessons_info (JSON) из исходной таблицы landings,
#       - Для каждого урока извлекаем значение поля "program"
#         и, если оно непустое, ищем в таблице modules модуль, принадлежащий к секциям
#         курса (по course_id) с совпадающим (TRIM) названием урока (поле title).
#       - Обновляем найденному модулю поле program_text.
#     Возвращает JSON с количеством обновлённых модулей.
#     """
#     try:
#         updated_total = 0
#
#         # Извлекаем лендинги с course_id != 0, объединяя данные из таблиц landing и landings
#         query = text("""
#             SELECT l.id AS landing_id, l.course_id, ls.lessons_info
#             FROM landing l
#             JOIN landings ls ON ls.id = l.id
#             WHERE l.course_id != 0;
#         """)
#         result = await db.execute(query)
#         records = result.mappings().all()
#         logger.info("Найдено лендингов для проверки: %d", len(records))
#
#         for record in records:
#             landing_id = record["landing_id"]
#             course_id = record["course_id"]
#             lessons_info = record.get("lessons_info") or "{}"
#             try:
#                 lessons_data = json.loads(lessons_info)
#             except Exception as e:
#                 logger.error(f"Ошибка парсинга lessons_info для лендинга id={landing_id}: {e}")
#                 continue
#
#             # lessons_data может быть dict или list – определяем итератор
#             if isinstance(lessons_data, dict):
#                 lessons_iter = lessons_data.values()
#             elif isinstance(lessons_data, list):
#                 lessons_iter = lessons_data
#             else:
#                 logger.warning(f"Неожиданный тип lessons_info для лендинга id={landing_id}: {type(lessons_data)}")
#                 continue
#
#             for lesson in lessons_iter:
#                 if not isinstance(lesson, dict):
#                     continue
#                 # Извлекаем название урока
#                 lesson_name = (lesson.get("lesson_name") or lesson.get("name") or "").strip()
#                 if not lesson_name:
#                     logger.warning(f"Пустое название урока в лендинге id={landing_id}")
#                     continue
#                 # Извлекаем значение program
#                 program_text = (lesson.get("program") or "").strip()
#                 if not program_text:
#                     logger.warning(f"Пустое значение program для урока '{lesson_name}' в лендинге id={landing_id}")
#                     continue
#
#                 # Обновляем модуль: ищем модуль в таблице modules, принадлежащий секциям с course_id = :course_id,
#                 # где TRIM(title) совпадает с lesson_name
#                 update_query = text("""
#                     UPDATE modules
#                     SET program_text = :program_text
#                     WHERE section_id IN (
#                         SELECT id FROM sections WHERE course_id = :course_id
#                     )
#                     AND TRIM(title) = :lesson_name
#                 """)
#                 res = await db.execute(update_query, {
#                     "program_text": program_text,
#                     "course_id": course_id,
#                     "lesson_name": lesson_name
#                 })
#                 if res.rowcount and res.rowcount > 0:
#                     logger.info(f"Обновлён модуль для урока '{lesson_name}' (landing id={landing_id})")
#                     updated_total += res.rowcount
#                 else:
#                     logger.warning(f"Модуль не найден для урока '{lesson_name}' (landing id={landing_id})")
#
#         await db.commit()
#         return JSONResponse({
#             "status": "Modules program_text updated from lessons_info",
#             "updated_count": updated_total
#         })
#
#     except Exception as e:
#         await db.rollback()
#         logger.error(f"Ошибка обновления program_text в модулях: {e}")
#         raise HTTPException(status_code=500, detail=str(e))
#
#
# logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)
#
#
# @router.post("/update-landing-modules-from-lessons-info")
# async def update_landing_modules_from_lessons_info(db: AsyncSession = Depends(get_async_db)):
#     """
#     Для каждого лендинга из таблицы landings:
#       - Извлекает JSON из поля lessons_info и поле linked_courses.
#       - Определяет course_id, взяв первый элемент JSON-массива linked_courses.
#       - Для каждого урока из lessons_info (JSON) извлекает название (ключ "lesson_name" или "name"), длительность (ключ "duration")
#         и программу (ключ "program").
#       - Обновляет в таблице modules (для модулей, принадлежащих секциям курса с найденным course_id) поля duration и program_text,
#         если TRIM(title) совпадает с названием урока.
#     Возвращает JSON с количеством обновлённых модулей.
#     """
#     try:
#         updated_total = 0
#         # Выбираем лендинги, у которых lessons_info не NULL, а также поле linked_courses для получения course_id
#         result = await db.execute(
#             text("SELECT id, lessons_info, linked_courses FROM landings WHERE lessons_info IS NOT NULL"))
#         landings = result.mappings().all()
#         logger.info("Найдено лендингов для обновления: %d", len(landings))
#
#         for landing in landings:
#             landing_id = landing["id"]
#             lessons_info = landing["lessons_info"]
#             linked_courses = landing.get("linked_courses", "[]")
#
#             # Определяем course_id из linked_courses
#             try:
#                 linked_list = json.loads(linked_courses)
#                 if isinstance(linked_list, list) and len(linked_list) > 0:
#                     course_id = linked_list[0]
#                 else:
#                     logger.warning(f"Лендинг id={landing_id} не содержит элементов в linked_courses")
#                     continue
#             except Exception as e:
#                 logger.error(f"Ошибка парсинга linked_courses для лендинга id={landing_id}: {e}")
#                 continue
#
#             # Если lessons_info приходит как строка, парсим JSON
#             if isinstance(lessons_info, str):
#                 try:
#                     lessons_data = json.loads(lessons_info)
#                 except Exception as e:
#                     logger.error(f"Ошибка парсинга lessons_info для лендинга id={landing_id}: {e}")
#                     continue
#             else:
#                 lessons_data = lessons_info
#
#             # Определяем итератор уроков: если словарь – берем значения, если список – просто итерируем по списку
#             if isinstance(lessons_data, dict):
#                 lessons_iter = lessons_data.values()
#             elif isinstance(lessons_data, list):
#                 lessons_iter = lessons_data
#             else:
#                 logger.warning(f"Неожиданный тип lessons_info для лендинга id={landing_id}: {type(lessons_data)}")
#                 continue
#
#             for lesson in lessons_iter:
#                 if not isinstance(lesson, dict):
#                     continue
#                 lesson_name = (lesson.get("lesson_name") or lesson.get("name") or "").strip()
#                 if not lesson_name:
#                     logger.warning(f"Пустое название урока в лендинге id={landing_id}")
#                     continue
#
#                 duration = lesson.get("duration", "").strip()
#                 program_text = lesson.get("program", "").strip()
#
#                 # Обновляем модуль: выбираем модуль по совпадению названия (после TRIM)
#                 update_query = text("""
#                     UPDATE modules
#                     SET duration = :duration, program_text = :program_text
#                     WHERE section_id IN (
#                         SELECT id FROM sections WHERE course_id = :course_id
#                     )
#                     AND TRIM(title) = :lesson_name
#                 """)
#                 res = await db.execute(update_query, {
#                     "duration": duration,
#                     "program_text": program_text,
#                     "course_id": course_id,
#                     "lesson_name": lesson_name
#                 })
#                 rowcount = res.rowcount if res.rowcount is not None else 0
#                 if rowcount == 0:
#                     logger.warning(f"Модуль не найден для урока '{lesson_name}' в лендинге id={landing_id}")
#                 else:
#                     logger.info(f"Обновлён модуль для урока '{lesson_name}' в лендинге id={landing_id}")
#                 updated_total += rowcount
#
#         await db.commit()
#         return JSONResponse({
#             "status": "Modules duration and program_text updated",
#             "updated_count": updated_total
#         })
#     except Exception as e:
#         await db.rollback()
#         logger.error(f"Ошибка обновления модулей: {e}")
#         raise HTTPException(status_code=500, detail=str(e))