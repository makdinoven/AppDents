import json

from bs4 import BeautifulSoup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


def clean_html(raw_html: str) -> str:
    if not raw_html:
        return raw_html
    soup = BeautifulSoup(raw_html, "html.parser")
    # Используем "\n" в качестве разделителя, чтобы сохранить переводы строк
    return soup.get_text(separator="\n", strip=True)



def clean_json_data(data):
    """
    Рекурсивно проходит по JSON-данным и очищает все строки от HTML-тегов.
    """
    if isinstance(data, dict):
        return {key: clean_json_data(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [clean_json_data(item) for item in data]
    elif isinstance(data, str):
        return clean_html(data)
    else:
        return data


async def clean_landings_old_data(db: AsyncSession) -> dict:
    """
    Очищает следующие поля в таблице landings_old:
      - course_program (прямой HTML),
      - lessons_info (JSON: рекурсивно очищаем все строки),
      - lecturers_info (JSON: рекурсивно очищаем все строки).

    Реализация производится через прямые SQL-запросы.
    """
    result = await db.execute(
        text("SELECT id, course_program, lessons_info, lecturers_info FROM landings_old")
    )
    rows = result.fetchall()
    updated_count = 0

    for row in rows:
        record_id = row[0]
        course_program = row[1]
        lessons_info = row[2]
        lecturers_info = row[3]

        updated = False

        # Очистка course_program
        new_course_program = course_program
        if course_program:
            cleaned_course_program = clean_html(course_program)
            if cleaned_course_program != course_program:
                new_course_program = cleaned_course_program
                updated = True

        # Очистка lessons_info (JSON)
        new_lessons_info = lessons_info
        if lessons_info:
            # Если данные не в виде словаря, пробуем их загрузить
            if not isinstance(lessons_info, dict):
                try:
                    lessons_info = json.loads(lessons_info)
                except Exception:
                    lessons_info = {}
            cleaned_lessons_info = clean_json_data(lessons_info)
            if cleaned_lessons_info != lessons_info:
                new_lessons_info = cleaned_lessons_info
                updated = True

        # Очистка lecturers_info (JSON)
        new_lecturers_info = lecturers_info
        if lecturers_info:
            if not isinstance(lecturers_info, dict):
                try:
                    lecturers_info = json.loads(lecturers_info)
                except Exception:
                    lecturers_info = {}
            cleaned_lecturers_info = clean_json_data(lecturers_info)
            if cleaned_lecturers_info != lecturers_info:
                new_lecturers_info = cleaned_lecturers_info
                updated = True

        # Если хоть одно поле изменилось, выполняем UPDATE-запрос
        if updated:
            await db.execute(
                text("""
                    UPDATE landings_old
                    SET course_program = :course_program,
                        lessons_info = :lessons_info,
                        lecturers_info = :lecturers_info
                    WHERE id = :id
                """),
                {
                    "course_program": new_course_program,
                    # Преобразуем JSON обратно в строку для сохранения (если данные представлены как dict)
                    "lessons_info": json.dumps(new_lessons_info) if isinstance(new_lessons_info,
                                                                               dict) else new_lessons_info,
                    "lecturers_info": json.dumps(new_lecturers_info) if isinstance(new_lecturers_info,
                                                                                   dict) else new_lecturers_info,
                    "id": record_id
                }
            )
            updated_count += 1

    await db.commit()
    return {"status": "success", "updated_records": updated_count}