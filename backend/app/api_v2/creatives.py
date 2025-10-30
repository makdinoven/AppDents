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
    PlacidQuotaError,
    PlacidServiceError,
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
    creative_code: str
    status: str
    s3_url: str
    payload_used: Optional[Dict[str, Any]] = None


class CreativesResponse(BaseModel):
    """Ответ с креативами."""
    items: List[CreativeItemResponse]
    overall: str


@router.post("/books/{book_id}/ai-process")
def ai_process(book_id: int, language: str = Query(...), db: Session = Depends(get_db), current_admin=Depends(require_roles("admin"))):
    import os
    from urllib.parse import urlparse, unquote, quote
    import time

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

    # Надёжный запуск процесса с ретраями на 5xx/таймауты (например, 524 от CDN)
    r = None
    post_max_attempts = 5
    post_interval_sec = 2
    for post_attempt in range(1, post_max_attempts + 1):
        try:
            r = requests.post(
                f"{settings.BOOKAI_BASE_URL}/process",
                json={"s3_url": preview_pdf_url, "language": language, "book_id": book_id},
                timeout=60,
            )
        except requests.exceptions.RequestException as e:
            logger.warning(f"BookAI /process request failed on attempt {post_attempt}: {e}")
            if post_attempt == post_max_attempts:
                raise HTTPException(status.HTTP_502_BAD_GATEWAY, "BookAI request failed")
            time.sleep(post_interval_sec)
            continue

        # Мягко обрабатываем 5xx (включая 524) ретраями, 4xx — сразу ошибка
        if r.status_code >= 500:
            logger.warning(f"BookAI /process returned {r.status_code} on attempt {post_attempt}")
            if post_attempt == post_max_attempts:
                raise HTTPException(r.status_code, r.text[:500])
            time.sleep(post_interval_sec)
            continue
        if r.status_code >= 400:
            raise HTTPException(r.status_code, r.text[:500])
        break

    # Если BookAI уже вернул финальный результат — отдадим сразу
    try:
        resp = r.json()
    except ValueError:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "BookAI returned non-JSON response")

    if not isinstance(resp, dict):
        return resp

    status_val = str(resp.get("status") or "").lower()
    task_id = resp.get("task_id") or resp.get("job_id") or resp.get("id")

    # Статусы строго по контракту BookAI
    if status_val == "completed":
        return resp
    if status_val == "failed":
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, resp.get("error_message") or "BookAI processing failed")

    # Для pending/processing — обязательен task_id
    if not task_id:
        # Нет способа ждать — возвращаем исходный ответ
        return resp

    polling_url = f"{settings.BOOKAI_BASE_URL}/task/{task_id}"

    # Polling до завершения
    max_attempts = 45  # ~1.5 минуты при 2s
    interval_sec = 2
    for attempt in range(1, max_attempts + 1):
        time.sleep(interval_sec)
        try:
            pr = requests.get(polling_url, timeout=20)
        except requests.exceptions.RequestException as e:
            logger.warning(f"BookAI polling failed on attempt {attempt}: {e}")
            continue

        # Для 5xx продолжаем ждать, 4xx — ошибка
        if pr.status_code >= 500:
            logger.warning(f"BookAI polling returned {pr.status_code} on attempt {attempt}, keep waiting")
            continue
        if pr.status_code >= 400:
            raise HTTPException(pr.status_code, pr.text[:500])

        try:
            pdata = pr.json()
        except ValueError:
            logger.warning("BookAI polling returned non-JSON response, keep waiting")
            continue

        pstatus = str(pdata.get("status") or "").lower()
        if pstatus == "completed":
            return pdata
        if pstatus == "failed":
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, pdata.get("error_message") or "BookAI processing failed")

    raise HTTPException(status.HTTP_504_GATEWAY_TIMEOUT, "BookAI processing timeout")


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
    # Берём последние версии по каждому шаблону, чтобы не отдать старые URL
    items = (
        db.query(BookCreative)
        .filter_by(book_id=book_id, language=language)
        .order_by(BookCreative.updated_at.desc(), BookCreative.created_at.desc())
        .all()
    )
    latest_by_code = {}
    for x in items:
        if x.creative_code not in latest_by_code:
            latest_by_code[x.creative_code] = x
    ready = {code: x for code, x in latest_by_code.items() if x.status == CreativeStatus.READY}
    needed = {PLACID_TPL_V1, PLACID_TPL_V2, PLACID_TPL_V3}

    if not regen and needed.issubset(set(ready.keys())):
        ordered = _order_creatives_by_template([ready[code] for code in needed if code in ready])
        return {
            "items": [
                {
                    "code": x.creative_code,
                    "creative_code": x.creative_code,
                    "status": x.status.value,
                    "s3_url": x.s3_url or "",
                    "payload_used": x.payload_used or {},
                }
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
                {
                    "code": x.creative_code,
                    "creative_code": x.creative_code,
                    "status": x.status.value,
                    "s3_url": x.s3_url or "",
                    "payload_used": x.payload_used or {},
                }
                for x in ordered
            ],
            "overall": "ready",
        }
    except BookAIValidationError as e:
        logger.error("BookAI validation error in get_or_create_creatives")
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(e))
    except BookAIServiceUnavailableError as e:
        logger.error("BookAI service unavailable in get_or_create_creatives")
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(e))
    except PlacidQuotaError as e:
        logger.error("Placid quota error in get_or_create_creatives")
        # 402 Payment Required логичнее для недостатка кредитов
        raise HTTPException(status.HTTP_402_PAYMENT_REQUIRED, "Placid: Requires Subscription and Credits")
    except PlacidServiceError as e:
        logger.error("Placid service error in get_or_create_creatives")
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Placid error: {str(e)}")
    except ValueError as e:
        logger.error("ValueError in get_or_create_creatives")
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(e))
    except Exception as e:
        logger.error("Unexpected error in get_or_create_creatives", exc_info=True)
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
                {
                    "code": item.creative_code,
                    "creative_code": item.creative_code,
                    "status": item.status.value,
                    "s3_url": item.s3_url or "",
                    "payload_used": item.payload_used or {},
                }
            ],
            "overall": "ready",
        }
    except BookAIValidationError as e:
        logger.error("BookAI validation error in manual_single_creative")
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(e))
    except BookAIServiceUnavailableError as e:
        logger.error("BookAI service unavailable in manual_single_creative")
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(e))
    except PlacidQuotaError as e:
        logger.error("Placid quota error in manual_single_creative")
        raise HTTPException(status.HTTP_402_PAYMENT_REQUIRED, "Placid: Requires Subscription and Credits")
    except PlacidServiceError as e:
        logger.error("Placid service error in manual_single_creative")
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Placid error: {str(e)}")
    except ValueError as e:
        logger.error("ValueError in manual_single_creative")
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(e))
    except Exception as e:
        logger.error("Unexpected error in manual_single_creative", exc_info=True)
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
                {
                    "code": x.creative_code,
                    "creative_code": x.creative_code,
                    "status": x.status.value,
                    "s3_url": x.s3_url or "",
                    "payload_used": x.payload_used or {},
                }
                for x in ordered
            ],
            "overall": "ready",
        }
    except BookAIValidationError as e:
        logger.error("BookAI validation error in manual_creatives")
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(e))
    except BookAIServiceUnavailableError as e:
        logger.error("BookAI service unavailable in manual_creatives")
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(e))
    except PlacidQuotaError as e:
        logger.error("Placid quota error in manual_creatives")
        raise HTTPException(status.HTTP_402_PAYMENT_REQUIRED, "Placid: Requires Subscription and Credits")
    except PlacidServiceError as e:
        logger.error("Placid service error in manual_creatives")
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Placid error: {str(e)}")
    except ValueError as e:
        logger.error("ValueError in manual_creatives")
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(e))
    except Exception as e:
        logger.error("Unexpected error in manual_creatives", exc_info=True)
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Failed to generate creatives: {str(e)}")


