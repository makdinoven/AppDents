import re
import csv
import json
import logging
from datetime import datetime
from io import StringIO
from typing import Dict, Any, Union, Tuple, Optional

from bs4 import BeautifulSoup
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..db.database import get_async_db
from ..models.models_v2 import Author, Landing

router = APIRouter()

# Настройка логгера
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Соответствие полей: ключ – имя в дампе, значение – имя в модели
FIELD_MAPPING = {
    'page_name': 'page_name',
    'course_name': 'landing_name',
    'old_price': 'old_price',
    'new_price': 'new_price',
    'course_program': 'course_program',
    'lessons_info': 'lessons_info',
    'lecturers_info': 'lecturers_info',
    'linked_courses': 'linked_courses',
    'preview_photo': 'preview_photo'
}


def remove_html_tags(text: str) -> str:
    """
    Удаляет HTML-теги и inline стили из строки.
    """
    if not text:
        return text
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text(separator=' ', strip=True)


def clean_json_data(data: Union[Dict[str, Any], list, str]) -> Union[Dict[str, Any], list, str]:
    """
    Рекурсивно проходит по JSON-структуре и очищает все строковые значения от HTML-тегов.
    """
    if isinstance(data, dict):
        return {k: clean_json_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_json_data(item) for item in data]
    elif isinstance(data, str):
        return remove_html_tags(data)
    else:
        return data


def parse_insert_line(statement: str) -> Optional[Dict[str, Any]]:
    """
    Принимает полный INSERT оператор из дампа.
    Извлекает список полей и значения, используя регулярное выражение с флагом DOTALL
    и модуль csv для корректного парсинга значений.

    Возвращает словарь с данными, где имена полей приведены согласно FIELD_MAPPING.
    """
    try:
        # Пример оператора:
        # INSERT INTO `landings` (`id`, `page_name`, `course_name`, ... )
        # VALUES (442, 'ninja-sinus-lift', 'Ninja Sinus Lift', ... );
        pattern = re.compile(r"INSERT INTO `landings`\s*\((.*?)\)\s*VALUES\s*\((.*?)\);", re.DOTALL)
        match = pattern.search(statement)
        if not match:
            return None

        fields_part = match.group(1)
        values_part = match.group(2)

        # Разбиваем список полей по запятой
        fields = [f.strip().strip('`') for f in fields_part.split(',')]

        # Используем csv для разбиения values, чтобы корректно обработать запятые в значениях
        csv_reader = csv.reader(StringIO(values_part), delimiter=',', quotechar="'", escapechar='\\')
        row = next(csv_reader)
        values = [val.strip() for val in row]

        # Если поле id присутствует, то оно исключается
        if 'id' in fields:
            idx = fields.index('id')
            del fields[idx]
            del values[idx]

        parsed = {}
        for i, field in enumerate(fields):
            if field not in FIELD_MAPPING:
                continue
            mapped_field = FIELD_MAPPING[field]
            value = values[i]
            # Если значение начинается с { или [, предполагаем JSON и пытаемся его загрузить
            if value.startswith('{') or value.startswith('['):
                try:
                    json_value = json.loads(value)
                    cleaned_json = clean_json_data(json_value)
                    parsed[mapped_field] = cleaned_json
                except json.JSONDecodeError:
                    parsed[mapped_field] = remove_html_tags(value)
            else:
                parsed[mapped_field] = remove_html_tags(value)
        return parsed

    except Exception as e:
        logger.error(f"Ошибка при парсинге оператора:\n{statement}\nОшибка: {str(e)}")
        return None


async def get_or_create_author(db: AsyncSession, name: str, description: str) -> Tuple[Author, bool]:
    """
    Пытается найти автора по имени, если не найден – создаёт нового.
    Возвращает кортеж (author, created), где created True, если автор создан.
    """
    try:
        result = await db.execute(select(Author).where(Author.name == name))
        author = result.scalars().first()
        if not author:
            author = Author(
                name=name,
                description=remove_html_tags(description),
                language='EN'
            )
            db.add(author)
            await db.commit()
            await db.refresh(author)
            logger.info(f"Создан новый автор: {name}")
            return (author, True)
        return (author, False)
    except Exception as e:
        logger.error(f"Ошибка при получении/создании автора '{name}': {str(e)}")
        raise


