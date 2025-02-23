import html
import re
import json
import csv
import io
import logging
from bs4 import BeautifulSoup
from ..services.dis_parser_service import extract_landings_from_dump, extract_courses_from_dump

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

import re
import json
import csv
import io
import logging
import html
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def strip_html(html_content: str) -> str:
    """Удаляет HTML-теги с помощью BeautifulSoup."""
    if not html_content:
        return ""
    soup = BeautifulSoup(html_content, "lxml")
    return soup.get_text(separator=' ', strip=True)


def clean_text(text: str) -> str:
    """
    Очищает текст от HTML-тегов, стилей и лишних пробелов.
    Применяет html.unescape, затем удаляет теги и нормализует пробелы.
    (Обратите внимание – последовательности обратных слэшей остаются без изменений.)
    """
    if not text:
        return ""
    text = html.unescape(text)
    cleaned = strip_html(text)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def extract_landings_from_dump_with_errors(content: str) -> dict:
    """
    Извлекает данные лендингов из дампа landing.sql.
    Дамп содержит многострочные INSERT-запросы.

    Алгоритм:
      1. Разбить файл на строки и собрать по INSERT-запросу (от "INSERT INTO" до ";" ).
      2. Для каждого запроса найти часть после VALUES (все содержимое между первой открывающей и последней закрывающей скобкой).
      3. Разбить эту строку на отдельные записи по разделителю "),(" (учитывая переносы строк).
      4. Для каждой записи разобрать поля через csv.reader.

    Ожидаемый порядок полей:
      id, page_name, course_name, old_price, new_price, course_program, lessons_info, lecturers_info, linked_courses, preview_photo

    Возвращает словарь с ключами:
      "landings": список словарей,
      "errors": список сообщений об ошибках.
    """
    landings = []
    errors = []
    lines = content.splitlines()
    queries = []
    current_query = []
    in_query = False

    for line in lines:
        if line.strip().upper().startswith("INSERT INTO"):
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

    for query in queries:
        m = re.search(r"VALUES\s*(\(.*\));", query, re.DOTALL | re.IGNORECASE)
        if not m:
            err = f"Не удалось найти VALUES в запросе: {query[:100]}"
            logger.error(err)
            errors.append(err)
            continue
        values_str = m.group(1).strip()
        if values_str.startswith("(") and values_str.endswith(")"):
            values_str = values_str[1:-1]
        # Разбиваем по шаблону "),(" с учетом переносов строк
        rows = re.split(r"\),\s*\(", values_str)
        logger.debug("Найдено %d записей в одном запросе.", len(rows))
        for row in rows:
            try:
                sio = io.StringIO(row, newline='')
                fields = next(csv.reader(sio, delimiter=',', quotechar="'", skipinitialspace=True))
                if len(fields) < 10:
                    err = f"Найдены не все поля: {fields}"
                    logger.warning(err)
                    errors.append(err)
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
                    "main_text": course_program,  # дальнейшая очистка производится ниже
                    "lessons_info": lessons_info,
                    "lecturers_info": lecturers_info,
                    "linked_courses": linked_courses,
                    "preview_photo": preview_photo,
                    "language": "EN"
                }
                landings.append(landing)
            except Exception as e:
                err = f"Ошибка при разборе строки лендинга: {e}"
                logger.error(err)
                errors.append(err)
    logger.debug("Всего извлечено лендингов: %d", len(landings))
    return {"landings": landings, "errors": errors}


