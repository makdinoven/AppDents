import re
import json
import csv
import io
import html
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Функция для удаления HTML-тегов
def strip_html(html_content: str) -> str:
    if not html_content:
        return html_content
    # Если input выглядит как имя файла, BeautifulSoup может ругаться – обрабатываем как строку
    soup = BeautifulSoup(html_content, "lxml")
    return soup.get_text(separator=' ', strip=True)

# Функция очистки текста: распаковка HTML-сущностей, удаление тегов и нормализация пробелов
def clean_text(text: str) -> str:
    if not text:
        return text
    text = html.unescape(text)
    cleaned = strip_html(text)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

# Рекурсивно очищает все строковые значения в JSON-объекте
def clean_json_object(obj):
    if isinstance(obj, dict):
        return {key: clean_json_object(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [clean_json_object(item) for item in obj]
    elif isinstance(obj, str):
        return clean_text(obj)
    else:
        return obj


logger = logging.getLogger(__name__)


def extract_landings_from_dump(content: str) -> list:
    landings = []
    query_pattern = re.compile(
        r"INSERT INTO\s+`landings`\s+\(.*?\)\s+VALUES\s+(\(.*?\));", re.DOTALL | re.IGNORECASE)
    queries = query_pattern.findall(content)
    logger.debug("Найдено %d запросов.", len(queries))  # Логируем количество запросов
    for query in queries:
        query = query.strip()
        if query.startswith("(") and query.endswith(")"):
            query = query[1:-1]

        # Разбиваем по разделителям записи
        rows = re.split(r"\),\s*\(", query)
        logger.debug("Найдено %d записей в одном запросе.", len(rows))  # Логируем количество записей
        for row in rows:
            try:
                sio = io.StringIO(row, newline='')
                reader = csv.reader(sio, delimiter=',', quotechar="'", escapechar='\\', skipinitialspace=True)
                fields = next(reader)

                # Проверка на достаточное количество полей
                if len(fields) < 10:
                    logger.warning("Недостаточно полей в записи: %s", fields)  # Логируем недостающие поля
                    fields += [None] * (10 - len(fields))  # Дополняем None, если поля отсутствуют

                # Очистка данных от лишних символов
                landing_id = int(fields[0].strip()) if fields[0] else None
                page_name = fields[1].strip() if fields[1] else None
                course_name = fields[2].strip() if fields[2] else None
                old_price_str = fields[3].strip().strip("'") if fields[3] else None
                new_price_str = fields[4].strip().strip("'") if fields[4] else None

                try:
                    old_price = float(old_price_str) if old_price_str else None
                except Exception:
                    old_price = None
                try:
                    new_price = float(new_price_str) if new_price_str else None
                except Exception:
                    new_price = None

                course_program = fields[5].strip() if fields[5] else None
                lessons_info = fields[6].strip() if fields[6] else None
                lecturers_info = fields[7].strip() if fields[7] else None
                linked_courses = fields[8].strip() if fields[8] else None
                preview_photo = fields[9].strip() if fields[9] else None

                # Очистка HTML из текста
                course_program_clean = re.sub(r'<[^>]*>', '', course_program) if course_program else None
                lessons_info_clean = re.sub(r'<[^>]*>', '', lessons_info) if lessons_info else None
                lecturers_info_clean = re.sub(r'<[^>]*>', '', lecturers_info) if lecturers_info else None

                # Логируем изображения в lecturers_info
                if lecturers_info and "<img" in lecturers_info:
                    logger.warning("Обнаружено изображение в поле 'lecturers_info' для лендинга %s", landing_id)

                # Проблемы с большими данными: если в lectureres_info записано слишком много данных, она могла попасть в другое поле
                if len(course_program) > 500:  # Примерная длина для проверки
                    logger.warning("Запись о курсе слишком длинная, может быть сбой. Лендинг %s", landing_id)

                # Дополнительная проверка для linked_courses
                if linked_courses is None or linked_courses == "":
                    logger.warning("Поле linked_courses пусто для лендинга %s", landing_id)

                # Преобразуем данные в структуру
                landing = {
                    "id": landing_id,
                    "slug": page_name,
                    "course_name": course_name,
                    "old_price": old_price,
                    "new_price": new_price,
                    "main_text": course_program_clean,
                    "lessons_info": lessons_info_clean,
                    "lecturers_info": lecturers_info_clean,
                    "linked_courses": linked_courses,
                    "preview_photo": preview_photo,
                    "language": "EN"
                }

                landings.append(landing)
            except Exception as e:
                logger.error("Ошибка при разборе строки лендинга: %s", e)

    logger.debug("Извлечено %d лендингов", len(landings))
    return landings


# Генерация SQL-дампа из очищённых данных лендингов
def generate_cleaned_landings_sql(landings: list) -> str:
    def sql_quote(value) -> str:
        if value is None:
            return "NULL"
        return "'" + str(value).replace("'", "''") + "'"
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
        line = ("INSERT INTO `landings` "
                "(`id`, `page_name`, `course_name`, `old_price`, `new_price`, `course_program`, "
                "`lessons_info`, `lecturers_info`, `linked_courses`, `preview_photo`) VALUES ("
                + ", ".join(values) + ");")
        sql_lines.append(line)
    return "\n".join(sql_lines)

# Основная функция очистки дампа лендингов
def clean_landing_dump(content: str) -> dict:
    raw_landings = extract_landings_from_dump(content)
    cleaned_landings = []
    errors = []
    for landing in raw_landings:
        try:
            landing["course_name"] = clean_text(landing.get("course_name", ""))
            landing["main_text"] = clean_text(landing.get("main_text", ""))
            landing["slug"] = clean_text(landing.get("slug", ""))
        except Exception as e:
            errors.append(f"Ошибка очистки course_name/main_text/slug для id={landing.get('id', 'неизвестно')}: {e}")
            continue

        # Обработка lessons_info (JSON)
        lessons_info = landing.get("lessons_info", "")
        if lessons_info:
            try:
                lessons_obj = json.loads(lessons_info)
                lessons_clean = clean_json_object(lessons_obj)
                landing["lessons_info"] = json.dumps(lessons_clean, ensure_ascii=False)
            except Exception as e:
                errors.append(f"Ошибка парсинга/очистки lessons_info для id={landing.get('id', 'неизвестно')}: {e}")
        else:
            landing["lessons_info"] = ""

        # Обработка lecturers_info (JSON)
        lecturers_info = landing.get("lecturers_info", "")
        if lecturers_info:
            try:
                lecturers_obj = json.loads(lecturers_info)
                lecturers_clean = clean_json_object(lecturers_obj)
                landing["lecturers_info"] = json.dumps(lecturers_clean, ensure_ascii=False)
            except Exception as e:
                errors.append(f"Ошибка парсинга/очистки lecturers_info для id={landing.get('id', 'неизвестно')}: {e}")
        else:
            landing["lecturers_info"] = ""

        # Поле linked_courses оставляем как есть (можно добавить дополнительную обработку, если требуется)
        # Поле preview_photo – оставляем, если оно не начинается с '{'
        preview_photo = landing.get("preview_photo", "")
        if preview_photo and not preview_photo.startswith("{"):
            landing["preview_photo"] = preview_photo.strip()
        else:
            landing["preview_photo"] = ""
        cleaned_landings.append(landing)
    logger.debug("После очистки лендингов: %d записей", len(cleaned_landings))
    return {"landings": cleaned_landings, "errors": errors}
