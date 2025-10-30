import io
import json
import logging
import re
import time
from typing import Optional, Dict, Any, Tuple

import requests
from sqlalchemy.orm import Session

from ..core.config import settings
from ..models.models_v2 import Book, BookLanding, BookCreative, CreativeStatus

logger = logging.getLogger(__name__)


PLACID_TPL_V1 = "kbhccvksoprg7"
PLACID_TPL_V2 = "ktawlyumyeaw7"
PLACID_TPL_V3 = "uoshaoahss0al"


def _only_for_text(lang: str) -> str:
    m = {
        "EN": "only |FOR|",
        "RU": "Только |ЗА|",
        "ES": "Solo |POR|",
        "PT": "Só |POR|",
        "AR": "فقط |بـ|",
        "IT": "Solo |A|",
    }
    return m.get(lang.upper(), "only |FOR|")


def _format_price(amount: Optional[float]) -> str:
    if amount is None:
        return ""
    # всегда доллар
    if float(amount).is_integer():
        return f"${int(amount)}"
    return f"${amount:.2f}"


def _min_price_landing(db: Session, book_id: int, language: str) -> Optional[BookLanding]:
    # выбираем BookLanding, где присутствует книга и язык совпадает; берем с минимальной new_price
    q = (
        db.query(BookLanding)
        .join(BookLanding.books)
        .filter(Book.id == book_id, BookLanding.language == language)
        .order_by(BookLanding.new_price.asc())
    )
    return q.first()


def _build_layers_v1(book: Book, lang: str, texts: Dict[str, str], price_old: str, price_new: str) -> Dict[str, Any]:
    return {
        "template_uuid": PLACID_TPL_V1,
        "layers": {
            "Main_book_image": {"media": book.cover_url},
            "Back_book_image": {"media": book.cover_url},
            "Iphone_image":{"media": book.cover_url},
            "Book_name": {"text": book.title},
            "Tag_1": {"text": texts.get("tag_1", "")},
            "Tag_2": {"text": texts.get("tag_2", "")},
            "Tag_3": {"text": texts.get("tag_3", "")},
            "Hight_description": {"text": texts.get("hight_description", "")},
            "Medium_description": {"text": texts.get("medium_description", "")},
            "Down_description": {"text": texts.get("down_description", "")},
            "Only_for_text": {"text": _only_for_text(lang)},
            "New_price": {"text": price_new},
            "Old_price": {"text": price_old},
        },
    }


def _build_layers_v2(book: Book, lang: str, texts: Dict[str, str], price_old: str, price_new: str) -> Dict[str, Any]:
    return {
        "template_uuid": PLACID_TPL_V2,
        "layers": {
            "Book_1_cover": {"media": book.cover_url},
            "Book_2_cover": {"media": book.cover_url},
            "Book_name": {"text": book.title},
            "Tag_1": {"text": texts.get("tag_1", "")},
            "Tag_2": {"text": texts.get("tag_2", "")},
            "Tag_3": {"text": texts.get("tag_3", "")},
            "Hight_description": {"text": texts.get("hight_description", "")},
            "Down_description": {"text": texts.get("down_description", "")},
            "Only_for": {"text": _only_for_text(lang)},
            "Old_price": {"text": price_old},
            "New_price": {"text": price_new},
        },
    }


def _build_layers_v3(book: Book, lang: str, price_old: str, price_new: str) -> Dict[str, Any]:
    return {
        "template_uuid": PLACID_TPL_V3,
        "layers": {
            "Book_cover": {"media": book.cover_url},
            "Ipad_screen": {"media": book.cover_url},
            "Iphone_screen": {"media": book.cover_url},
            "Formats": {"text": "* — PDF, EPUB, MOBI, AZW3, FB2"},
            "Button_text": {"text": "Download right now"},
            "Title": {"text": "All formats available"},
            "New_price": {"text": price_new},
            "Only_for": {"text": _only_for_text(lang)},
            "Old_price": {"text": price_old},
        },
    }


