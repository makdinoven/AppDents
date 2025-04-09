import io
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from starlette.responses import StreamingResponse

from ..services import dump_cleaner

router=APIRouter()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

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