import zipfile
from io import BytesIO
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException, Query
from ..services.parser_service import parse_and_save
from ..models.models import LanguageEnum

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