def _placid_render(payload: Dict[str, Any]) -> Tuple[str, Optional[str]]:
    """Рендерит изображение через Placid API. Обрабатывает статусы queued/processing с polling."""
    # Логируем image/media URLs для отладки проблем с обложками
    layers = payload.get("layers", {})
    image_layers = {}
    for k, v in layers.items():
        if isinstance(v, dict):
            # Проверяем оба ключа - "image" и "media"
            image_url = v.get("image") or v.get("media")
            if image_url:
                image_layers[k] = image_url
    if image_layers:
        logger.info(f"Placid payload image/media URLs: {image_layers}")
    
    try:
        # Ретраи на 5xx/таймауты для POST /images (например, 524 от CDN)
        post_max_attempts = 5
        post_interval_sec = 2
        r = None
        for post_attempt in range(1, post_max_attempts + 1):
            try:
                r = requests.post(
                    f"{settings.PLACID_BASE_URL}/images",
                    headers={
                        "Authorization": f"Bearer {settings.PLACID_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    data=json.dumps(payload),
                    timeout=90,
                )
            except requests.exceptions.RequestException as e:
                logger.warning(f"Placid API /images request failed on attempt {post_attempt}: {e}")
                if post_attempt == post_max_attempts:
                    return "", f"placid request error: {str(e)}"
                time.sleep(post_interval_sec)
                continue

            if r.status_code >= 500:
                logger.warning(f"Placid API /images returned {r.status_code} on attempt {post_attempt}")
                if post_attempt == post_max_attempts:
                    logger.error(f"Placid API error {r.status_code}: {r.text[:500]}")
                    return "", f"placid {r.status_code}: {r.text[:500]}"
                time.sleep(post_interval_sec)
                continue
            if r.status_code >= 400:
                logger.error(f"Placid API error {r.status_code}: {r.text[:500]}")
                return "", f"placid {r.status_code}: {r.text[:500]}"
            break
        try:
            data = r.json()
        except (ValueError, json.JSONDecodeError) as e:
            logger.error(f"Placid API invalid JSON response: {e}, response text: {r.text[:500]}")
            return "", f"placid: invalid json response - {str(e)}"
        
        # Проверяем наличие ошибок или warnings в ответе
        errors = data.get("errors", [])
        if errors:
            logger.warning(f"Placid API returned errors in response: {errors}")
        
        # Проверяем статус ответа
        status = data.get("status", "").lower()
        image_id = data.get("id")
        polling_url = data.get("polling_url")
        
        logger.info(f"Placid API initial response: id={image_id}, status={status}, errors={len(errors) if errors else 0}")
        
        # Функция для извлечения URL из ответа Placid
        def _extract_url(response_data: Dict) -> Optional[str]:
            """Извлекает URL изображения из ответа Placid API."""
            # Проверяем различные возможные поля с URL в порядке приоритета
            # Проверяем image_url в первую очередь (приоритет для Placid API)
            url = response_data.get("image_url")
            if url and isinstance(url, str) and url.strip():
                logger.debug(f"Found image_url in response: {url[:50]}...")
                return url.strip()
            
            url = response_data.get("url")
            if url and isinstance(url, str) and url.strip():
                logger.debug(f"Found url in response: {url[:50]}...")
                return url.strip()
                
            url = response_data.get("transfer_url")
            if url and isinstance(url, str) and url.strip():
                logger.debug(f"Found transfer_url in response: {url[:50]}...")
                return url.strip()
            
            # Проверяем вложенный объект data
            data_obj = response_data.get("data")
            if isinstance(data_obj, dict):
                url = data_obj.get("image_url") or data_obj.get("url")
                if url and isinstance(url, str) and url.strip():
                    logger.debug(f"Found url in data object: {url[:50]}...")
                    return url.strip()
            
            return None
        
        # Если изображение готово сразу (completed или finished)
        if status in ("completed", "finished"):
            url = _extract_url(data)
            if url:
                logger.info(f"Placid image {image_id} ready immediately with status: {status}")
                return url, None
            else:
                logger.warning(f"Placid image {image_id} status {status} but no URL found, trying polling_url")
                # Если нет URL, но есть polling_url - используем его для получения URL
                if polling_url:
                    # Делаем один запрос к polling_url для получения URL
                    try:
                        poll_r = requests.get(
                            polling_url,
                            headers={"Authorization": f"Bearer {settings.PLACID_API_KEY}"},
                            timeout=30,
                        )
                        if poll_r.status_code < 300:
                            poll_data = poll_r.json()
                            url = _extract_url(poll_data)
                            if url:
                                logger.info(f"Placid image {image_id} URL obtained via polling_url for status {status}")
                                return url, None
                    except Exception as e:
                        logger.warning(f"Failed to get URL via polling_url for finished image: {e}")
                
                logger.error(f"Placid image {image_id} status {status} but no URL and polling failed: {data}")
                return "", f"placid: no url for status {status}"
        
        # Если в очереди или обрабатывается - делаем polling
        if status in ("queued", "processing") and polling_url:
            logger.info(f"Placid image {image_id} is {status}, polling for completion...")
            max_attempts = 120  # максимум 120 попыток
            poll_interval = 2   # каждые 2 секунды (итого до ~4 минут)
            
            for attempt in range(1, max_attempts + 1):
                time.sleep(poll_interval)
                try:
                    poll_r = requests.get(
                        polling_url,
                        headers={"Authorization": f"Bearer {settings.PLACID_API_KEY}"},
                        timeout=30,
                    )
                    if poll_r.status_code >= 300:
                        logger.warning(f"Placid polling error {poll_r.status_code} on attempt {attempt}")
                        continue
                    
                    poll_data = poll_r.json()
                    poll_status = poll_data.get("status", "").lower()
                    poll_errors = poll_data.get("errors", [])
                    
                    # Логируем ошибки если есть (часто там указываются проблемы с загрузкой изображений)
                    if poll_errors:
                        for error in poll_errors:
                            error_msg = error.get("message", "") if isinstance(error, dict) else str(error)
                            logger.warning(f"Placid image {image_id} polling error on attempt {attempt}: {error_msg}")
                            # Если ошибка связана с изображением, детально логируем
                            if "image" in error_msg.lower() or "media" in error_msg.lower() or "file" in error_msg.lower():
                                logger.error(f"Placid image loading error details: {error}")
                    
                    # Если изображение готово (completed или finished)
                    if poll_status in ("completed", "finished"):
                        url = _extract_url(poll_data)
                        if url:
                            if poll_errors:
                                logger.warning(f"Placid image {image_id} completed with errors (warnings): {poll_errors}")
                            logger.info(f"Placid image {image_id} completed (status: {poll_status}) after {attempt} polling attempts, URL: {url}")
                            return url, None
                        else:
                            # Детальное логирование для отладки
                            logger.warning(
                                f"Placid image {image_id} status {poll_status} but no URL extracted. "
                                f"Response keys: {list(poll_data.keys())}, "
                                f"image_url={poll_data.get('image_url')}, "
                                f"url={poll_data.get('url')}, "
                                f"transfer_url={poll_data.get('transfer_url')}"
                            )
                            # Если статус finished и нет URL после нескольких попыток - это ошибка
                            if attempt >= 3:  # После 3 попыток считаем это ошибкой
                                logger.error(f"Placid image {image_id} finished but no URL found after {attempt} attempts")
                                return "", f"placid: finished status but no URL in response after {attempt} attempts"
                            continue
                    
                    elif poll_status in ("queued", "processing"):
                        logger.debug(f"Placid image {image_id} still {poll_status}, attempt {attempt}/{max_attempts}")
                        continue
                    else:
                        # Ошибка или неизвестный статус
                        errors = poll_data.get("errors", [])
                        error_msg = f"Placid image {image_id} status: {poll_status}"
                        if errors:
                            error_msg += f", errors: {errors}"
                        logger.error(error_msg)
                        return "", f"placid: unexpected status {poll_status}"
                        
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Placid polling request failed on attempt {attempt}: {e}")
                    continue
            
            # Исчерпаны попытки
            logger.error(f"Placid image {image_id} polling timeout after {max_attempts} attempts")
            return "", f"placid: polling timeout (image still {status} after {max_attempts * poll_interval}s)"
        
        # Статус unknown или нет polling_url - пытаемся извлечь URL
        url = _extract_url(data)
        if not url:
            logger.error(f"Placid API empty url in response (status={status}): {data}")
            return "", f"placid: empty url (status={status})"
        return url, None
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Placid API request failed: {e}")
        return "", f"placid request error: {str(e)}"


class BookAIServiceError(Exception):
    """Базовое исключение для ошибок BookAI сервиса."""
    pass


class BookAIValidationError(BookAIServiceError):
    """Ошибка валидации данных (400, 422) - должна возвращать 422."""
    pass


class BookAIServiceUnavailableError(BookAIServiceError):
    """Сервис недоступен (502, 503, timeout) - должна возвращать 502."""
    pass


class PlacidServiceError(Exception):
    """Базовая ошибка для Placid рендеринга."""
    pass


class PlacidQuotaError(PlacidServiceError):
    """Недостаточно подписки/кредитов в Placid (403 Requires Subscription and Credits)."""
    pass


def _clean_creative_text(text: str) -> str:
    """Очищает текст от артефактов валидации типа '(60 chars.)' в конце."""
    if not text:
        return text
    
    # Удаляем паттерны типа "(60 chars.)", "(120 chars)", " (chars.)" и подобные в конце текста
    text = re.sub(r'\s*\([^)]*chars[^)]*\)\s*$', '', text, flags=re.IGNORECASE)
    return text.strip()


def _bookai_texts(db: Session, book_id: int, language: str, version: int) -> Dict[str, str]:
    """Получает тексты для креатива через BookAI API, используя PDF файл книги."""
    from ..models.models_v2 import BookFile, BookFileFormat
    
    # Получаем PDF файл книги
    pdf = (
        db.query(BookFile)
        .filter(BookFile.book_id == book_id, BookFile.file_format == BookFileFormat.PDF)
        .first()
    )
    if not pdf:
        raise ValueError("No source PDF for the book")
    
    s3_url = pdf.s3_url
    if not s3_url:
        raise ValueError("PDF file has no s3_url")
    
    endpoint = "/creative/generate-v2" if version == 2 else "/creative/generate"
    url = f"{settings.BOOKAI_BASE_URL}{endpoint}"
    logger.info(f"BookAI request: {url} book_id={book_id} lang={language}")
    
    try:
        r = requests.post(
            url,
            json={"s3_url": s3_url, "language": language},
            timeout=90,
        )
        if r.status_code == 400:
            raise BookAIValidationError("bookai validation error (400)")
        if r.status_code == 422:
            raise BookAIValidationError("bookai validation error (422)")
        if r.status_code >= 500:
            raise BookAIServiceUnavailableError(f"bookai service error ({r.status_code})")
        r.raise_for_status()
        try:
            texts = r.json()
            cleaned_texts = {}
            for key, value in texts.items():
                if isinstance(value, str):
                    cleaned_texts[key] = _clean_creative_text(value)
                else:
                    cleaned_texts[key] = value
            return cleaned_texts
        except (ValueError, json.JSONDecodeError) as e:
            raise BookAIServiceUnavailableError("bookai invalid json response")
            
    except BookAIServiceError:
        raise  # Перебрасываем специальные исключения как есть
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response else None
        logger.error(f"BookAI HTTP error {status_code}")
        if status_code and status_code >= 500:
            raise BookAIServiceUnavailableError(f"bookai http error ({status_code})")
        else:
            raise BookAIValidationError(f"bookai http error ({status_code})")
            
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        logger.error("BookAI connection/timeout error")
        raise BookAIServiceUnavailableError("bookai service unavailable")
        
    except requests.exceptions.RequestException as e:
        logger.error("BookAI request failed")
        raise BookAIServiceUnavailableError("bookai request error")


def _download_bytes(url: str) -> bytes:
    # Часто URL становится доступен не сразу — делаем ретраи
    max_attempts = 10
    interval_sec = 1
    last_err: Optional[Exception] = None
    for attempt in range(1, max_attempts + 1):
        try:
            r = requests.get(url, timeout=120)
            if r.status_code >= 500:
                logger.warning(f"Download {url} returned {r.status_code} on attempt {attempt}")
                last_err = RuntimeError(f"server error {r.status_code}")
            elif r.status_code >= 400:
                # Для 4xx тоже попробуем несколько раз — ресурс может ещё не прогрессировал у CDN
                logger.warning(f"Download {url} returned {r.status_code} on attempt {attempt}")
                last_err = RuntimeError(f"client error {r.status_code}")
            else:
                return r.content
        except requests.exceptions.RequestException as e:
            logger.warning(f"Download {url} failed on attempt {attempt}: {e}")
            last_err = e
        time.sleep(interval_sec)
    logger.error(f"Failed to download image from {url} after {max_attempts} attempts: {last_err}")
    raise RuntimeError(f"Failed to download image: {str(last_err) if last_err else 'unknown error'}")


def _upload_image_to_placid(image_url: str) -> Optional[Dict[str, str]]:
    """
    Загружает изображение в Placid через Upload Media API.
    Возвращает словарь с file_key и file_id.
    
    Returns:
        Словарь с ключами "file_key" и "file_id" или None в случае ошибки
    """
    try:
        # Скачиваем изображение
        logger.info(f"Downloading image for Placid upload: {image_url[:100]}...")
        image_data = _download_bytes(image_url)
        
        # Определяем расширение файла из URL или content-type
        import mimetypes
        content_type = mimetypes.guess_type(image_url)[0] or "image/jpeg"
        
        # Используем уникальное имя файла для загрузки
        import uuid
        file_key = f"cover_{uuid.uuid4().hex[:8]}"
        filename = f"{file_key}.jpg"
        
        # Подготовка файла для загрузки
        files = {
            file_key: (filename, image_data, content_type)
        }
        
        # Загружаем в Placid
        logger.info(f"Uploading image to Placid Media API with file_key={file_key}...")
        r = requests.post(
            f"{settings.PLACID_BASE_URL}/media",
            headers={
                "Authorization": f"Bearer {settings.PLACID_API_KEY}",
            },
            files=files,
            timeout=120,
        )
        
        logger.info(f"Placid Media API response status: {r.status_code}")
        
        if r.status_code >= 300:
            logger.error(f"Placid Media upload error {r.status_code}: {r.text[:500]}")
            return None
        
        try:
            response_data = r.json()
            logger.info(f"Placid Media API full response: {response_data}")
            
            media_list = response_data.get("media", [])
            if media_list and len(media_list) > 0:
                # Ищем элемент с нашим file_key
                media_item = None
                for item in media_list:
                    if item.get("file_key") == file_key:
                        media_item = item
                        break
                
                # Если не нашли по ключу, берем первый
                if not media_item:
                    media_item = media_list[0]
                
                file_id = media_item.get("file_id")
                returned_file_key = media_item.get("file_key")
                
                logger.info(f"Placid Media response: file_key={returned_file_key}, file_id={file_id}")
                
                if file_id:
                    logger.info(f"Image uploaded to Placid successfully, file_key={returned_file_key}, file_id: {file_id}")
                    return {
                        "file_key": returned_file_key,
                        "file_id": file_id
                    }
                else:
                    logger.error(f"Placid Media API returned no file_id in response: {response_data}")
                    return None
            else:
                logger.error(f"Placid Media API returned empty media array: {response_data}")
                return None
        except (ValueError, json.JSONDecodeError) as e:
            logger.error(f"Placid Media API invalid JSON response: {e}, response text: {r.text[:500]}")
            return None
            
    except Exception as e:
        logger.error(f"Failed to upload image to Placid: {e}", exc_info=True)
        return None


def _ensure_placid_media_url(cover_url: str) -> str:
    """
    Гарантирует, что изображение доступно для Placid.
    Загружает изображение через Placid Upload Media API для надежности.
    
    Args:
        cover_url: Исходный URL обложки
        
    Returns:
        file_id (URL от Placid) для использования в слоях как "media" или "image"
        В Placid используется либо прямой URL, либо file_id от Upload Media API
    """
    # Всегда загружаем через Placid Upload Media для гарантии доступа
    media_info = _upload_image_to_placid(cover_url)
    
    if media_info and media_info.get("file_id"):
        # Используем file_id (URL от Placid) - он должен работать
        file_id = media_info["file_id"]
        logger.info(f"Using Placid file_id: {file_id}")
        return file_id
    else:
        # Fallback: используем оригинальный URL (может не сработать, но попробуем)
        logger.warning(f"Failed to upload to Placid Media, using original URL as fallback: {cover_url}")
        return cover_url


def _s3_key(book_id: int, code: str) -> str:
    """Генерирует S3 ключ для креатива с уникальным именем (book_id + код шаблона)."""
    return f"books/{book_id}/creatives/{book_id}_{code}.png"


def _upload_to_s3(key: str, data: bytes) -> str:
    # используем такой же подход как в api_v2/media.py
    import os
    import boto3
    from botocore.config import Config
    S3_ENDPOINT = os.getenv("S3_ENDPOINT", "https://s3.timeweb.com")
    S3_BUCKET = os.getenv("S3_BUCKET", "cdn.dent-s.com")
    S3_REGION = os.getenv("S3_REGION", "ru-1")
    S3_PUBLIC_HOST = os.getenv("S3_PUBLIC_HOST", "https://cdn.dent-s.com")

    s3 = boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        region_name=S3_REGION,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        config=Config(signature_version="s3", s3={"addressing_style": "path"}),
    )
    # Агрессивно отключаем кэш у CDN/браузера для предотвращения отдачи старых версий
    from datetime import datetime, timezone
    cache_control = "no-cache, no-store, must-revalidate, max-age=0"
    expires_dt = datetime.now(timezone.utc)

    s3.upload_fileobj(
        io.BytesIO(data),
        S3_BUCKET,
        key,
        ExtraArgs={
            "ACL": "public-read",
            "ContentType": "image/png",
            "CacheControl": cache_control,
            "Expires": expires_dt,
        },
    )

    # Добавляем cache-busting параметр, чтобы обойти CDN кеш по тому же ключу
    version = int(time.time())
    return f"{S3_PUBLIC_HOST}/{key}?v={version}"


