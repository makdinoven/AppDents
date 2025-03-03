import json
from bs4 import BeautifulSoup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

def clean_html(raw_html: str) -> str:
    """
    Удаляет HTML-теги из строки, сохраняя переводы строк.
    """
    if not raw_html:
        return raw_html
    soup = BeautifulSoup(raw_html, "html.parser")
    return soup.get_text(separator="\n", strip=True)

def clean_json_data(data):
    """
    Рекурсивно проходит по JSON-данным и очищает все строковые значения от HTML-тегов.
    """
    if isinstance(data, dict):
        return {k: clean_json_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_json_data(item) for item in data]
    elif isinstance(data, str):
        return clean_html(data)
    else:
        return data

async def migrate_landings(db: AsyncSession) -> int:
    """
    Мигрирует данные из таблицы landings_old в новую таблицу landings.
    Обрабатываются следующие поля:
      - id, page_name, course_name → landing_name, old_price, new_price,
        course_program (очищается от HTML),
      - lessons_info (рекурсивная очистка JSON),
      - linked_courses (разбивается для заполнения landing_course),
      - preview_photo – копируется без изменений,
      - lecturers_info – для каждого лектора создаётся запись в authors и связь в landing_authors.
    """
    result = await db.execute(text("""
        SELECT id, page_name, course_name, old_price, new_price, course_program, lessons_info, linked_courses, preview_photo, lecturers_info
        FROM landings_old
    """))
    rows = result.fetchall()
    landing_count = 0

    for row in rows:
        old_id = row[0]
        page_name = row[1]
        course_name = row[2]
        old_price = row[3]
        new_price = row[4]
        course_program = row[5]
        lessons_info = row[6]
        linked_courses = row[7]
        preview_photo = row[8]
        lecturers_info = row[9]

        # Очистка course_program
        cleaned_course_program = clean_html(course_program) if course_program else course_program

        # Обработка lessons_info (ожидается, что это словарь; если строка — парсим)
        if lessons_info:
            try:
                lessons_obj = lessons_info if isinstance(lessons_info, dict) else json.loads(lessons_info)
            except Exception:
                lessons_obj = {}
            lessons_obj = clean_json_data(lessons_obj)
            lessons_cleaned = json.dumps(lessons_obj, ensure_ascii=False)
        else:
            lessons_cleaned = None

        # Обработка linked_courses (ожидается JSON-массив идентификаторов)
        if linked_courses:
            try:
                linked_courses_obj = linked_courses if isinstance(linked_courses, list) else json.loads(linked_courses)
            except Exception:
                linked_courses_obj = []
        else:
            linked_courses_obj = []

        # Вставляем данные в новую таблицу landings.
        await db.execute(text("""
            INSERT INTO landings (id, page_name, landing_name, old_price, new_price, course_program, lessons_info, linked_courses, preview_photo)
            VALUES (:id, :page_name, :landing_name, :old_price, :new_price, :course_program, :lessons_info, NULL, :preview_photo)
        """), {
            "id": old_id,
            "page_name": page_name,
            "landing_name": course_name,
            "old_price": old_price,
            "new_price": new_price,
            "course_program": cleaned_course_program,
            "lessons_info": lessons_cleaned,
            "preview_photo": preview_photo
        })
        landing_count += 1

        # Обработка связей с курсами (таблица landing_course)
        for course_id in linked_courses_obj:
            await db.execute(text("""
                INSERT INTO landing_course (landing_id, course_id)
                VALUES (:landing_id, :course_id)
            """), {"landing_id": old_id, "course_id": course_id})

        # Обработка lecturers_info
        if lecturers_info:
            # Если lecturers_info является строкой, пытаемся его разобрать
            if isinstance(lecturers_info, str):
                try:
                    lecturers_info = json.loads(lecturers_info)
                except Exception:
                    lecturers_info = {}
            # Если lecturers_info является списком, преобразуем его в словарь с индексами в качестве ключей
            if isinstance(lecturers_info, list):
                lecturers_info = {str(i): lect for i, lect in enumerate(lecturers_info)}
            # Если после преобразований lecturers_info не словарь, делаем его пустым
            if not isinstance(lecturers_info, dict):
                lecturers_info = {}

            for key, lecturer in lecturers_info.items():
                lecturer_name = lecturer.get("name")
                lecturer_description = lecturer.get("description")
                if not lecturer_name:
                    continue
                cleaned_name = lecturer_name.strip()
                cleaned_description = clean_html(lecturer_description) if lecturer_description else None

                # Проверяем, существует ли автор с таким именем
                res = await db.execute(text("""
                    SELECT id FROM authors WHERE name = :name
                """), {"name": cleaned_name})
                author_row = res.fetchone()
                if author_row:
                    author_id = author_row[0]
                else:
                    # Вставляем нового автора
                    await db.execute(text("""
                        INSERT INTO authors (name, description)
                        VALUES (:name, :description)
                    """), {"name": cleaned_name, "description": cleaned_description})
                    res = await db.execute(text("""
                        SELECT id FROM authors WHERE name = :name
                    """), {"name": cleaned_name})
                    author_row = res.fetchone()
                    author_id = author_row[0]

                # Вставляем связь лендинг-автор
                await db.execute(text("""
                    INSERT INTO landing_authors (landing_id, author_id)
                    VALUES (:landing_id, :author_id)
                """), {"landing_id": old_id, "author_id": author_id})
    await db.commit()
    return landing_count

