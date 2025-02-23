import re
import json
import csv
import io
import logging
import asyncio
from bs4 import BeautifulSoup
from rapidfuzz import fuzz
from sqlalchemy.future import select
from sqlalchemy import or_, text
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.models import Landing, Course, Section, Module, Author, LanguageEnum

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

FUZZY_THRESHOLD = 80

def normalize_text(text: str) -> str:
    """Приводит текст к нижнему регистру и удаляет все символы, кроме латинских букв и цифр."""
    return re.sub(r'[^a-z0-9]', '', text.lower())

def strip_html(html: str) -> str:
    """Удаляет HTML-теги с помощью BeautifulSoup."""
    soup = BeautifulSoup(html, "lxml")
    return soup.get_text(separator=' ', strip=True)

def find_lessons_recursively(obj) -> list:
    """
    Рекурсивно обходит объект (dict или list) и возвращает список всех объектов,
    содержащих одновременно ключи "lesson_name" (или "name") и "video_link".
    """
    lessons = []
    if isinstance(obj, dict):
        if (("lesson_name" in obj) or ("name" in obj)) and ("video_link" in obj):
            lessons.append(obj)
        for value in obj.values():
            lessons.extend(find_lessons_recursively(value))
    elif isinstance(obj, list):
        for item in obj:
            lessons.extend(find_lessons_recursively(item))
    return lessons

def extract_lessons_from_json(json_str: str) -> list:
    """
    Извлекает все уроки из строки JSON с использованием рекурсивного обхода.
    """
    try:
        data = json.loads(json_str)
    except Exception as e:
        logger.error("Ошибка парсинга JSON: %s", e)
        return []
    return find_lessons_recursively(data)

def csv_reader(record: str) -> list:
    """
    Вспомогательная функция для разбора строки, содержащей значения из SQL дампа.
    Использует csv.reader с newline='' для корректной обработки.
    """
    record = record.strip()
    if record.startswith('(') and record.endswith(')'):
        record = record[1:-1]
    sio = io.StringIO(record, newline='')
    reader = csv.reader(sio, delimiter=',', quotechar="'")
    return next(reader)


def extract_landings_from_dump(content: str) -> list:
    """
    Извлекает данные лендингов из дампа landing.sql.
    Дамп содержит многострочные INSERT-запросы.

    Алгоритм:
      1. Разбить весь файл на строки.
      2. Собрать все строки, относящиеся к одному INSERT-запросу (начинаются с "INSERT INTO" и заканчиваются на ";").
      3. Для каждого запроса извлечь часть после VALUES (все содержимое между первой открывающей и последней закрывающей скобкой).
      4. Разбить полученную строку на отдельные записи по разделителю "),(" (учитывая, что внутренняя структура может содержать переносы строк).
      5. Для каждой записи с помощью csv.reader разобрать поля (ожидается, что их 10).

    Ожидаемый порядок полей:
      id, page_name, course_name, old_price, new_price, course_program, lessons_info, lecturers_info, linked_courses, preview_photo
    Возвращает список словарей.
    """
    landings = []
    lines = content.splitlines()
    queries = []
    current_query = []
    in_query = False

    for line in lines:
        if line.strip().upper().startswith("INSERT INTO"):
            # Если уже собирали предыдущий запрос, сохраняем его
            if in_query and current_query:
                queries.append("\n".join(current_query))
                current_query = []
            in_query = True
        if in_query:
            current_query.append(line)
            if line.strip().endswith(";"):
                queries.append("\n".join(current_query))
                current_query = []
                in_query = False

    if current_query:
        queries.append("\n".join(current_query))

    logger.debug("Найдено %d INSERT запросов для лендингов.", len(queries))

    # Обрабатываем каждый INSERT-запрос
    for query in queries:
        # Ищем часть после VALUES до завершающей точки с запятой
        m = re.search(r"VALUES\s*(\(.*\));", query, re.DOTALL | re.IGNORECASE)
        if not m:
            logger.error("Не удалось найти VALUES в запросе: %s", query[:100])
            continue
        values_str = m.group(1).strip()
        # Убираем начальную и конечную скобки, чтобы получить строки, разделённые "),("
        if values_str.startswith("(") and values_str.endswith(")"):
            values_str = values_str[1:-1]
        # Разбиваем по шаблону "),(" с учётом пробелов и переносов строк
        rows = re.split(r"\),\s*\(", values_str)
        for row in rows:
            try:
                sio = io.StringIO(row, newline='')
                fields = next(csv.reader(sio, delimiter=',', quotechar="'", skipinitialspace=True))
                if len(fields) < 10:
                    logger.warning("Найдены не все поля: %s", fields)
                    continue
                landing_id = int(fields[0].strip())
                page_name = fields[1].strip()
                course_name = fields[2].strip()
                old_price_str = fields[3].strip().strip("'")
                new_price_str = fields[4].strip().strip("'")
                try:
                    old_price = float(old_price_str) if old_price_str else None
                except Exception:
                    old_price = None
                try:
                    new_price = float(new_price_str) if new_price_str else None
                except Exception:
                    new_price = None
                course_program = fields[5].strip()
                lessons_info = fields[6].strip()
                lecturers_info = fields[7].strip()
                linked_courses = fields[8].strip()
                preview_photo = fields[9].strip()
                landing = {
                    "id": landing_id,
                    "slug": page_name,
                    "course_name": course_name,
                    "old_price": old_price,
                    "new_price": new_price,
                    "main_text": course_program,  # дальнейшая очистка будет происходить позже
                    "lessons_info": lessons_info,
                    "lecturers_info": lecturers_info,
                    "linked_courses": linked_courses,
                    "preview_photo": preview_photo,
                    "language": "EN"
                }
                landings.append(landing)
            except Exception as e:
                logger.error("Ошибка при разборе строки лендинга: %s", e)
    logger.debug("Извлечено лендингов: %d", len(landings))
    return landings

