# import json
# import logging
# from bs4 import BeautifulSoup
# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy import text
# from sqlalchemy.ext.asyncio import AsyncSession
#
# # Импорт асинхронного получения сессии из вашего модуля подключения
# from ..db.database import get_async_db
#
# router = APIRouter()
# logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)
#
#
# def clean_html(html_content: str) -> str:
#     """
#     Удаляет HTML-теги из строки, оставляя только текст.
#     """
#     if not html_content:
#         return ""
#     soup = BeautifulSoup(html_content, "lxml")
#     return soup.get_text(separator=' ', strip=True)
#
#
# def recursive_clean(obj):
#     """
#     Рекурсивно обходит объект (dict, list или строку) и для всех строк удаляет HTML-теги.
#     Структура (dict/list) остаётся неизменной.
#     """
#     if isinstance(obj, dict):
#         return {k: recursive_clean(v) for k, v in obj.items()}
#     elif isinstance(obj, list):
#         return [recursive_clean(item) for item in obj]
#     elif isinstance(obj, str):
#         return clean_html(obj)
#     else:
#         return obj
#
#
# @router.post("/clean-landings-sql", summary="Очистка таблицы landings от HTML-тегов (SQL)")
# async def clean_landings_sql(db: AsyncSession = Depends(get_async_db)):
#     """
#     Проходит по всем записям в таблице landings и:
#       - Очищает текстовое поле course_program от HTML-тегов.
#       - Рекурсивно очищает JSON-поля lessons_info и lecturers_info от HTML-тегов.
#     Если данные изменяются, обновляет запись с помощью прямых SQL-запросов.
#     Возвращает количество обновлённых записей.
#     """
#     try:
#         # Получаем все записи из таблицы landings
#         select_query = text("""
#             SELECT id, course_program, lessons_info, lecturers_info, linked_courses, preview_photo
#             FROM landings
#         """)
#         result = await db.execute(select_query)
#         rows = result.mappings().all()
#         logger.info("Найдено %d записей в таблице landings", len(rows))
#         updated_count = 0
#
#         # Обходим каждую запись
#         for row in rows:
#             record_id = row["id"]
#
#             # Очищаем course_program
#             original_program = row.get("course_program") or ""
#             cleaned_program = clean_html(original_program)
#
#             # Обработка lessons_info (JSON)
#             original_lessons = row.get("lessons_info")
#             cleaned_lessons = original_lessons
#             if original_lessons:
#                 try:
#                     # Если значение строковое – пытаемся распарсить JSON
#                     if isinstance(original_lessons, str):
#                         lessons_obj = json.loads(original_lessons)
#                     else:
#                         lessons_obj = original_lessons
#                     cleaned_lessons_obj = recursive_clean(lessons_obj)
#                     cleaned_lessons = json.dumps(cleaned_lessons_obj, ensure_ascii=False)
#                 except Exception as e:
#                     logger.error("Ошибка очистки lessons_info для id=%s: %s", record_id, e)
#                     # Если парсинг не удался – оставляем оригинал
#                     cleaned_lessons = original_lessons
#
#             # Обработка lecturers_info (JSON)
#             original_lecturers = row.get("lecturers_info")
#             cleaned_lecturers = original_lecturers
#             if original_lecturers:
#                 try:
#                     if isinstance(original_lecturers, str):
#                         lecturers_obj = json.loads(original_lecturers)
#                     else:
#                         lecturers_obj = original_lecturers
#                     cleaned_lecturers_obj = recursive_clean(lecturers_obj)
#                     cleaned_lecturers = json.dumps(cleaned_lecturers_obj, ensure_ascii=False)
#                 except Exception as e:
#                     logger.error("Ошибка очистки lecturers_info для id=%s: %s", record_id, e)
#                     cleaned_lecturers = original_lecturers
#
#             # Сравниваем: если хотя бы одно поле изменилось, то обновляем запись
#             if (cleaned_program != original_program or
#                     (original_lessons and cleaned_lessons != original_lessons) or
#                     (original_lecturers and cleaned_lecturers != original_lecturers)):
#                 update_query = text("""
#                     UPDATE landings
#                     SET course_program = :course_program,
#                         lessons_info = :lessons_info,
#                         lecturers_info = :lecturers_info
#                     WHERE id = :id
#                 """)
#                 params = {
#                     "course_program": cleaned_program,
#                     "lessons_info": cleaned_lessons,
#                     "lecturers_info": cleaned_lecturers,
#                     "id": record_id
#                 }
#                 await db.execute(update_query, params)
#                 updated_count += 1
#
#         await db.commit()
#         logger.info("Обновлено %d записей", updated_count)
#         return {"message": f"Обновлено {updated_count} записей."}
#     except Exception as e:
#         logger.error("Ошибка при очистке таблицы landings: %s", e)
#         raise HTTPException(status_code=500, detail=str(e))
