from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl, constr, validator, condecimal
from datetime import datetime
from pydantic import AnyUrl

class HttpS3Url(AnyUrl):
    """
    URL с разрешёнными схемами http / https / s3.
    """
    allowed_schemes = {'http', 'https', 's3'}




class BookLandingBase(BaseModel):
    language: str = Field(default="EN", pattern="^(EN|RU|ES|PT|AR|IT)$")
    page_name: str
    landing_name: Optional[str] = None
    description: Optional[str] = None
    old_price: Optional[Decimal] = None
    new_price: Optional[Decimal] = None
    is_hidden: Optional[bool] = False

    # НЕОБЯЗАТЕЛЬНО:
    book_ids: Optional[List[int]] = None
    tag_ids: Optional[List[int]] = None
    # preview_photo НЕ грузим здесь — это делает upload-роут (останется опциональным полем на PATCH)
    preview_imgs: Optional[List[str]] = None   # если захотите руками задать

class BookLandingCreate(BookLandingBase):
    pass

# ---------- ↓ Payload’ы CRUD книги -------------------------------------------------
class BookFilePayload(BaseModel):
    file_format: constr(to_upper=True,
                        regex="^(PDF|EPUB|MOBI|AZW3|FB2)$")
    s3_url:      HttpUrl
    size_bytes:  Optional[int]

class BookAudioPayload(BaseModel):
    chapter_index: Optional[int] = Field(None, ge=1)
    title:         Optional[str]
    duration_sec:  Optional[int]
    s3_url:        HttpUrl

class BookCreate(BaseModel):
    title:       str
    slug: constr(regex=r"^[a-zA-Z0-9\-]+$")
    description: Optional[str]
    cover_url:   HttpUrl
    tag_ids: list[int] = Field(default_factory=list)
    language:    constr(to_upper=True,
                        regex="^(EN|RU|ES|PT|AR|IT)$") = "EN"
    author_ids:  List[int] = Field(default_factory=list)
    files:       List[BookFilePayload]
    audio_files: List[BookAudioPayload] = Field(default_factory=list)

class BookUpdate(BookCreate):
    """Все поля те же, все опциональные."""
    title:       Optional[str] = None
    slug: Optional[constr(regex=r"^[a-zA-Z0-9\-]+$")] = None
    cover_url:   Optional[HttpUrl] = None
    files:       Optional[List[BookFilePayload]]
    audio_files: Optional[List[BookAudioPayload]]
    tag_ids: list[int] = Field(default_factory=list)


class BookResponse(BaseModel):
    id:          int
    title:       str
    description: Optional[str]
    cover_url:   HttpUrl
    language:    str
    author_ids:  List[int]
    files:       List[Dict[str, Any]]
    audio_files: List[Dict[str, Any]]
    created_at:  datetime
    updated_at:  datetime

    class Config:
        orm_mode = True


class BookLandingUpdate(BaseModel):
    language: Optional[str] = Field(default=None, pattern="^(EN|RU|ES|PT|AR|IT)$")
    page_name: Optional[str] = None
    landing_name: Optional[str] = None
    description: Optional[str] = None
    old_price: Optional[Decimal] = None
    new_price: Optional[Decimal] = None
    is_hidden: Optional[bool] = None

    book_ids: Optional[List[int]] = None
    tag_ids: Optional[List[int]] = None
    preview_photo: Optional[str] = None
    preview_imgs: Optional[List[str]] = None

class BookMini(BaseModel):
    id: int
    title: str
    slug: str
    cover_url: Optional[str] = None
    # Превью PDF берём вычисляемым полем на детальном GET (см. ниже)

class TagMini(BaseModel):
    id: int
    name: str

class AuthorMini(BaseModel):
    id: int
    name: str
    photo: Optional[str] = None
    # counts можно добавить в детальном ответе как вычисляемые

class BookLandingOut(BaseModel):
    id: int
    language: str
    page_name: str
    landing_name: Optional[str]
    description: Optional[str]
    old_price: Optional[Decimal]
    new_price: Optional[Decimal]
    is_hidden: bool
    preview_photo: Optional[str]
    preview_imgs: Optional[List[str]]

    books: List[BookMini] = []
    tags: List[TagMini] = []

    class Config:
        orm_mode = True

class BookLandingDetail(BookLandingOut):
    # Расширение для детального GET
    authors: List[AuthorMini] = []
    # Превью по книгам:
    book_previews: List[dict] = []  # [{book_id, preview_pdf_url}, ...]

# >>> app/schemas_v2/book.py — ДОБАВИТЬ ПЕРЕД/РЯДОМ С BookLandingResponse <<<

class IncludedBookShort(BaseModel):
    """
    Короткое представление книги внутри лендинга:
    id, title, slug, обложка и превью-PDF (15 страниц).
    """
    id: int
    title: str
    slug: str
    cover_url: Optional[HttpUrl] = None
    preview_pdf: Optional[HttpS3Url] = None  # может быть http/https/s3


class BookLandingResponse(BaseModel):
    id:          int
    book_id:     int
    page_name:   str
    landing_name: Optional[str]
    old_price: Decimal | None = None
    new_price: Decimal | None = None
    description:  Optional[str]
    preview_photo: Optional[HttpS3Url]
    preview_pdf:   Optional[HttpS3Url]
    preview_imgs:  Optional[List[HttpS3Url]]
    sales_count:   int
    is_hidden:     bool

    # ↓↓↓ ДОБАВЛЕНО: список книг, входящих в лендинг (bundle или одиночная)
    included_books: List[IncludedBookShort] = Field(default_factory=list)
    bundle_size: int = 0

    class Config:
        orm_mode = True


# ─────────────────────── DOWNLOAD-модели ──────────────────────────
class BookFileDownload(BaseModel):
    file_format: str
    download_url: HttpUrl
    size_bytes: int | None = None

class BookAudioDownload(BaseModel):
    chapter_index: int | None
    title: str | None
    duration_sec: int | None
    download_url: HttpUrl

class BookDetailResponse(BookResponse):
    """Расширенный ответ для админов и владельцев книги."""
    landings: list[BookLandingResponse]
    files_download: list[BookFileDownload]
    audio_download: list[BookAudioDownload]

class PdfUploadInitRequest(BaseModel):
    filename: str = Field(..., description="Имя файла, например `book.pdf`")
    content_type: str = Field("application/pdf", description="MIME, по умолчанию PDF")

class PdfUploadInitResponse(BaseModel):
    method: str = "POST"
    url: str
    fields: dict
    key: str
    cdn_url: str
    max_size_mb: int = 2048

class PdfUploadFinalizeRequest(BaseModel):
    key: str = Field(..., description="S3 key, полученный на шаге INIT")
    size_bytes: int | None = None