def _require_book_fields(book: Book) -> None:
    if not book.title:
        raise ValueError("Book.title is required")
    if not book.cover_url:
        raise ValueError("Book.cover_url is required")


def generate_creative_v1(
    db: Session,
    book: Book,
    language: str,
    texts: Optional[Dict[str, str]],
    context_overrides: Optional[Dict[str, Any]] = None,
) -> BookCreative:
    try:
        _require_book_fields(book)
        bl = _min_price_landing(db, book.id, language)
        if not bl or bl.new_price is None:
            raise ValueError("Price not found in book_landings")
        price_new = _format_price(float(bl.new_price))
        price_old = _format_price(float(bl.old_price or 0))

        # Применяем переопределения цен/полей при наличии
        ov = context_overrides or {}
        if "price_new" in ov:
            try:
                price_new = _format_price(float(ov.get("price_new")))
            except Exception:
                price_new = str(ov.get("price_new"))
        if "price_old" in ov:
            try:
                price_old = _format_price(float(ov.get("price_old")))
            except Exception:
                price_old = str(ov.get("price_old"))

        # Позволяем переопределить титул/обложку/слои
        title = ov.get("title", book.title)
        cover_url = ov.get("cover_url", book.cover_url)
        
        if not cover_url:
            raise ValueError("Book cover_url is required for creative generation")
        
        logger.info(f"Using cover_url for creative v1, book_id={book.id}, cover_url={cover_url[:100]}...")
        
        # Загружаем изображение в Placid для гарантированного доступа
        placid_media_url = _ensure_placid_media_url(cover_url)
        logger.info(f"Placid media URL for creative v1: {placid_media_url[:100]}...")
        
        layers_override = ov.get("layers") if ov else None

        # Если не переданы слои, но нужны тексты — генерируем их через BookAI
        if texts is None and not (layers_override and isinstance(layers_override, dict)):
            logger.info(f"Generating texts for creative v1, book_id={book.id}, language={language}")
            texts = _bookai_texts(db, book.id, language, version=1)

        if layers_override and isinstance(layers_override, dict):
            payload = {"template_uuid": PLACID_TPL_V1, "layers": layers_override}
        else:
            payload = {
                "template_uuid": PLACID_TPL_V1,
                "layers": {
                    "Main_book_image": {"image": placid_media_url},
                    "Back_book_image": {"image": placid_media_url},
                    "Iphone_image":{"image": placid_media_url},
                    "Book_name": {"text": title},
                    "Tag_1": {"text": texts.get("tag_1", "")},
                    "Tag_2": {"text": texts.get("tag_2", "")},
                    "Tag_3": {"text": texts.get("tag_3", "")},
                    "Hight_description": {"text": texts.get("hight_description", "")},
                    "Medium_description": {"text": texts.get("medium_description", "")},
                    "Down_description": {"text": texts.get("down_description", "")},
                    "Only_for_text": {"text": _only_for_text(language)},
                    "New_price": {"text": price_new},
                    "Old_price": {"text": price_old},
                },
            }
        logger.info(f"Rendering creative v1 via Placid, book_id={book.id}")
        url, err = _placid_render(payload)
        if err:
            # Определяем исчерпание кредитов/отсутствие подписки
            msg = str(err)
            if "Requires Subscription and Credits" in msg or "placid 403" in msg:
                raise PlacidQuotaError(msg)
            raise PlacidServiceError(msg)
        logger.info(f"Downloading image from Placid, book_id={book.id}")
        img = _download_bytes(url)
        key = _s3_key(book.id, PLACID_TPL_V1)
        logger.info(f"Uploading creative v1 to S3, book_id={book.id}, key={key}")
        s3_url = _upload_to_s3(key, img)

        existing = (
            db.query(BookCreative)
            .filter(
                BookCreative.book_id == book.id,
                BookCreative.language == language,
                BookCreative.creative_code == PLACID_TPL_V1,
            )
            .first()
        )
        if existing:
            existing.status = CreativeStatus.READY
            existing.placid_image_url = url
            existing.s3_key = key
            existing.s3_url = s3_url
            existing.payload_used = {"layers": payload.get("layers", {})}
            row = existing
        else:
            row = BookCreative(
                book_id=book.id,
                language=language,
                creative_code=PLACID_TPL_V1,
                status=CreativeStatus.READY,
                placid_image_url=url,
                s3_key=key,
                s3_url=s3_url,
                payload_used={"layers": payload.get("layers", {})},
            )
            db.add(row)
        db.commit()
        logger.info(f"Creative v1 generated successfully, book_id={book.id}")
        return row
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to generate creative v1 for book_id={book.id}, language={language}: {e}", exc_info=True)
        raise


