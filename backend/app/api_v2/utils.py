import re
import json
import logging
from datetime import datetime
from io import StringIO
from typing import Dict, Any, Union, Tuple

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

# Соответствие полей: ключ = поле в дампе, значение = поле в модели проекта
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
    Удаляет HTML теги и inline стили из строки с помощью BeautifulSoup.
    """
    if not text:
        return text
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text(separator=' ', strip=True)


def clean_json_data(data: Union[Dict[str, Any], list, str]) -> Union[Dict[str, Any], list, str]:
    """
    Рекурсивно проходит по JSON-структуре и удаляет HTML из всех строковых значений,
    не нарушая структуру.
    """
    if isinstance(data, dict):
        return {k: clean_json_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_json_data(item) for item in data]
    elif isinstance(data, str):
        return remove_html_tags(data)
    else:
        return data


def parse_insert_line(line: str) -> Union[Dict[str, Any], None]:
    """
    Парсит строку INSERT запроса и возвращает словарь с полями,
    преобразованными согласно FIELD_MAPPING. Для JSON-значений выполняется очистка.
    """
    try:
        pattern = r"INSERT INTO `landings` \(([^)]+)\) VALUES \((.+)\);"
        match = re.search(pattern, line)
        if not match:
            return None

        fields_str = match.group(1)
        values_str = match.group(2)

        # Разбиваем строки с полями и значениями
        fields = [field.strip().strip('`') for field in fields_str.split(',')]
        values = values_str.split(',', len(fields) - 1)  # учитываем, что значение может содержать запятые

        # Удаляем поле "id"
        if 'id' in fields:
            idx = fields.index('id')
            del fields[idx]
            del values[idx]

        parsed = {}
        for i, field in enumerate(fields):
            if field not in FIELD_MAPPING:
                continue
            mapped_field = FIELD_MAPPING[field]
            # Убираем внешние одинарные кавычки
            value = values[i].strip().strip("'")
            if value.startswith('{') or value.startswith('['):
                try:
                    json_value = json.loads(value.replace("\\", ""))
                    cleaned_json = clean_json_data(json_value)
                    parsed[mapped_field] = cleaned_json
                except json.JSONDecodeError:
                    parsed[mapped_field] = remove_html_tags(value)
            else:
                parsed[mapped_field] = remove_html_tags(value)
        return parsed

    except Exception as e:
        logger.error(f"Ошибка при парсинге строки: {line}\nОшибка: {str(e)}")
        return None


async def get_or_create_author(db: AsyncSession, name: str, description: str) -> Tuple[Author, bool]:
    """
    Получает автора по имени или создаёт нового, если его нет.
    Возвращает кортеж (author, created) где created=True, если автор создан.
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
        logger.error(f"Ошибка при получении/создании автора {name}: {str(e)}")
        raise


@router.post("/import-dump")
async def import_dump(
        file: UploadFile = File(..., description="SQL dump file"),
        db: AsyncSession = Depends(get_async_db)
):
    """
    Импортирует дамп SQL в базу данных проекта.
    Для каждой строки дампа:
      – Выполняется парсинг и очистка HTML тегов из текстовых полей (включая JSON-структуру),
      – Приводятся поля согласно требуемой модели (например, course_name → landing_name),
      – Создаётся объект Landing, вычисляется количество уроков по lessons_info,
      – Из lecturers_info извлекаются данные для авторов, которые создаются/связываются,
      – Выполняется вставка в базу.

    В ответ возвращается сводная статистика:
      • Общее количество обработанных строк,
      • Количество успешно вставленных лендингов,
      • Количество строк, не распознанных для импорта,
      • Количество ошибок при коммитах,
      • Количество созданных новых авторов.

    Логируются все этапы и выбрасываются исключения при критичных ошибках.
    """
    total_lines = 0
    landings_inserted = 0
    failed_parse = 0
    commit_errors = 0
    new_authors_created = 0

    try:
        start_time = datetime.now()
        logger.info(f"🚀 Запуск импорта дампа из файла: {file.filename}")
        contents = await file.read()
        file_stream = StringIO(contents.decode('utf-8'))

        for line in file_stream:
            total_lines += 1
            line = line.strip()
            if not line.startswith("INSERT INTO"):
                logger.debug(f"Пропуск строки {total_lines}: не является INSERT запросом")
                continue

            parsed_data = parse_insert_line(line)
            if not parsed_data:
                failed_parse += 1
                logger.warning(f"⚠️ Не удалось распарсить строку {total_lines}")
                continue

            logger.info(f"🔍 Обработка строки {total_lines}")

            # Формируем данные для лендинга (без lecturers_info)
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
                logger.error(f"❌ Ошибка коммита на строке {total_lines}: {str(commit_error)}")
                continue

        elapsed = datetime.now() - start_time
        logger.info(f"🏁 Импорт завершён за {elapsed}")
        return {
            "status": "success",
            "message": "Дамп успешно импортирован",
            "time_elapsed": str(elapsed),
            "lines_processed": total_lines,
            "landings_inserted": landings_inserted,
            "lines_failed_parse": failed_parse,
            "commit_errors": commit_errors,
            "new_authors_created": new_authors_created
        }

    except Exception as e:
        logger.critical(f"💥 Критическая ошибка: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await file.close()