async def migrate_courses(db: AsyncSession) -> int:
    """
    Мигрирует данные из таблицы courses_old в новую таблицу courses (все поля, включая id).
    """
    result = await db.execute(text("""
        SELECT id, name, description, lessons FROM course_old
    """))
    rows = result.fetchall()
    course_count = 0
    for row in rows:
        id_val, name, description, lessons = row
        await db.execute(text("""
            INSERT INTO courses (id, name, description, lessons)
            VALUES (:id, :name, :description, :lessons)
        """), {
            "id": id_val,
            "name": name,
            "description": description,
            "lessons": lessons
        })
        course_count += 1
    await db.commit()
    return course_count

async def migrate_users(db: AsyncSession) -> int:
    """
    Мигрирует данные из таблицы users_old в новую таблицу users.
    – Переносит: id, email, pass, role.
    – JSON-поле course разбивается, и для каждого найденного course создаётся запись в ассоциативной таблице users_courses.
    """
    result = await db.execute(text("""
        SELECT id, email, pass, role, course FROM users_old
    """))
    rows = result.fetchall()
    user_count = 0
    for row in rows:
        id_val, email, password, role, course_json = row
        await db.execute(text("""
            INSERT INTO users (id, email, password, role)
            VALUES (:id, :email, :password, :role)
        """), {
            "id": id_val,
            "email": email,
            "password": password,
            "role": role
        })
        user_count += 1

        # Обработка связей пользователя с курсами
        if course_json:
            try:
                course_ids = course_json if isinstance(course_json, list) else json.loads(course_json)
            except Exception:
                course_ids = []
            if isinstance(course_ids, list):
                for course_id in course_ids:
                    if course_id is None:
                        continue  # Пропускаем пустые значения
                    # Проверяем, существует ли курс с таким id в таблице courses
                    res = await db.execute(text("SELECT id FROM courses WHERE id = :id"), {"id": course_id})
                    if not res.fetchone():
                        # Если курс с таким id не найден, пропускаем вставку
                        continue
                    await db.execute(text("""
                        INSERT INTO users_courses (user_id, course_id)
                        VALUES (:user_id, :course_id)
                    """), {"user_id": id_val, "course_id": course_id})
    await db.commit()
    return user_count

async def run_migration(db: AsyncSession) -> dict:
    """
    Запускает миграцию для всех трёх таблиц:
      – landings_old → landings (+ landing_course, landing_authors),
      – courses_old → courses,
      – users_old → users (+ users_courses).
    Возвращает сводный отчёт по количеству перенесённых записей.
    """
    landings_migrated = await migrate_landings(db)
    courses_migrated = await migrate_courses(db)
    users_migrated = await migrate_users(db)
    return {
        "landings_migrated": landings_migrated,
        "courses_migrated": courses_migrated,
        "users_migrated": users_migrated
    }