def generate_creative_v2(
    db: Session,
    book: Book,
    language: str,
    texts: Optional[Dict[str, str]],
    context_overrides: Optional[Dict[str, Any]] = None,
) -> BookCreative:
    try:
        _require_book_fields(book)
        bl = _min_price_landing(db, book.id, language)
        if not bl or bl.new_price is None:
            raise ValueError("Price not found in book_landings")
        price_new = _format_price(float(bl.new_price))
        price_old = _format_price(float(bl.old_price or 0))

        # Применяем переопределения цен/полей при наличии
        ov = context_overrides or {}
        if "price_new" in ov:
            try:
                price_new = _format_price(float(ov.get("price_new")))
            except Exception:
                price_new = str(ov.get("price_new"))
        if "price_old" in ov:
            try:
                price_old = _format_price(float(ov.get("price_old")))
            except Exception:
                price_old = str(ov.get("price_old"))

        # Позволяем переопределить титул/обложку/слои
        title = ov.get("title", book.title)
        cover_url = ov.get("cover_url", book.cover_url)
        
        if not cover_url:
            raise ValueError("Book cover_url is required for creative generation")
        
        logger.info(f"Using cover_url for creative v2, book_id={book.id}, cover_url={cover_url[:100]}...")
        
        # Загружаем изображение в Placid для гарантированного доступа
        placid_media_url = _ensure_placid_media_url(cover_url)
        logger.info(f"Placid media URL for creative v2: {placid_media_url[:100]}...")
        
        layers_override = ov.get("layers") if ov else None

        # Если не переданы слои, но нужны тексты — генерируем их через BookAI
        if texts is None and not (layers_override and isinstance(layers_override, dict)):
            logger.info(f"Generating texts for creative v2, book_id={book.id}, language={language}")
            texts = _bookai_texts(db, book.id, language, version=2)

        if layers_override and isinstance(layers_override, dict):
            payload = {"template_uuid": PLACID_TPL_V2, "layers": layers_override}
        else:
            payload = {
                "template_uuid": PLACID_TPL_V2,
                "layers": {
                    "Book_1_cover": {"image": placid_media_url},
                    "Book_2_cover": {"image": placid_media_url},
                    "Book_name": {"text": title},
                    "Tag_1": {"text": texts.get("tag_1", "")},
                    "Tag_2": {"text": texts.get("tag_2", "")},
                    "Tag_3": {"text": texts.get("tag_3", "")},
                    "Hight_description": {"text": texts.get("hight_description", "")},
                    "Down_description": {"text": texts.get("down_description", "")},
                    "Only_for": {"text": _only_for_text(language)},
                    "Old_price": {"text": price_old},
                    "New_price": {"text": price_new},
                },
            }
        logger.info(f"Rendering creative v2 via Placid, book_id={book.id}")
        url, err = _placid_render(payload)
        if err:
            msg = str(err)
            if "Requires Subscription and Credits" in msg or "placid 403" in msg:
                raise PlacidQuotaError(msg)
            raise PlacidServiceError(msg)
        logger.info(f"Downloading image from Placid, book_id={book.id}")
        img = _download_bytes(url)
        key = _s3_key(book.id, PLACID_TPL_V2)
        logger.info(f"Uploading creative v2 to S3, book_id={book.id}, key={key}")
        s3_url = _upload_to_s3(key, img)

        existing = (
            db.query(BookCreative)
            .filter(
                BookCreative.book_id == book.id,
                BookCreative.language == language,
                BookCreative.creative_code == PLACID_TPL_V2,
            )
            .first()
        )
        if existing:
            existing.status = CreativeStatus.READY
            existing.placid_image_url = url
            existing.s3_key = key
            existing.s3_url = s3_url
            existing.payload_used = {"layers": payload.get("layers", {})}
            row = existing
        else:
            row = BookCreative(
                book_id=book.id,
                language=language,
                creative_code=PLACID_TPL_V2,
                status=CreativeStatus.READY,
                placid_image_url=url,
                s3_key=key,
                s3_url=s3_url,
                payload_used={"layers": payload.get("layers", {})},
            )
            db.add(row)
        db.commit()
        logger.info(f"Creative v2 generated successfully, book_id={book.id}")
        return row
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to generate creative v2 for book_id={book.id}, language={language}: {e}", exc_info=True)
        raise


