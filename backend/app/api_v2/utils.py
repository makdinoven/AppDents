import re
import json
import logging
from datetime import datetime
from io import StringIO
from typing import Dict, Any, Union

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

# Определяем соответствие полей: имя поля в дампе → имя поля в модели
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
    Удаляет HTML-теги и инлайн-стили из строки с помощью BeautifulSoup.
    """
    if not text:
        return text
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text(separator=' ', strip=True)


def clean_json_data(data: Union[Dict[str, Any], list, str]) -> Union[Dict[str, Any], list, str]:
    """
    Рекурсивно проходит по JSON-структуре и удаляет HTML из всех строковых значений,
    не разрушая саму структуру.
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
    Парсит строку INSERT-запроса и приводит её к словарю с учетом FIELD_MAPPING.
    Применяются функции удаления HTML-тегов как для обычного текста,
    так и для строк вида JSON.
    """
    try:
        pattern = r"INSERT INTO `landings` \(([^)]+)\) VALUES \((.+)\);"
        match = re.search(pattern, line)
        if not match:
            return None

        fields_str = match.group(1)
        values_str = match.group(2)

        # Разбиваем поля и значения
        fields = [field.strip().strip('`') for field in fields_str.split(',')]
        values = values_str.split(',', len(fields) - 1)  # учитываем, что значения могут содержать запятые

        # Исключаем поле "id"
        if 'id' in fields:
            idx = fields.index('id')
            del fields[idx]
            del values[idx]

        parsed = {}
        for i, field in enumerate(fields):
            if field not in FIELD_MAPPING:
                continue
            mapped_field = FIELD_MAPPING[field]
            # Удаляем внешние одинарные кавычки
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


async def get_or_create_author(db: AsyncSession, name: str, description: str) -> Author:
    """
    Получает автора по имени или создаёт нового, если его нет.
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
        return author
    except Exception as e:
        logger.error(f"Ошибка при получении/создании автора {name}: {str(e)}")
        raise


@router.post("/import-dump")
async def import_dump(
        file: UploadFile = File(..., description="SQL dump file"),
        db: AsyncSession = Depends(get_async_db)
):
    """
    Импортирует данные из SQL дампа в базу проекта:
     – проходит по всем строкам файла,
     – удаляет HTML теги и inline стили (в том числе внутри JSON),
     – приводит поля к нужному соответствию (например, course_name → landing_name),
     – сохраняет запись лендинга и связывает с лекторами (авторами).

     Логируются все ключевые этапы и происходят выбросы исключений при критичных ошибках.
    """
    try:
        start_time = datetime.now()
        logger.info(f"🚀 Запуск импорта дампа из файла: {file.filename}")
        contents = await file.read()
        file_stream = StringIO(contents.decode('utf-8'))

        line_number = 0
        for line in file_stream:
            line_number += 1
            line = line.strip()
            if not line.startswith("INSERT INTO"):
                logger.debug(f"Пропуск строки {line_number}: не является INSERT запросом")
                continue

            parsed_data = parse_insert_line(line)
            if not parsed_data:
                logger.warning(f"⚠️ Не удалось распарсить строку {line_number}")
                continue

            logger.info(f"🔍 Обработка строки {line_number}")

            # Извлекаем данные для лендинга (без lecturer_info, обрабатываем их отдельно)
            landing_data = {k: v for k, v in parsed_data.items() if k != 'lecturers_info'}
            lessons_info = parsed_data.get('lessons_info')
            if isinstance(lessons_info, (dict, list)):
                landing_data['lessons_count'] = str(len(lessons_info))
            else:
                landing_data['lessons_count'] = "0"

            landing_data['language'] = 'EN'
            landing_data.setdefault('duration', '')

            landing = Landing(**landing_data)

            # Обработка авторов (lecturers_info)
            lecturers = parsed_data.get('lecturers_info', {})
            for lecturer_key in ['lecturer1', 'lecturer2', 'lecturer3']:
                lecturer_data = lecturers.get(lecturer_key)
                if lecturer_data and lecturer_data.get('name'):
                    author = await get_or_create_author(
                        db,
                        lecturer_data.get('name'),
                        lecturer_data.get('description', '')
                    )
                    landing.authors.append(author)
                    logger.debug(f"👤 Привязан автор: {author.name}")

            db.add(landing)
            try:
                await db.commit()
                await db.refresh(landing)
                logger.info(f"✅ Лендинг создан, ID: {landing.id}")
            except Exception as commit_error:
                await db.rollback()
                logger.error(f"❌ Ошибка коммита на строке {line_number}: {str(commit_error)}")
                continue

        elapsed = datetime.now() - start_time
        logger.info(f"🏁 Импорт завершён за {elapsed}")
        return {"status": "success", "message": "Дамп успешно импортирован", "time_elapsed": str(elapsed)}

    except Exception as e:
        logger.critical(f"💥 Критическая ошибка: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await file.close()