def extract_courses_from_dump(content: str) -> list:
    """
    Извлекает данные курсов из дампа course.sql.
    Порядок полей:
      id, name, description, lessons (JSON)
    Возвращает список курсов, где каждый курс – словарь с ключами:
      id, name, description, sections (список секций, каждая секция содержит section_name и modules)
    """
    courses = []
    record_pattern = re.compile(
        r"INSERT INTO\s+`course`\s+\(.*?\)\s+VALUES\s*\((.*?)\);", re.DOTALL)
    matches = record_pattern.findall(content)
    logger.debug("Найдено %d записей для курсов.", len(matches))
    for record in matches:
        record = record.strip()
        if record.startswith('(') and record.endswith(')'):
            record = record[1:-1]
        try:
            fields = list(csv.reader([record], delimiter=',', quotechar="'", skipinitialspace=True))[0]
        except Exception as e:
            logger.error("Ошибка чтения CSV строки курса: %s", e)
            continue
        if len(fields) < 4:
            continue
        try:
            course_id = int(fields[0].strip())
            name = fields[1].strip()
            description = fields[2].strip()
            lessons_json = fields[3].strip()
        except Exception as e:
            logger.error("Ошибка при разборе записи курса: %s", e)
            continue
        try:
            lessons_data = json.loads(lessons_json)
        except Exception as e:
            logger.error("Ошибка парсинга JSON для курса '%s': %s", name, e)
            continue
        sections = []
        if isinstance(lessons_data, dict):
            for key, sec in lessons_data.items():
                section_name = sec.get("section_name", "Default Section")
                lessons_arr = sec.get("lessons", [])
                modules = []
                for lesson in lessons_arr:
                    title = lesson.get("lesson_name")
                    link = lesson.get("video_link")
                    duration = lesson.get("duration", "")
                    program = lesson.get("program", "")
                    modules.append({
                        "title": title,
                        "full_video_link": link,  # Для курсов видео ссылка записывается в full_video_link
                        "duration": duration,
                        "program_text": strip_html(program)
                    })
                sections.append({
                    "section_name": section_name,
                    "modules": modules
                })
        course = {
            "id": course_id,
            "name": name,
            "description": description,
            "sections": sections
        }
        courses.append(course)
    logger.debug("Извлечено курсов: %d", len(courses))
    return courses