def generate_creative_v3(
    db: Session,
    book: Book,
    language: str,
    context_overrides: Optional[Dict[str, Any]] = None,
) -> BookCreative:
    try:
        _require_book_fields(book)
        bl = _min_price_landing(db, book.id, language)
        if not bl or bl.new_price is None:
            raise ValueError("Price not found in book_landings")
        price_new = _format_price(float(bl.new_price))
        price_old = _format_price(float(bl.old_price or 0))

        ov = context_overrides or {}
        if "price_new" in ov:
            try:
                price_new = _format_price(float(ov.get("price_new")))
            except Exception:
                price_new = str(ov.get("price_new"))
        if "price_old" in ov:
            try:
                price_old = _format_price(float(ov.get("price_old")))
            except Exception:
                price_old = str(ov.get("price_old"))

        title = ov.get("title")  # не используется в v3 по умолчанию
        cover_url = ov.get("cover_url", book.cover_url)
        
        if not cover_url:
            raise ValueError("Book cover_url is required for creative generation")
        
        logger.info(f"Using cover_url for creative v3, book_id={book.id}, cover_url={cover_url[:100]}...")
        
        # Загружаем изображение в Placid для гарантированного доступа
        placid_media_url = _ensure_placid_media_url(cover_url)
        logger.info(f"Placid media URL for creative v3: {placid_media_url[:100]}...")
        
        layers_override = ov.get("layers") if ov else None

        if layers_override and isinstance(layers_override, dict):
            payload = {"template_uuid": PLACID_TPL_V3, "layers": layers_override}
        else:
            payload = {
                "template_uuid": PLACID_TPL_V3,
                "layers": {
                    "Book_cover": {"image": placid_media_url},
                    "Ipad_screen": {"image": placid_media_url},
                    "Iphone_screen": {"image": placid_media_url},
                    "Formats": {"text": "* — PDF, EPUB, MOBI, AZW3, FB2"},
                    "Button_text": {"text": "Download right now"},
                    "Title": {"text": "All formats available"},
                    "New_price": {"text": price_new},
                    "Only_for": {"text": _only_for_text(language)},
                    "Old_price": {"text": price_old},
                },
            }
        logger.info(f"Rendering creative v3 via Placid, book_id={book.id}")
        url, err = _placid_render(payload)
        if err:
            msg = str(err)
            if "Requires Subscription and Credits" in msg or "placid 403" in msg:
                raise PlacidQuotaError(msg)
            raise PlacidServiceError(msg)
        logger.info(f"Downloading image from Placid, book_id={book.id}")
        img = _download_bytes(url)
        key = _s3_key(book.id, PLACID_TPL_V3)
        logger.info(f"Uploading creative v3 to S3, book_id={book.id}, key={key}")
        s3_url = _upload_to_s3(key, img)

        existing = (
            db.query(BookCreative)
            .filter(
                BookCreative.book_id == book.id,
                BookCreative.language == language,
                BookCreative.creative_code == PLACID_TPL_V3,
            )
            .first()
        )
        if existing:
            existing.status = CreativeStatus.READY
            existing.placid_image_url = url
            existing.s3_key = key
            existing.s3_url = s3_url
            existing.payload_used = {"layers": payload.get("layers", {})}
            row = existing
        else:
            row = BookCreative(
                book_id=book.id,
                language=language,
                creative_code=PLACID_TPL_V3,
                status=CreativeStatus.READY,
                placid_image_url=url,
                s3_key=key,
                s3_url=s3_url,
                payload_used={"layers": payload.get("layers", {})},
            )
            db.add(row)
        db.commit()
        logger.info(f"Creative v3 generated successfully, book_id={book.id}")
        return row
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to generate creative v3 for book_id={book.id}, language={language}: {e}", exc_info=True)
        raise


