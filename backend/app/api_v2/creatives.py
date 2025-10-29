from typing import Optional, Dict, Any, List
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status, Path
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..dependencies.role_checker import require_roles
from ..models.models_v2 import Book, BookCreative, CreativeStatus, BookFile, BookFileFormat
from ..services_v2.creative_service import (
    generate_all_creatives, 
    generate_single_creative, 
    PLACID_TPL_V1, 
    PLACID_TPL_V2, 
    PLACID_TPL_V3,
    BookAIValidationError,
    BookAIServiceUnavailableError,
)
from ..core.config import settings

import requests

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2")


class ManualV1(BaseModel):
    hight_description: Optional[str] = None
    medium_description: Optional[str] = None
    down_description: Optional[str] = None
    tag_1: Optional[str] = None
    tag_2: Optional[str] = None
    tag_3: Optional[str] = None


class ManualV2(BaseModel):
    hight_description: Optional[str] = None
    down_description: Optional[str] = None
    tag_1: Optional[str] = None
    tag_2: Optional[str] = None
    tag_3: Optional[str] = None


class ManualCreatives(BaseModel):
    language: str
    v1: Optional[ManualV1] = None
    v2: Optional[ManualV2] = None


class ManualCreativeFlexible(BaseModel):
    language: str
    # Произвольные поля для переопределения: price_new, price_old, title, cover_url, texts, layers, и т.д.
    fields: Optional[Dict[str, Any]] = None


class CreativeItemResponse(BaseModel):
    """Элемент креатива в ответе."""
    code: str
    status: str
    s3_url: str


class CreativesResponse(BaseModel):
    """Ответ с креативами."""
    items: List[CreativeItemResponse]
    overall: str


@router.post("/books/{book_id}/ai-process")
def ai_process(book_id: int, language: str = Query(...), db: Session = Depends(get_db), current_admin=Depends(require_roles("admin"))):
    import os
    from urllib.parse import urlparse, unquote, quote

    S3_BUCKET = os.getenv("S3_BUCKET", "cdn.dent-s.com")
    S3_PUBLIC_HOST = os.getenv("S3_PUBLIC_HOST", "https://cdn.dent-s.com")

    def _key_from_url(url: str) -> str:
        if url.startswith("s3://"):
            return urlparse(url).path.lstrip("/")
        p = urlparse(url)
        path = unquote(p.path.lstrip("/"))
        if path.startswith(f"{S3_BUCKET}/"):
            return path[len(S3_BUCKET) + 1 :]
        return path

    def _preview_key_from_src(src_key: str, pages: int) -> str:
        # books/<ID>/original/File.pdf  → books/<ID>/preview/preview_{pages}p.pdf
        from pathlib import PurePosixPath
        p = PurePosixPath(src_key)
        base = p.parent.parent
        return str(base / "preview" / f"preview_{pages}p.pdf")

    def _cdn_url_for_key(key: str) -> str:
        key = key.lstrip("/")
        return f"{S3_PUBLIC_HOST}/{quote(key, safe='/-._~()')}"

    book = db.query(Book).get(book_id)
    if not book:
        raise HTTPException(404, "Book not found")

    pdf = (
        db.query(BookFile)
          .filter(BookFile.book_id == book.id, BookFile.file_format == BookFileFormat.PDF)
          .first()
    )
    if not pdf:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "No source PDF for the book")

    src_key = _key_from_url(pdf.s3_url)
    prev_key = _preview_key_from_src(src_key, 20)
    preview_pdf_url = _cdn_url_for_key(prev_key)

    # Проверяем доступность превью 20p, иначе fallback на исходный PDF (подпись/прямая ссылка)
    try:
        head = requests.head(preview_pdf_url, timeout=5, allow_redirects=True)
        if head.status_code != 200:
            raise RuntimeError("not ready")
    except Exception:
        # Fallback: используем исходный PDF URL (как есть)
        preview_pdf_url = pdf.s3_url

    r = requests.post(
        f"{settings.BOOKAI_BASE_URL}/process",
        json={"s3_url": preview_pdf_url, "language": language, "book_id": book_id},
        timeout=30,
    )
    if r.status_code >= 300:
        raise HTTPException(r.status_code, r.text[:500])
    return r.json()


def _order_creatives_by_template(creatives: List[BookCreative]) -> List[BookCreative]:
    """Упорядочивает креативы по шаблонам: v1, v2, v3."""
    order = {PLACID_TPL_V1: 0, PLACID_TPL_V2: 1, PLACID_TPL_V3: 2}
    return sorted(creatives, key=lambda x: order.get(x.creative_code, 999))


