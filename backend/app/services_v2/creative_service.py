import io
import json
import logging
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
    try:
        r = requests.post(
            f"{settings.PLACID_BASE_URL}/images",
            headers={
                "Authorization": f"Bearer {settings.PLACID_API_KEY}",
                "Content-Type": "application/json",
            },
            data=json.dumps(payload),
            timeout=30,
        )
        if r.status_code >= 300:
            logger.error(f"Placid API error {r.status_code}: {r.text[:500]}")
            return "", f"placid {r.status_code}: {r.text[:500]}"
        try:
            data = r.json()
        except (ValueError, json.JSONDecodeError) as e:
            logger.error(f"Placid API invalid JSON response: {e}, response text: {r.text[:500]}")
            return "", f"placid: invalid json response - {str(e)}"
        # API Placid возвращает объект с полем url или data.url
        url = data.get("url") or data.get("image_url") or data.get("data", {}).get("url")
        if not url:
            logger.error(f"Placid API empty url in response: {data}")
            return "", "placid: empty url"
        return url, None
    except requests.exceptions.RequestException as e:
        logger.error(f"Placid API request failed: {e}")
        return "", f"placid request error: {str(e)}"


def _bookai_texts(db: Session, s3_url: str, language: str, version: int) -> Dict[str, str]:
    endpoint = "/creative/generate-v2" if version == 2 else "/creative/generate"
    try:
        r = requests.post(
            f"{settings.BOOKAI_BASE_URL}{endpoint}",
            json={"s3_url": s3_url, "language": language},
            timeout=60,
        )
        if r.status_code == 400:
            logger.error(f"BookAI 400 error: {r.text[:500]}")
            raise ValueError(f"bookai 400: {r.text[:500]}")
        r.raise_for_status()
        try:
            return r.json()
        except (ValueError, json.JSONDecodeError) as e:
            logger.error(f"BookAI invalid JSON response: {e}, response text: {r.text[:500]}")
            raise ValueError(f"bookai invalid json response: {str(e)}")
    except requests.exceptions.HTTPError as e:
        logger.error(f"BookAI HTTP error: {e}, response: {e.response.text[:500] if e.response else 'N/A'}")
        raise ValueError(f"bookai http error: {str(e)}")
    except requests.exceptions.RequestException as e:
        logger.error(f"BookAI request failed: {e}")
        raise ValueError(f"bookai request error: {str(e)}")


def _download_bytes(url: str) -> bytes:
    try:
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        return r.content
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download image from {url}: {e}")
        raise RuntimeError(f"Failed to download image: {str(e)}")


def _s3_key(book_id: int, code: str) -> str:
    return f"creatives/{book_id}/{code}.png"


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
    s3.upload_fileobj(io.BytesIO(data), S3_BUCKET, key, ExtraArgs={"ACL": "public-read", "ContentType": "image/png"})
    return f"{S3_PUBLIC_HOST}/{key}"


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

        if texts is None:
            logger.info(f"Generating texts for creative v1, book_id={book.id}, language={language}")
            texts = _bookai_texts(db, book.cover_url, language, version=1)

        # Позволяем переопределить титул/обложку/слои
        title = ov.get("title", book.title)
        cover_url = ov.get("cover_url", book.cover_url)
        layers_override = ov.get("layers") if ov else None

        if layers_override and isinstance(layers_override, dict):
            payload = {"template_uuid": PLACID_TPL_V1, "layers": layers_override}
        else:
            payload = {
                "template_uuid": PLACID_TPL_V1,
                "layers": {
                    "Main_book_image": {"media": cover_url},
                    "Back_book_image": {"media": cover_url},
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
            raise RuntimeError(err)
        logger.info(f"Downloading image from Placid, book_id={book.id}")
        img = _download_bytes(url)
        key = _s3_key(book.id, PLACID_TPL_V1)
        logger.info(f"Uploading creative v1 to S3, book_id={book.id}, key={key}")
        s3_url = _upload_to_s3(key, img)

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
        db.merge(row)
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

        if texts is None:
            logger.info(f"Generating texts for creative v2, book_id={book.id}, language={language}")
            texts = _bookai_texts(db, book.cover_url, language, version=2)

        # Позволяем переопределить титул/обложку/слои
        title = ov.get("title", book.title)
        cover_url = ov.get("cover_url", book.cover_url)
        layers_override = ov.get("layers") if ov else None

        if layers_override and isinstance(layers_override, dict):
            payload = {"template_uuid": PLACID_TPL_V2, "layers": layers_override}
        else:
            payload = {
                "template_uuid": PLACID_TPL_V2,
                "layers": {
                    "Book_1_cover": {"media": cover_url},
                    "Book_2_cover": {"media": cover_url},
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
            raise RuntimeError(err)
        logger.info(f"Downloading image from Placid, book_id={book.id}")
        img = _download_bytes(url)
        key = _s3_key(book.id, PLACID_TPL_V2)
        logger.info(f"Uploading creative v2 to S3, book_id={book.id}, key={key}")
        s3_url = _upload_to_s3(key, img)

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
        db.merge(row)
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
        layers_override = ov.get("layers") if ov else None

        if layers_override and isinstance(layers_override, dict):
            payload = {"template_uuid": PLACID_TPL_V3, "layers": layers_override}
        else:
            payload = {
                "template_uuid": PLACID_TPL_V3,
                "layers": {
                    "Book_cover": {"media": cover_url},
                    "Ipad_screen": {"media": cover_url},
                    "Iphone_screen": {"media": cover_url},
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
            raise RuntimeError(err)
        logger.info(f"Downloading image from Placid, book_id={book.id}")
        img = _download_bytes(url)
        key = _s3_key(book.id, PLACID_TPL_V3)
        logger.info(f"Uploading creative v3 to S3, book_id={book.id}, key={key}")
        s3_url = _upload_to_s3(key, img)

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
        db.merge(row)
        db.commit()
        logger.info(f"Creative v3 generated successfully, book_id={book.id}")
        return row
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to generate creative v3 for book_id={book.id}, language={language}: {e}", exc_info=True)
        raise


def generate_all_creatives(db: Session, book_id: int, language: str, manual_payload: Optional[Dict[str, Dict[str, str]]] = None):
    book = db.query(Book).get(book_id)
    if not book:
        raise ValueError("Book not found")

    v1_payload = manual_payload.get("v1") if manual_payload else None
    v2_payload = manual_payload.get("v2") if manual_payload else None

    c1 = generate_creative_v1(db, book, language, v1_payload)
    c2 = generate_creative_v2(db, book, language, v2_payload)
    c3 = generate_creative_v3(db, book, language)
    return [c1, c2, c3]


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