def generate_all_creatives(db: Session, book_id: int, language: str, manual_payload: Optional[Dict[str, Dict[str, str]]] = None):
    """Генерирует все три креатива для книги. Пробрасывает исключения BookAI без изменений."""
    logger.info(f"Starting generation of all creatives, book_id={book_id}, language={language}")
    book = db.query(Book).get(book_id)
    if not book:
        raise ValueError("Book not found")

    v1_payload = manual_payload.get("v1") if manual_payload else None
    v2_payload = manual_payload.get("v2") if manual_payload else None

    try:
        logger.info(f"Generating creative v1, book_id={book_id}")
        c1 = generate_creative_v1(db, book, language, v1_payload)
        logger.info(f"Generating creative v2, book_id={book_id}")
        c2 = generate_creative_v2(db, book, language, v2_payload)
        logger.info(f"Generating creative v3, book_id={book_id}")
        c3 = generate_creative_v3(db, book, language)
        logger.info(f"All creatives generated successfully, book_id={book_id}")
        return [c1, c2, c3]
    except (BookAIServiceError, PlacidServiceError, ValueError) as e:
        # Пробрасываем BookAI ошибки и ValueError как есть
        logger.error(f"Error in generate_all_creatives, book_id={book_id}, language={language}: {e}")
        raise
    except Exception as e:
        # Обертываем неожиданные ошибки
        logger.error(f"Unexpected error in generate_all_creatives, book_id={book_id}, language={language}: {e}", exc_info=True)
        raise