@router.get("/books/{book_id}/creatives", response_model=CreativesResponse)
def get_or_create_creatives(
    book_id: int,
    language: str = Query(..., description="Язык креатива (RU, EN, ES, PT, AR, IT)"),
    regen: bool = Query(False, description="Принудительно перегенерировать все креативы"),
    db: Session = Depends(get_db),
    current_admin=Depends(require_roles("admin")),
):
    """
    Получить или создать креативы для книги.
    
    Возвращает три креатива в фиксированном порядке:
    - v1 (TPL: kbhccvksoprg7)
    - v2 (TPL: ktawlyumyeaw7)
    - v3 (TPL: uoshaoahss0al)
    
    Каждый элемент содержит code (creative_code), status и s3_url.
    """
    q = db.query(BookCreative).filter_by(book_id=book_id, language=language)
    items = q.all()
    ready = {x.creative_code: x for x in items if x.status == CreativeStatus.READY}
    needed = {PLACID_TPL_V1, PLACID_TPL_V2, PLACID_TPL_V3}

    if not regen and needed.issubset(set(ready.keys())):
        ordered = _order_creatives_by_template([ready[code] for code in needed if code in ready])
        return {
            "items": [
                {"code": x.creative_code, "status": x.status.value, "s3_url": x.s3_url or ""}
                for x in ordered
            ],
            "overall": "ready",
        }

    # Генерация (синхронно)
    try:
        results = generate_all_creatives(db, book_id, language)
        ordered = _order_creatives_by_template(results)
        return {
            "items": [
                {"code": x.creative_code, "status": x.status.value, "s3_url": x.s3_url or ""}
                for x in ordered
            ],
            "overall": "ready",
        }
    except BookAIValidationError as e:
        logger.error(f"BookAI validation error in get_or_create_creatives, book_id={book_id}, language={language}: {e}")
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(e))
    except BookAIServiceUnavailableError as e:
        logger.error(f"BookAI service unavailable in get_or_create_creatives, book_id={book_id}, language={language}: {e}")
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(e))
    except ValueError as e:
        logger.error(f"ValueError in get_or_create_creatives, book_id={book_id}, language={language}: {e}")
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(e))
    except Exception as e:
        logger.error(f"Unexpected error in get_or_create_creatives, book_id={book_id}, language={language}: {e}", exc_info=True)
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Failed to generate creatives: {str(e)}")



@router.post("/books/{book_id}/creatives/manual/{target}", response_model=CreativesResponse)
def manual_single_creative(
    book_id: int,
    target: str = Path(
        ...,
        description=f"Целевой креатив для обновления: 'v1' | 'v2' | 'v3' или конкретный creative_code.\n"
                    f"Допустимые значения:\n"
                    f"- v1 (или {PLACID_TPL_V1})\n"
                    f"- v2 (или {PLACID_TPL_V2})\n"
                    f"- v3 (или {PLACID_TPL_V3})"
    ),
    body: ManualCreativeFlexible = ...,
    db: Session = Depends(get_db),
    current_admin=Depends(require_roles("admin")),
):
    """
    Ручная регенерация ОДНОГО креатива для книги.
    
    **target** - какой креатив обновить:
    - `v1` (или `kbhccvksoprg7`) - первый шаблон
    - `v2` (или `ktawlyumyeaw7`) - второй шаблон  
    - `v3` (или `uoshaoahss0al`) - третий шаблон
    
    **body.fields** - словарь произвольных переопределений:
    - `price_new`, `price_old` - цены
    - `title` - название книги
    - `cover_url` - URL обложки
    - `texts` - словарь с текстовыми полями (hight_description, tag_1, tag_2, tag_3 и т.д.)
    - `layers` - полный словарь слоёв для Placid (если нужно полное переопределение)
    
    Возвращает массив с одним элементом, содержащим code, status и s3_url обновлённого креатива.
    """
    overrides = body.fields or {}
    try:
        item = generate_single_creative(db, book_id, body.language, target, overrides=overrides)
        return {
            "items": [
                {"code": item.creative_code, "status": item.status.value, "s3_url": item.s3_url or ""}
            ],
            "overall": "ready",
        }
    except BookAIValidationError as e:
        logger.error(f"BookAI validation error in manual_single_creative, book_id={book_id}, target={target}, language={body.language}: {e}")
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(e))
    except BookAIServiceUnavailableError as e:
        logger.error(f"BookAI service unavailable in manual_single_creative, book_id={book_id}, target={target}, language={body.language}: {e}")
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(e))
    except ValueError as e:
        logger.error(f"ValueError in manual_single_creative, book_id={book_id}, target={target}, language={body.language}: {e}")
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(e))
    except Exception as e:
        logger.error(f"Unexpected error in manual_single_creative, book_id={book_id}, target={target}, language={body.language}: {e}", exc_info=True)
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Failed to generate creative: {str(e)}")

@router.post("/books/{book_id}/creatives/manual", response_model=CreativesResponse)
def manual_creatives(
    book_id: int,
    body: ManualCreatives,
    db: Session = Depends(get_db),
    current_admin=Depends(require_roles("admin")),
):
    """
    Ручная регенерация всех креативов (v1 и v2) для книги.
    
    Обновляет креативы v1 и v2 одновременно, если переданы соответствующие данные.
    Креатив v3 генерируется автоматически без ручных данных.
    
    Возвращает все три креатива в фиксированном порядке:
    - v1 (TPL: kbhccvksoprg7)
    - v2 (TPL: ktawlyumyeaw7)
    - v3 (TPL: uoshaoahss0al)
    
    Каждый элемент содержит code (creative_code), status и s3_url.
    """
    mp: Dict[str, Dict] = {}
    if body.v1:
        mp["v1"] = body.v1.dict(exclude_none=True)
    if body.v2:
        mp["v2"] = body.v2.dict(exclude_none=True)
    try:
        results = generate_all_creatives(db, book_id, body.language, manual_payload=mp or None)
        ordered = _order_creatives_by_template(results)
        return {
            "items": [
                {"code": x.creative_code, "status": x.status.value, "s3_url": x.s3_url or ""}
                for x in ordered
            ],
            "overall": "ready",
        }
    except BookAIValidationError as e:
        logger.error(f"BookAI validation error in manual_creatives, book_id={book_id}, language={body.language}: {e}")
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(e))
    except BookAIServiceUnavailableError as e:
        logger.error(f"BookAI service unavailable in manual_creatives, book_id={book_id}, language={body.language}: {e}")
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(e))
    except ValueError as e:
        logger.error(f"ValueError in manual_creatives, book_id={book_id}, language={body.language}: {e}")
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(e))
    except Exception as e:
        logger.error(f"Unexpected error in manual_creatives, book_id={book_id}, language={body.language}: {e}", exc_info=True)
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Failed to generate creatives: {str(e)}")


