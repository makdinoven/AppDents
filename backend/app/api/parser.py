import logging
import zipfile
from io import BytesIO
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..services.dis_parser_service import process_all_dumps
from ..services.dump_cleaner import clean_course_dump, clean_landing_dump, generate_cleaned_landings_sql, \
    generate_cleaned_courses_sql
from ..services.parser_service import parse_and_save, process_dump_and_update_from_content
from ..models.models import LanguageEnum
import io
import pandas as pd
from fastapi import FastAPI, Depends, Response
from sqlalchemy.orm import Session
from ..db.database import get_db, get_async_db
from ..models.models import Landing
from ..services.tilda_user_paser import process_csv_and_update_users

router = APIRouter()

def process_course(file_content: str, language: LanguageEnum, file_name: str):
    try:
        parse_and_save(file_content, language)
        print(f"Данные добавлены для курса: {file_name}")
    except Exception as exc:
        print(f"Ошибка при обработке файла {file_name}: {exc}")

@router.post("/parse-zip/")
async def parse_zip(
    background_tasks: BackgroundTasks,
    language: LanguageEnum = Query(..., description="Язык курса: EN, RU или ES"),
    file: UploadFile = File(..., description="Zip-архив, содержащий курсы")
):
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Файл должен быть zip-архивом.")

    content = await file.read()
    try:
        zip_file = zipfile.ZipFile(BytesIO(content))
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Неверный zip-архив.")

    file_names = zip_file.namelist()
    processed_count = 0
    error_count = 0
    for name in file_names:
        # Пропускаем директории
        if name.endswith("/"):
            continue
        try:
            extracted_content = zip_file.read(name)
            text = extracted_content.decode("utf-8")
            background_tasks.add_task(process_course, text, language, name)
            processed_count += 1
        except Exception as e:
            print(f"Ошибка обработки файла {name}: {e}")
            error_count += 1

    return {
        "message": "Файлы из архива загружены и обрабатываются в фоне.",
        "processed": processed_count,
        "errors": error_count
    }

app = FastAPI()

@router.get("/export")
def export_to_excel(db: Session = Depends(get_db)):
    # Делаем запрос: выбираем нужные поля
    results = db.query(Landing.title, Landing.old_price, Landing.price).all()

    # Преобразуем результат в DataFrame
    df = pd.DataFrame(results, columns=["Название курса", "Старая цена", "Цена"])

    # Записываем DataFrame в Excel в памяти
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Лендинги")
    output.seek(0)

    headers = {
        'Content-Disposition': 'attachment; filename="data.xlsx"'
    }
    return Response(
        content=output.getvalue(),
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers=headers
    )

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

@router.post("/update-modules")
async def update_modules(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Эндпоинт принимает SQL-дамп в виде загружаемого файла
    и асинхронно обновляет поле full_video_link в таблице Module,
    используя нечеткое сопоставление lesson_name и очищенного title.
    """
    try:
        logger.debug("Получен файл дампа через API.")
        file_content = (await file.read()).decode("utf-8")
        logger.debug("Содержимое файла прочитано и декодировано.")
        # Передаём оба аргумента: содержимое и объект db
        result = await process_dump_and_update_from_content(file_content, db)
        logger.debug("Асинхронная обработка дампа завершена, отправляем результат: %s", result)
    except Exception as e:
        logger.error("Ошибка в эндпоинте /update-modules: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
    return result


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


@router.post("/import-users")
async def import_users(file: UploadFile = File(...), db: AsyncSession = Depends(get_async_db)):
    """
    Эндпоинт для импорта купленных курсов для существующих пользователей из CSV-файла.
    CSV должен содержать следующие колонки (разделённые запятыми):
      1. Email
      2. Имя пользователя
      3. Статус
      4. created_at
      5. updated_at
      6. Купленные курсы – строка с названиями, разделёнными запятыми.

    Для каждого пользователя производится fuzzy‑matching названий из CSV с заголовками лендингов.
    Если совпадение выше порога, используется course_id из лендинга для создания записи в user_courses.
    Повторное присвоение одного и того же курса пользователю предотвращается.

    Возвращает статистику по добавленным записям в user_courses.
    """
    try:
        logger.debug("Получен CSV-файл для импорта курсов пользователей.")
        file_content = (await file.read()).decode("utf-8")
        logger.debug("Содержимое CSV прочитано и декодировано.")
        result = await process_csv_and_update_users(file_content, db)
        logger.debug("Импорт курсов пользователей завершён. Результат: %s", result)
    except Exception as e:
        logger.error("Ошибка в эндпоинте /import-users: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
    return result

@router.post("/import-all")
async def import_all(landing_file: UploadFile = File(...),
                     course_file: UploadFile = File(...),
                     db: AsyncSession = Depends(get_async_db)):
    """
    Эндпоинт для импорта данных из дампов:
      - landing_file: дамп landing.sql
      - course_file: дамп course.sql
    Обрабатывает данные, заполняет таблицы Landing, Course, Section, Module, Author и устанавливает связи.
    Возвращает общую статистику.
    """
    try:
        landing_content = (await landing_file.read()).decode("utf-8")
        course_content = (await course_file.read()).decode("utf-8")
        result = await process_all_dumps(landing_content, course_content, db)
        logger.debug("Импорт данных завершён. Результат: %s", result)
    except Exception as e:
        logger.error("Ошибка при импорте данных: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
    return result

@router.post("/download-cleaned-landings-sql")
async def download_cleaned_landings_sql(landing_file: UploadFile = File(...)):
    """
    Принимает файл дампа лендингов (.sql), очищает текстовые поля (course_program и внутренние поля JSON в lessons_info)
    и генерирует новый .sql-файл с INSERT-запросами для лендингов.
    Пользователь сможет скачать очищённый дамп.
    """
    try:
        content = (await landing_file.read()).decode("utf-8")
        cleaned = clean_landing_dump(content)
        cleaned_sql = generate_cleaned_landings_sql(cleaned["landings"])
        buffer = io.StringIO(cleaned_sql)
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="text/sql",
            headers={"Content-Disposition": "attachment; filename=cleaned_landings.sql"}
        )
    except Exception as e:
        logger.error("Ошибка при очистке и генерации SQL для лендингов: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/download-cleaned-courses-sql")
async def download_cleaned_courses_sql(course_file: UploadFile = File(...)):
    """
    Принимает файл дампа курсов (.sql), очищает текстовые поля и генерирует новый .sql-файл с INSERT-запросами для курсов.
    Пользователь сможет скачать очищённый дамп.
    """
    try:
        content = (await course_file.read()).decode("utf-8")
        cleaned_courses = clean_course_dump(content)
        cleaned_sql = generate_cleaned_courses_sql(cleaned_courses)
        buffer = io.StringIO(cleaned_sql)
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="text/sql",
            headers={"Content-Disposition": "attachment; filename=cleaned_courses.sql"}
        )
    except Exception as e:
        logger.error("Ошибка при очистке и генерации SQL для курсов: %s", e)
        raise HTTPException(status_code=500, detail=str(e))