def generate_single_creative(
    db: Session,
    book_id: int,
    language: str,
    target: str,
    overrides: Optional[Dict[str, Any]] = None,
) -> BookCreative:
    book = db.query(Book).get(book_id)
    if not book:
        raise ValueError("Book not found")

    # Нормализуем target: допускаем 'v1'/'v2'/'v3' или прямой creative_code
    code = target.strip().lower()
    if code in {"v1", PLACID_TPL_V1}:
        # Тексты можно передать как overrides["texts"] либо плоскими ключами
        texts: Optional[Dict[str, str]] = None
        if overrides:
            if isinstance(overrides.get("texts"), dict):
                texts = overrides.get("texts")
            else:
                # собираем известные текстовые поля
                known = ("hight_description", "medium_description", "down_description", "tag_1", "tag_2", "tag_3")
                texts = {k: overrides[k] for k in known if k in overrides}
                if not texts:
                    texts = None
        return generate_creative_v1(db, book, language, texts, context_overrides=overrides)
    if code in {"v2", PLACID_TPL_V2}:
        texts = None
        if overrides:
            if isinstance(overrides.get("texts"), dict):
                texts = overrides.get("texts")
            else:
                known = ("hight_description", "down_description", "tag_1", "tag_2", "tag_3")
                texts = {k: overrides[k] for k in known if k in overrides}
                if not texts:
                    texts = None
        return generate_creative_v2(db, book, language, texts, context_overrides=overrides)
    if code in {"v3", PLACID_TPL_V3}:
        return generate_creative_v3(db, book, language, context_overrides=overrides)

    raise ValueError("Unknown creative target")