async def process_landing_dump(file_content: str, db: AsyncSession) -> dict:
    """
    Обрабатывает дамп landing.sql:
      - Извлекает лендинги и создает объекты Landing.
      - Из lessons_info извлекает уроки и создает объекты Module, привязанные к дефолтной секции.
        Для лендингов видео ссылка записывается в short_video_link.
      - Из lecturers_info извлекает авторов и связывает их с лендингом.
    Возвращает статистику по созданным лендингам, модулям и авторам.
    """
    landing_dicts = extract_landings_from_dump(file_content)
    created_landings = 0
    created_modules = 0
    created_authors = 0
    for ld in landing_dicts:
        landing_obj = Landing(
            id=ld["id"],
            title=ld["course_name"],
            slug=ld["slug"],
            old_price=ld["old_price"],
            price=ld["new_price"],
            main_text=strip_html(ld["main_text"]),
            main_image=ld["preview_photo"],  # Используем значение из preview_photo напрямую
            language="EN",
            course_id=0  # Связь с Course установится позже через fuzzy matching
        )
        db.add(landing_obj)
        created_landings += 1

        if ld["lessons_info"]:
            lessons = extract_lessons_from_json(ld["lessons_info"])
            if lessons:
                # Создаем дефолтную секцию для лендинга (логика может быть изменена по необходимости)
                default_section = Section(name="Default Section", course_id=0)
                db.add(default_section)
                await db.flush()
                for lesson in lessons:
                    module_obj = Module(
                        title=lesson.get("name") or lesson.get("lesson_name"),
                        short_video_link=lesson.get("link"),  # Для лендингов ссылка в short_video_link
                        full_video_link=None,
                        duration=lesson.get("duration", ""),
                        program_text=strip_html(lesson.get("program", "")),
                        section_id=default_section.id
                    )
                    db.add(module_obj)
                    created_modules += 1

        if ld["lecturers_info"]:
            try:
                lecturers_data = json.loads(ld["lecturers_info"])
                for key, lecturer in lecturers_data.items():
                    author_obj = Author(
                        name=lecturer.get("name"),
                        description=strip_html(lecturer.get("description", "")),
                        photo=""
                    )
                    db.add(author_obj)
                    await db.flush()
                    landing_obj.authors.append(author_obj)
                    created_authors += 1
            except Exception as e:
                logger.error("Ошибка парсинга lecturers_info для лендинга id=%s: %s", ld["id"], e)
    await db.commit()
    stats = {
        "created_landings": created_landings,
        "created_modules": created_modules,
        "created_authors": created_authors
    }
    logger.debug("Обработка лендингов завершена. Статистика: %s", stats)
    return stats

async def process_course_dump(file_content: str, db: AsyncSession) -> dict:
    """
    Обрабатывает дамп course.sql:
      - Извлекает данные курса и создает объект Course.
      - Из поля lessons (JSON) извлекает секции и создает объекты Section.
      - Для каждой секции создаются объекты Module, где видео ссылка записывается в full_video_link.
    Возвращает статистику по созданным курсам, секциям и модулям.
    """
    course_dicts = extract_courses_from_dump(file_content)
    created_courses = 0
    created_sections = 0
    created_modules = 0
    for cd in course_dicts:
        course_obj = Course(
            id=cd["id"],
            name=cd["name"],
            description=cd["description"]
        )
        db.add(course_obj)
        created_courses += 1
        for sec in cd["sections"]:
            section_obj = Section(
                name=sec["section_name"],
                course=course_obj
            )
            db.add(section_obj)
            created_sections += 1
            for mod in sec["modules"]:
                module_obj = Module(
                    title=mod["title"],
                    full_video_link=mod["full_video_link"],  # Для курсов видео ссылка в full_video_link
                    short_video_link=None,
                    duration=mod["duration"],
                    program_text=mod["program_text"],
                    section=section_obj
                )
                db.add(module_obj)
                created_modules += 1
    await db.commit()
    stats = {
        "created_courses": created_courses,
        "created_sections": created_sections,
        "created_modules": created_modules
    }
    logger.debug("Обработка курсов завершена. Статистика: %s", stats)
    return stats

async def link_landings_to_courses(db: AsyncSession) -> dict:
    """
    Выполняет fuzzy matching между landing.title и Course.name
    (с использованием fuzz.token_sort_ratio после нормализации) и обновляет поле course_id в Landing.
    Возвращает статистику по количеству обновленных лендингов.
    """
    updated = 0
    result = await db.execute(select(Landing))
    landings = result.scalars().all()
    result = await db.execute(select(Course))
    courses = result.scalars().all()

    for landing in landings:
        # Используем landing.title, так как при импорте туда записали название курса
        normalized_landing = normalize_text(landing.title)
        best_match = None
        best_score = 0
        for course in courses:
            score = fuzz.token_sort_ratio(normalized_landing, normalize_text(course.name))
            if score > best_score:
                best_score = score
                best_match = course
        if best_match and best_score >= FUZZY_THRESHOLD:
            landing.course_id = best_match.id
            updated += 1
            logger.info("Связано: Landing '%s' -> Course '%s' (score=%d)",
                        landing.title, best_match.name, best_score)
    await db.commit()
    return {"updated_landings": updated}

async def process_all_dumps(landing_content: str, course_content: str, db: AsyncSession) -> dict:
    # Отключаем проверки внешних ключей для лендингов
    await db.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
    landing_stats = await process_landing_dump(landing_content, db)
    course_stats = await process_course_dump(course_content, db)
    link_stats = await link_landings_to_courses(db)
    # Включаем проверки внешних ключей
    await db.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
    return {
        "landing_stats": landing_stats,
        "course_stats": course_stats,
        "link_stats": link_stats
    }