def clean_landing_dump(content: str) -> dict:
    """
    Извлекает данные лендингов, очищает текстовые поля и внутренние поля JSON в lessons_info.
    Возвращает словарь с ключами:
      "landings": список очищённых лендингов,
      "errors": список ошибок, возникших при извлечении/очистке.
    """
    result = extract_landings_from_dump(content)
    cleaned_landings = []
    errors = []

    for i, landing in enumerate(result):
        if not isinstance(landing, dict):
            err = f"Запись с индексом {i} не является словарём: {landing}"
            logger.error(err)
            errors.append(err)
            continue

        try:
            landing["course_name"] = clean_text(landing.get("course_name", ""))
        except Exception as e:
            errors.append(f"Ошибка очистки course_name для записи с id={landing.get('id', 'неизвестно')}: {e}")
            continue

        try:
            landing["main_text"] = clean_text(landing.get("main_text", ""))
        except Exception as e:
            errors.append(f"Ошибка очистки main_text для записи с id={landing.get('id', 'неизвестно')}: {e}")
            continue

        try:
            landing["slug"] = clean_text(landing.get("slug", ""))
        except Exception as e:
            errors.append(f"Ошибка очистки slug для записи с id={landing.get('id', 'неизвестно')}: {e}")
            continue

        # Обработка lessons_info
        lessons_info = landing.get("lessons_info", "")
        if lessons_info:
            lessons_obj = None
            try:
                lessons_obj = json.loads(lessons_info)
            except Exception as e:
                # Если ошибка связана с одинарными кавычками, попробуем заменить их на двойные
                if "Expecting property name enclosed in double quotes" in str(e):
                    try:
                        fixed = lessons_info.replace("'", '"')
                        lessons_obj = json.loads(fixed)
                        logger.info("Использовано исправление одинарных кавычек для лендинга id=%s", landing.get("id"))
                    except Exception as e2:
                        err = (f"Ошибка парсинга/очистки lessons_info для лендинга id={landing.get('id', 'неизвестно')}: {e}; "
                               f"попытка исправления: {e2}")
                        logger.error(err)
                        errors.append(err)
                else:
                    err = f"Ошибка парсинга lessons_info для лендинга id={landing.get('id', 'неизвестно')}: {e}"
                    logger.error(err)
                    errors.append(err)
            # Если удалось распарсить, проверим тип
            if lessons_obj is None:
                landing["lessons_info"] = ""
            elif not isinstance(lessons_obj, dict):
                err = (f"Ошибка: lessons_info для лендинга id={landing.get('id', 'неизвестно')} имеет тип "
                       f"{type(lessons_obj).__name__}, ожидался dict")
                logger.error(err)
                errors.append(err)
                landing["lessons_info"] = ""
            else:
                for key, lesson in lessons_obj.items():
                    if isinstance(lesson, dict):
                        if "program" in lesson:
                            lesson["program"] = clean_text(lesson["program"])
                        if "name" in lesson:
                            lesson["name"] = clean_text(lesson["name"])
                        if "lesson_name" in lesson:
                            lesson["lesson_name"] = clean_text(lesson["lesson_name"])
                    else:
                        err = (f"Ошибка: для лендинга id={landing.get('id', 'неизвестно')} значение lessons_info[{key}] "
                               f"не является словарём: {lesson}")
                        logger.error(err)
                        errors.append(err)
                landing["lessons_info"] = json.dumps(lessons_obj, ensure_ascii=False)
        else:
            landing["lessons_info"] = ""

        # Обработка preview_photo – оставляем без изменений, если значение не похоже на JSON
        preview_photo = landing.get("preview_photo", "")
        if preview_photo and not preview_photo.strip().startswith("{"):
            landing["preview_photo"] = preview_photo.strip()
        else:
            landing["preview_photo"] = ""

        cleaned_landings.append(landing)

    logger.debug("После очистки лендингов: %d записей", len(cleaned_landings))
    return {"landings": cleaned_landings, "errors": errors}


def clean_course_dump(content: str) -> dict:
    """
    Извлекает данные курсов, очищает текстовые поля и возвращает словарь:
      "courses": список очищённых курсов,
      "errors": список ошибок.
    """
    courses = extract_courses_from_dump(content)
    errors = []  # Можно добавить логирование ошибок, если потребуется
    for course in courses:
        course["name"] = clean_text(course.get("name", ""))
        course["description"] = clean_text(course.get("description", ""))
        for section in course.get("sections", []):
            section["section_name"] = clean_text(section.get("section_name", ""))
            for module in section.get("modules", []):
                module["title"] = clean_text(module.get("title", ""))
                module["program_text"] = clean_text(module.get("program_text", ""))
    logger.debug("После очистки курсов: %d записей", len(courses))
    return {"courses": courses, "errors": errors}


def sql_quote(value) -> str:
    """
    Возвращает значение, заключенное в одинарные кавычки для SQL.
    Если значение None, возвращает NULL.
    Экранирует одинарные кавычки внутри строки.
    """
    if value is None:
        return "NULL"
    return "'" + str(value).replace("'", "''") + "'"


def generate_cleaned_landings_sql(landings: list) -> str:
    """
    Генерирует SQL-строку с INSERT-запросами для таблицы landings,
    используя очищённые данные.
    Порядок полей:
      id, page_name, course_name, old_price, new_price, course_program, lessons_info, lecturers_info, linked_courses, preview_photo
    """
    sql_lines = []
    for landing in landings:
        values = [
            str(landing.get("id")),
            sql_quote(landing.get("slug")),
            sql_quote(landing.get("course_name")),
            str(landing.get("old_price")) if landing.get("old_price") is not None else "NULL",
            str(landing.get("new_price")) if landing.get("new_price") is not None else "NULL",
            sql_quote(landing.get("main_text")),
            sql_quote(landing.get("lessons_info")),
            sql_quote(landing.get("lecturers_info")),
            sql_quote(landing.get("linked_courses")),
            sql_quote(landing.get("preview_photo"))
        ]
        line = "INSERT INTO `landings` (`id`, `page_name`, `course_name`, `old_price`, `new_price`, `course_program`, `lessons_info`, `lecturers_info`, `linked_courses`, `preview_photo`) VALUES (" + ", ".join(
            values) + ");"
        sql_lines.append(line)
    return "\n".join(sql_lines)


def generate_cleaned_courses_sql(courses: list) -> str:
    """
    Генерирует SQL-строку с INSERT-запросами для таблицы course,
    используя очищённые данные.
    Структура дампа курсов:
      id, name, description, lessons
    lessons представлено в виде JSON (список секций).
    """
    sql_lines = []
    for course in courses:
        course_id = str(course.get("id"))
        name = sql_quote(course.get("name"))
        description = sql_quote(course.get("description"))
        lessons_json = json.dumps(course.get("sections", []), ensure_ascii=False)
        lessons_val = sql_quote(lessons_json)
        line = "INSERT INTO `course` (`id`, `name`, `description`, `lessons`) VALUES (" + ", ".join(
            [course_id, name, description, lessons_val]) + ");"
        sql_lines.append(line)
    return "\n".join(sql_lines)
