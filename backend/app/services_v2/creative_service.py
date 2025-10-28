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
        return "", f"placid {r.status_code}: {r.text[:500]}"
    data = r.json()
    # API Placid возвращает объект с полем url или data.url
    url = data.get("url") or data.get("image_url") or data.get("data", {}).get("url")
    if not url:
        return "", "placid: empty url"
    return url, None


def _bookai_texts(db: Session, s3_url: str, language: str, version: int) -> Dict[str, str]:
    endpoint = "/creative/generate-v2" if version == 2 else "/creative/generate"
    r = requests.post(
        f"{settings.BOOKAI_BASE_URL}{endpoint}",
        json={"s3_url": s3_url, "language": language},
        timeout=60,
    )
    if r.status_code == 400:
        raise ValueError(f"bookai 400: {r.text[:500]}")
    r.raise_for_status()
    return r.json()


def _download_bytes(url: str) -> bytes:
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    return r.content


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


def generate_creative_v1(db: Session, book: Book, language: str, texts: Optional[Dict[str, str]]) -> BookCreative:
    _require_book_fields(book)
    bl = _min_price_landing(db, book.id, language)
    if not bl or bl.new_price is None:
        raise ValueError("Price not found in book_landings")
    price_new = _format_price(float(bl.new_price))
    price_old = _format_price(float(bl.old_price or 0))

    if texts is None:
        texts = _bookai_texts(db, book.cover_url, language, version=1)

    payload = _build_layers_v1(book, language, texts, price_old, price_new)
    url, err = _placid_render(payload)
    if err:
        raise RuntimeError(err)
    img = _download_bytes(url)
    key = _s3_key(book.id, PLACID_TPL_V1)
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
    return row


def generate_creative_v2(db: Session, book: Book, language: str, texts: Optional[Dict[str, str]]) -> BookCreative:
    _require_book_fields(book)
    bl = _min_price_landing(db, book.id, language)
    if not bl or bl.new_price is None:
        raise ValueError("Price not found in book_landings")
    price_new = _format_price(float(bl.new_price))
    price_old = _format_price(float(bl.old_price or 0))

    if texts is None:
        texts = _bookai_texts(db, book.cover_url, language, version=2)

    payload = _build_layers_v2(book, language, texts, price_old, price_new)
    url, err = _placid_render(payload)
    if err:
        raise RuntimeError(err)
    img = _download_bytes(url)
    key = _s3_key(book.id, PLACID_TPL_V2)
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
    return row


def generate_creative_v3(db: Session, book: Book, language: str) -> BookCreative:
    _require_book_fields(book)
    bl = _min_price_landing(db, book.id, language)
    if not bl or bl.new_price is None:
        raise ValueError("Price not found in book_landings")
    price_new = _format_price(float(bl.new_price))
    price_old = _format_price(float(bl.old_price or 0))

    payload = _build_layers_v3(book, language, price_old, price_new)
    url, err = _placid_render(payload)
    if err:
        raise RuntimeError(err)
    img = _download_bytes(url)
    key = _s3_key(book.id, PLACID_TPL_V3)
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
    return row


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


