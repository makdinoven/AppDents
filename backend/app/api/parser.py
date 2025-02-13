# api/routes.py
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from ..services.parser_service import parse_and_save
from ..models.models import LanguageEnum

router = APIRouter()


@router.post("/{lang_code}")
async def parse_html(lang_code: str, html_file: UploadFile = File(...)):
    # Определяем язык по коду: en, ru, es
    lang_map = {
        'en': LanguageEnum.EN,
        'ru': LanguageEnum.RU,
        'es': LanguageEnum.ES
    }
    language = lang_map.get(lang_code.lower())
    if not language:
        raise HTTPException(status_code=400, detail="Неверный код языка")

    try:
        content = await html_file.read()
        html_content = content.decode("utf-8")
    except Exception as e:
        raise HTTPException(status_code=400, detail="Ошибка чтения файла: " + str(e))

    try:
        parse_and_save(html_content, language)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Ошибка при сохранении данных: " + str(e))

    return JSONResponse(content={"status": "Данные успешно сохранены"})
