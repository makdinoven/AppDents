import io
from fastapi import UploadFile, File, HTTPException
from starlette.responses import StreamingResponse

from ..db.database import get_db
from ..models.models_v2 import Author, Landing
from ..services import dump_cleaner

import re
import logging
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from typing import Dict, Any
import json
from datetime import datetime

router=APIRouter()
@router.post("/download-cleaned-landings-sql")
async def download_cleaned_landings_sql(landing_file: UploadFile = File(...)):
    """
    Принимает SQL дамп лендингов (.sql), очищает текстовые поля (в course_program и внутри lessons_info, lecturers_info)
    и генерирует новый SQL дамп для скачивания.
    """
    try:
        content = (await landing_file.read()).decode("utf-8")
        result = dump_cleaner.clean_landing_dump(content)
        cleaned_landings = result.get("landings", [])
        errors = result.get("errors", [])
        if errors:
            for err in errors:
                logger.error(err)
        if not cleaned_landings:
            raise HTTPException(status_code=400, detail="Не удалось извлечь записи лендингов.")
        cleaned_sql = dump_cleaner.generate_cleaned_landings_sql(cleaned_landings)
        buffer = io.StringIO(cleaned_sql)
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="text/sql",
            headers={"Content-Disposition": "attachment; filename=cleaned_landings.sql"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Настройка логгера
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('migration.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


# Регулярка для парсинга INSERT запросов
INSERT_PATTERN = re.compile(
    r"INSERT INTO `landings` \(([^)]+)\) VALUES \((.+)\);",
    re.IGNORECASE
)

# Соответствие полей между дампом и моделью
FIELD_MAPPING = {
    'id': 'id',
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
    """Удаление HTML тегов и стилей из текста"""
    if not text:
        return text
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text(separator=' ', strip=True)


def clean_json_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Рекурсивная очистка HTML из структур JSON"""
    cleaned = {}
    for key, value in data.items():
        if isinstance(value, dict):
            cleaned[key] = clean_json_data(value)
        elif isinstance(value, str):
            cleaned[key] = remove_html_tags(value)
        else:
            cleaned[key] = value
    return cleaned


def parse_insert_line(line: str) -> Dict[str, Any]:
    """Парсинг строки INSERT в словарь"""
    try:
        match = INSERT_PATTERN.search(line)
        if not match:
            return None

        fields = [f.strip().strip('`') for f in match.group(1).split(',')]
        values = match.group(2).split(',', len(fields) - 1)

        parsed = {}
        for i, field in enumerate(fields):
            value = values[i].strip().strip("'")
            if value.startswith('{') or value.startswith('['):
                try:
                    parsed_value = json.loads(value.replace("\\", ""))
                    parsed_value = clean_json_data(parsed_value)
                except json.JSONDecodeError:
                    parsed_value = remove_html_tags(value)
            else:
                parsed_value = remove_html_tags(value)

            mapped_field = FIELD_MAPPING.get(field)
            if mapped_field:
                parsed[mapped_field] = parsed_value

        return parsed
    except Exception as e:
        logger.error(f"Error parsing line: {line}\nError: {str(e)}")
        return None


def get_or_create_author(db: Session, name: str, description: str) -> Author:
    """Создание или получение автора"""
    author = db.query(Author).filter(Author.name == name).first()
    if not author:
        author = Author(
            name=name,
            description=remove_html_tags(description),
            language='EN'
        )
        db.add(author)
        db.commit()
        db.refresh(author)
        logger.info(f"Created new author: {name}")
    return author


@router.post("/import-dump")
async def import_dump(
        dump_file_path: str = "path/to/your/dump.sql",
        db: Session = Depends(get_db)
):
    try:
        start_time = datetime.now()
        logger.info(f"Starting dump import from: {dump_file_path}")

        with open(dump_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line.startswith("INSERT INTO"):
                    continue

                parsed_data = parse_insert_line(line)
                if not parsed_data:
                    continue

                # Создание лендинга
                landing = Landing(
                    **{k: v for k, v in parsed_data.items() if k != 'lecturers_info'},
                    language='EN',
                    duration='',  # Заполнить при необходимости
                    lessons_count=str(len(parsed_data.get('lessons_info', {})))
                )

                # Обработка авторов
                lecturers = parsed_data.get('lecturers_info', {})
                for lecturer_key in ['lecturer1', 'lecturer2', 'lecturer3']:
                    lecturer_data = lecturers.get(lecturer_key)
                    if lecturer_data:
                        author = get_or_create_author(
                            db,
                            lecturer_data['name'],
                            lecturer_data['description']
                        )
                        landing.authors.append(author)

                db.add(landing)
                db.commit()
                db.refresh(landing)
                logger.info(f"Successfully imported landing: {landing.id}")

        logger.info(f"Import completed in {datetime.now() - start_time}")
        return {"status": "success", "message": "Dump imported successfully"}

    except Exception as e:
        db.rollback()
        logger.error(f"Import failed: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}