@router.post("/import-dump")
async def import_dump(
        file: UploadFile = File(..., description="SQL dump file"),
        db: AsyncSession = Depends(get_async_db)
):
    """
    Импортирует SQL дамп в базу проекта.

    Для каждого оператора INSERT:
      • Парсится оператор (с учётом многострочности)
      • Удаляются HTML-теги и inline стили из текстовых полей (а также рекурсивно внутри JSON)
      • Поля приводятся к нужному соответствию (например, course_name → landing_name)
      • Создаётся объект Landing, вычисляется количество уроков (на основе lessons_info)
      • Из lecturers_info извлекаются данные для авторов, которые создаются (или берутся из базы) и связываются
      • Выполняется вставка в БД

    В ответе возвращается сводная статистика:
      – Общее количество найденных операторов INSERT
      – Количество успешно вставленных лендингов
      – Количество операторов, которые не удалось распарсить
      – Количество ошибок коммита
      – Количество созданных новых авторов
      – Общее время импорта
    """
    total_statements = 0
    landings_inserted = 0
    failed_parse = 0
    commit_errors = 0
    new_authors_created = 0

    try:
        start_time = datetime.now()
        logger.info(f"🚀 Запуск импорта дампа из файла: {file.filename}")
        contents = await file.read()
        content_str = contents.decode('utf-8')

        # Используем finditer для нахождения всех INSERT операторов в файле (многострочные)
        pattern = re.compile(r"(INSERT INTO `landings`\s*\(.*?\)\s*VALUES\s*\(.*?\);)", re.DOTALL)
        statements = pattern.findall(content_str)
        logger.info(f"Найдено операторов INSERT: {len(statements)}")
        total_statements = len(statements)

        for stmt in statements:
            parsed_data = parse_insert_line(stmt)
            if not parsed_data:
                failed_parse += 1
                logger.warning(f"⚠️ Не удалось распарсить оператор:\n{stmt[:200]}...")
                continue

            logger.info("🔍 Обработка оператора INSERT")

            # Формирование данных для лендинга (без lecturers_info)
            landing_data = {k: v for k, v in parsed_data.items() if k != 'lecturers_info'}

            lessons_info = parsed_data.get('lessons_info')
            if isinstance(lessons_info, (dict, list)):
                landing_data['lessons_count'] = str(len(lessons_info))
            else:
                landing_data['lessons_count'] = "0"

            landing_data['language'] = 'EN'
            landing_data.setdefault('duration', '')

            landing = Landing(**landing_data)

            # Обработка авторов из lecturers_info
            lecturers = parsed_data.get('lecturers_info', {})
            for lecturer_key in ['lecturer1', 'lecturer2', 'lecturer3']:
                lecturer_data = lecturers.get(lecturer_key)
                if lecturer_data and lecturer_data.get('name'):
                    author, created = await get_or_create_author(
                        db,
                        lecturer_data.get('name'),
                        lecturer_data.get('description', '')
                    )
                    if created:
                        new_authors_created += 1
                    landing.authors.append(author)
                    logger.debug(f"👤 Привязан автор: {author.name}")

            db.add(landing)
            try:
                await db.commit()
                await db.refresh(landing)
                landings_inserted += 1
                logger.info(f"✅ Лендинг создан, ID: {landing.id}")
            except Exception as commit_error:
                commit_errors += 1
                await db.rollback()
                logger.error(f"❌ Ошибка коммита для оператора:\n{stmt[:200]}...\nОшибка: {str(commit_error)}")
                continue

        elapsed = datetime.now() - start_time
        logger.info(f"🏁 Импорт завершён за {elapsed}")
        return {
            "status": "success",
            "message": "Дамп успешно импортирован",
            "time_elapsed": str(elapsed),
            "statements_found": total_statements,
            "landings_inserted": landings_inserted,
            "statements_failed_parse": failed_parse,
            "commit_errors": commit_errors,
            "new_authors_created": new_authors_created
        }

    except Exception as e:
        logger.critical(f"💥 Критическая ошибка импорта: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await file.close()
