from typing import Optional, Dict, Any, List
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status, Path, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from celery.result import AsyncResult

from ..db.database import get_db
from ..dependencies.role_checker import require_roles
from ..models.models_v2 import Book, BookCreative, CreativeStatus, BookFile, BookFileFormat
from ..services_v2.creative_service import (
    generate_all_creatives, 
    generate_single_creative, 
    PLACID_TPL_V1, 
    PLACID_TPL_V2, 
    PLACID_TPL_V3,
    PLACID_TPL_V4,
    BookAIValidationError,
    BookAIServiceUnavailableError,
    PlacidQuotaError,
    PlacidServiceError,
)
from ..core.config import settings
from ..celery_app import celery
from ..tasks.creatives import get_active_task, set_active_task

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


class CreativeTaskResponse(BaseModel):
    """Ответ при постановке задачи на генерацию."""
    task_id: str
    status_url: str
    status: str = "queued"


class CreativeStatusResponse(BaseModel):
    """Ответ о статусе задачи генерации."""
    task_id: str
    state: str
    result: Optional[Dict[str, Any]] = None
    progress: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


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

    # Отправляем в BookAI ПОЛНУЮ версию PDF из BookFiles
    process_pdf_url = pdf.s3_url

    # Надёжный запуск процесса с ретраями на 5xx/таймауты (например, 524 от CDN)
    r = None
    post_max_attempts = 5
    post_interval_sec = 2
    for post_attempt in range(1, post_max_attempts + 1):
        try:
            r = requests.post(
                f"{settings.BOOKAI_BASE_URL}/process",
                json={"s3_url": process_pdf_url, "language": language, "book_id": book_id},
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
    """Упорядочивает креативы по шаблонам: v1, v2, v3,v4"""
    order = {PLACID_TPL_V1: 0, PLACID_TPL_V2: 1, PLACID_TPL_V3: 2, PLACID_TPL_V4: 3}
    return sorted(creatives, key=lambda x: order.get(x.creative_code, 999))


@router.get("/books/{book_id}/creatives")
def get_or_create_creatives(
    book_id: int,
    language: str = Query(..., description="Язык креатива (RU, EN, ES, PT, AR, IT)"),
    regen: bool = Query(False, description="Принудительно перегенерировать все креативы"),
    request: Request = None,
    db: Session = Depends(get_db),
    current_admin=Depends(require_roles("admin")),
):
    """
    Получить или создать креативы для книги (асинхронный режим).
    
    Возвращает:
    - Если креативы готовы и не требуется регенерация: 200 + CreativesResponse
    - Если требуется генерация: 202 + CreativeTaskResponse с task_id
    
    Для проверки статуса используйте GET /books/creatives/status/{task_id}
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
    needed = {PLACID_TPL_V1, PLACID_TPL_V2, PLACID_TPL_V3,PLACID_TPL_V4}

    # Если все креативы готовы и не требуется регенерация - возвращаем их
    if not regen and needed.issubset(set(ready.keys())):
        ordered = _order_creatives_by_template([ready[code] for code in needed if code in ready])
        return CreativesResponse(
            items=[
                CreativeItemResponse(
                    code=x.creative_code,
                    creative_code=x.creative_code,
                    status=x.status.value,
                    s3_url=x.s3_url or "",
                    payload_used=x.payload_used or {},
                )
                for x in ordered
            ],
            overall="ready",
        )

    # Нужна генерация - проверяем активную задачу
    existing_task_id = get_active_task(book_id, language)
    if existing_task_id:
        # Проверяем, действительно ли задача еще выполняется
        task_result = AsyncResult(existing_task_id, app=celery)
        if task_result.state in ("PENDING", "STARTED", "PROGRESS"):
            # Задача еще выполняется - возвращаем существующий task_id
            base = str(request.base_url).rstrip("/") if request else ""
            status_url = f"{base}/api/v2/books/creatives/status/{existing_task_id}"
            return CreativeTaskResponse(
                task_id=existing_task_id,
                status_url=status_url,
                status="processing" if task_result.state in ("STARTED", "PROGRESS") else "queued",
            )

    # Запускаем новую задачу
    try:
        task = celery.send_task(
            "app.tasks.creatives.generate_all_creatives_task",
            kwargs={"book_id": book_id, "language": language, "manual_payload": None},
            queue="book",
        )
        task_id = task.id
        
        # Сохраняем маппинг в Redis
        set_active_task(book_id, language, task_id)
        
        # Формируем URL статуса
        base = str(request.base_url).rstrip("/") if request else ""
        status_url = f"{base}/api/v2/books/creatives/status/{task_id}"
        
        logger.info(f"Started creative generation task {task_id} for book_id={book_id}, language={language}")
        
        response = CreativeTaskResponse(
            task_id=task_id,
            status_url=status_url,
            status="queued",
        )
        return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content=response.dict())
        
    except Exception as e:
        logger.error(f"Failed to enqueue creative generation task: {e}", exc_info=True)
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Failed to start generation task: {str(e)}")



@router.post("/books/{book_id}/creatives/manual/{target}")
def manual_single_creative(
    book_id: int,
    target: str = Path(
        ...,
        description=f"Целевой креатив для обновления: 'v1' | 'v2' | 'v3' или конкретный creative_code.\n"
                    f"Допустимые значения:\n"
                    f"- v1 (или {PLACID_TPL_V1})\n"
                    f"- v2 (или {PLACID_TPL_V2})\n"
                    f"- v3 (или {PLACID_TPL_V3})\n"
                    f"- v4 (или {PLACID_TPL_V4})"
    ),
    body: ManualCreativeFlexible = ...,
    request: Request = None,
    db: Session = Depends(get_db),
    current_admin=Depends(require_roles("admin")),
):
    """
    Ручная регенерация ОДНОГО креатива для книги (асинхронный режим).
    
    **target** - какой креатив обновить:
    - `v1` (или `kbhccvksoprg7`) - первый шаблон
    - `v2` (или `ktawlyumyeaw7`) - второй шаблон  
    - `v3` (или `uoshaoahss0al`) - третий шаблон
    - `v4` (или `9lzxp889n80qo`) - четвертый шаблон
    
    **body.fields** - словарь произвольных переопределений:
    - `price_new`, `price_old` - цены
    - `title` - название книги
    - `cover_url` - URL обложки
    - `texts` - словарь с текстовыми полями (hight_description, tag_1, tag_2, tag_3 и т.д.)
    - `layers` - полный словарь слоёв для Placid (если нужно полное переопределение)
    
    Возвращает:
    - 202 + CreativeTaskResponse с task_id для отслеживания
    
    Для проверки статуса используйте GET /books/creatives/status/{task_id}
    """
    overrides = body.fields or {}
    
    # Проверяем активную задачу для этого конкретного креатива
    existing_task_id = get_active_task(book_id, body.language, target)
    if existing_task_id:
        # Проверяем, действительно ли задача еще выполняется
        task_result = AsyncResult(existing_task_id, app=celery)
        if task_result.state in ("PENDING", "STARTED", "PROGRESS"):
            # Задача еще выполняется - возвращаем существующий task_id
            base = str(request.base_url).rstrip("/") if request else ""
            status_url = f"{base}/api/v2/books/creatives/status/{existing_task_id}"
            return JSONResponse(
                status_code=status.HTTP_202_ACCEPTED,
                content=CreativeTaskResponse(
                    task_id=existing_task_id,
                    status_url=status_url,
                    status="processing" if task_result.state in ("STARTED", "PROGRESS") else "queued",
                ).dict()
            )
    
    # Запускаем новую задачу
    try:
        task = celery.send_task(
            "app.tasks.creatives.generate_single_creative_task",
            kwargs={
                "book_id": book_id,
                "language": body.language,
                "target": target,
                "overrides": overrides,
            },
            queue="book",
        )
        task_id = task.id
        
        # Сохраняем маппинг в Redis
        set_active_task(book_id, body.language, task_id, target=target)
        
        # Формируем URL статуса
        base = str(request.base_url).rstrip("/") if request else ""
        status_url = f"{base}/api/v2/books/creatives/status/{task_id}"
        
        logger.info(f"Started single creative generation task {task_id} for book_id={book_id}, language={body.language}, target={target}")
        
        response = CreativeTaskResponse(
            task_id=task_id,
            status_url=status_url,
            status="queued",
        )
        return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content=response.dict())
        
    except Exception as e:
        logger.error(f"Failed to enqueue single creative generation task: {e}", exc_info=True)
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Failed to start generation task: {str(e)}")

@router.post("/books/{book_id}/creatives/manual")
def manual_creatives(
    book_id: int,
    body: ManualCreatives,
    request: Request = None,
    db: Session = Depends(get_db),
    current_admin=Depends(require_roles("admin")),
):
    """
    Ручная регенерация всех креативов (v1 и v2) для книги (асинхронный режим).
    
    Обновляет креативы v1 и v2 одновременно, если переданы соответствующие данные.
    Креатив v3 генерируется автоматически без ручных данных.
    
    Возвращает:
    - 202 + CreativeTaskResponse с task_id для отслеживания
    
    Для проверки статуса используйте GET /books/creatives/status/{task_id}
    """
    mp: Dict[str, Dict] = {}
    if body.v1:
        mp["v1"] = body.v1.dict(exclude_none=True)
    if body.v2:
        mp["v2"] = body.v2.dict(exclude_none=True)
    
    # Проверяем активную задачу
    existing_task_id = get_active_task(book_id, body.language)
    if existing_task_id:
        # Проверяем, действительно ли задача еще выполняется
        task_result = AsyncResult(existing_task_id, app=celery)
        if task_result.state in ("PENDING", "STARTED", "PROGRESS"):
            # Задача еще выполняется - возвращаем существующий task_id
            base = str(request.base_url).rstrip("/") if request else ""
            status_url = f"{base}/api/v2/books/creatives/status/{existing_task_id}"
            return JSONResponse(
                status_code=status.HTTP_202_ACCEPTED,
                content=CreativeTaskResponse(
                    task_id=existing_task_id,
                    status_url=status_url,
                    status="processing" if task_result.state in ("STARTED", "PROGRESS") else "queued",
                ).dict()
            )
    
    # Запускаем новую задачу
    try:
        task = celery.send_task(
            "app.tasks.creatives.generate_all_creatives_task",
            kwargs={
                "book_id": book_id,
                "language": body.language,
                "manual_payload": mp or None,
            },
            queue="book",
        )
        task_id = task.id
        
        # Сохраняем маппинг в Redis
        set_active_task(book_id, body.language, task_id)
        
        # Формируем URL статуса
        base = str(request.base_url).rstrip("/") if request else ""
        status_url = f"{base}/api/v2/books/creatives/status/{task_id}"
        
        logger.info(f"Started manual creative generation task {task_id} for book_id={book_id}, language={body.language}")
        
        response = CreativeTaskResponse(
            task_id=task_id,
            status_url=status_url,
            status="queued",
        )
        return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content=response.dict())
        
    except Exception as e:
        logger.error(f"Failed to enqueue manual creative generation task: {e}", exc_info=True)
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Failed to start generation task: {str(e)}")


@router.get("/books/creatives/status/{task_id}")
def get_creative_status(
    task_id: str,
    current_admin=Depends(require_roles("admin")),
):
    """
    Проверка статуса задачи генерации креативов.
    
    Возвращает:
    - `status: "queued"` - задача в очереди
    - `status: "processing"` - задача выполняется (с полем progress)
    - `status: "done"` - задача завершена (с полем items и overall)
    - `status: "error"` - произошла ошибка (с полем error)
    """
    result = AsyncResult(task_id, app=celery)
    state = result.state
    
    if state == "PENDING":
        return CreativeStatusResponse(
            task_id=task_id,
            state="queued",
        )
    
    if state in ("STARTED", "PROGRESS"):
        meta = result.info if isinstance(result.info, dict) else {}
        return CreativeStatusResponse(
            task_id=task_id,
            state="processing",
            progress=meta,
        )
    
    if state == "SUCCESS":
        data = result.get(propagate=False)
        
        # Проверяем формат результата
        if isinstance(data, dict):
            if data.get("status") == "success":
                # Успешная генерация - возвращаем креативы
                items = data.get("items", [])
                return {
                    "task_id": task_id,
                    "state": "done",
                    "result": {
                        "items": items,
                        "overall": "ready",
                    }
                }
            elif data.get("status") == "error":
                # Ошибка в процессе генерации
                error_type = data.get("error_type", "general")
                error_msg = data.get("error", "Unknown error")
                
                # Формируем понятное сообщение об ошибке
                return CreativeStatusResponse(
                    task_id=task_id,
                    state="error",
                    error=f"{error_type}: {error_msg}",
                )
        
        # Неожиданный формат результата
        return CreativeStatusResponse(
            task_id=task_id,
            state="done",
            result=data,
        )
    
    if state == "FAILURE":
        err = str(result.info) if result.info else "Unknown error"
        return CreativeStatusResponse(
            task_id=task_id,
            state="error",
            error=err,
        )
    
    # Прочие нестандартные статусы
    meta = result.info if isinstance(result.info, dict) else {}
    return CreativeStatusResponse(
        task_id=task_id,
        state=state.lower(),
        progress=meta,
    )


