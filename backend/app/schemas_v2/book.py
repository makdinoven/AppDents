from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl, constr, validator, condecimal
from datetime import datetime, date
from pydantic import AnyUrl
from pydantic.v1 import ConfigDict


from ..schemas_v2.common import AuthorCardResponse, TagResponse


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
    description: Optional[str]
    cover_url:   Optional[HttpUrl] = None
    tag_ids: list[int] = Field(default_factory=list)
    language:    constr(to_upper=True,
                        regex="^(EN|RU|ES|PT|AR|IT)$") = "EN"
    author_ids:  List[int] = Field(default_factory=list)
    files:       List[BookFilePayload]
    audio_files: List[BookAudioPayload] = Field(default_factory=list)
    publication_date: Optional[str] = None

    @validator("cover_url", pre=True)
    def _empty_cover_to_none(cls, v):
        if v is None:
            return None
        if isinstance(v, str) and v.strip() == "":
            return None
        return v

class BookUpdate(BookCreate):
    """Все поля те же, все опциональные."""
    title:       Optional[str] = None

    cover_url:   Optional[HttpUrl] = None
    files:       Optional[List[BookFilePayload]]
    audio_files: Optional[List[BookAudioPayload]]
    tag_ids: list[int] = Field(default_factory=list)

    @validator("cover_url", pre=True)
    def _empty_cover_to_none_update(cls, v):
        if v is None:
            return None
        if isinstance(v, str) and v.strip() == "":
            return None
        return v


class BookResponse(BaseModel):
    id:          int
    title:       str
    description: Optional[str]
    cover_url:   Optional[HttpUrl] = None
    language:    str
    author_ids:  List[int]
    files:       List[Dict[str, Any]]
    audio_files: List[Dict[str, Any]]
    created_at:  datetime
    updated_at:  datetime
    publication_date: Optional[str] = None
    page_count: Optional[int] = None
    publishers: List[Dict[str, Any]] = []  # [{"id": int, "name": str}, ...]

    class Config:
        orm_mode = True


class BookListResponse(BaseModel):
    id: int
    title: str
    language: str
    cover_url: str | None = None
    publication_date: Optional[str] = None
    page_count: Optional[int] = None
    publishers: List[Dict[str, Any]] = []

    class Config:
        orm_mode = True

class BookListPageResponse(BaseModel):
    total: int
    total_pages: int
    page: int
    size: int
    items: list[BookListResponse]

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

class BookMini(BaseModel):
    id: int
    title: str
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

# в schemas_v2/book.py
from pydantic import BaseModel, ConfigDict

class BookBrief(BaseModel):
    id: int
    title: str
    cover_url: str | None = None

    class Config:
        orm_mode = True

class BookLandingOut(BaseModel):
    id: int
    language: str
    page_name: str
    landing_name: str | None = None
    description: str | None = None
    old_price: float | None = None
    new_price: float | None = None
    is_hidden: bool
    books: list[BookBrief] = []

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
    preview_pdf:   Optional[HttpS3Url]
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

class CatalogGalleryImage(BaseModel):
    id: int
    url: HttpUrl
    alt: str | None = None
    caption: str | None = None
    sort_index: int

class BookLandingCatalogItem(BaseModel):
    id: int
    page_name: str
    landing_name: str | None = None
    language: str
    old_price: float | None = None
    new_price: float | None = None
    tags: list[TagMini] = []
    gallery: list[CatalogGalleryImage] = []

# Один ответ для обоих типов пагинации
class BookLandingCatalogPageResponse(BaseModel):
    # для пагинации по страницам
    total: int | None = None
    total_pages: int | None = None
    page: int | None = None
    size: int | None = None
    # для "see more" (курсорная)
    next_cursor: int | None = None
    has_more: bool | None = None

    items: list[BookLandingCatalogItem]

class BookLandingGalleryItem(BaseModel):
    id: int
    url: str
    alt: Optional[str] = None
    caption: Optional[str] = None
    sort_index: int

class BookLandingCardResponse(BaseModel):
    id: int
    landing_name: str
    slug: str                 # = page_name
    language: str             # регион/язык
    old_price: Optional[str] = None
    new_price: Optional[str] = None
    total_pages: Optional[int] = None  # сумма страниц всех книг лендинга
    publishers: List[Dict[str, Any]] = []  # издатели всех книг лендинга
    authors: List[AuthorCardResponse] = []
    tags: List[TagResponse] = []
    first_tag: Optional[str] = None
    gallery: List[BookLandingGalleryItem] = []
    main_image: str | None = None
    book_ids: list[int] | None = None
    available_formats: List[str] = []  # форматы всех книг лендинга

class BookLandingCardsResponse(BaseModel):
    total: int
    cards: List[BookLandingCardResponse]

class BookLandingCardsResponsePaginations(BaseModel):
    total: int
    total_pages: int
    page: int
    size: int
    cards: List[BookLandingCardResponse]

class UserBookDetailResponse(BaseModel):
    id: int
    title: str
    cover_url: Optional[str] = None
    description: Optional[str] = None
    publication_date: Optional[str] = None
    page_count: Optional[int] = None
    publishers: List[Dict[str, Any]] = []  # [{"id": int, "name": str}, ...]
    files_download: List[BookFileDownload] = []
    audio_download: List[BookAudioDownload] = []
    available_formats: List[str] = []  # ["PDF", "EPUB", ...]

class AuthorRef(BaseModel):
    id: int
    name: str
    photo: Optional[str] = None

class TagRef(BaseModel):
    id: int
    name: str

class BookFileAdmin(BaseModel):
    file_format: str
    s3_url: str
    size_bytes: Optional[int] = None

class BookAudioAdmin(BaseModel):
    id: int
    chapter_index: Optional[int] = None
    title: Optional[str] = None
    duration_sec: Optional[int] = None
    s3_url: str

class BookAdminDetailResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    cover_url: Optional[str] = None
    language: str
    publication_date: Optional[str] = None
    preview_pdf_url: Optional[str] = None
    page_count: Optional[int] = None
    publisher_ids: List[int] = []  # только ID издателей

    author_ids: List[int] = []
    tag_ids: List[int] = []


    files: List[BookFileAdmin] = []
    audio_files: List[BookAudioAdmin] = []

class BookPatch(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    cover_url: Optional[HttpUrl] = None
    language: Optional[constr(to_upper=True, regex="^(EN|RU|ES|PT|AR|IT)$")] = None
    publication_date: Optional[str] = None
    author_ids: Optional[List[int]] = None
    tag_ids: Optional[List[int]] = None

    @validator("cover_url", pre=True)
    def _empty_cover_to_none_patch(cls, v):
        if v is None:
            return None
        if isinstance(v, str) and v.strip() == "":
            return None
        return v


# ═══════════════════ Metadata Extraction ═══════════════════

class PublisherCandidate(BaseModel):
    """Кандидат издателя из метаданных PDF"""
    value: str
    source: str  # "Creator", "Author", "Producer", etc
    confidence: str  # "high", "medium", "low"

class DateCandidate(BaseModel):
    """Кандидат даты публикации из метаданных PDF"""
    value: str  # год или полная дата
    source: str  # "CreationDate", "ModDate", "XMP", etc
    confidence: str

class PDFMetadataExtracted(BaseModel):
    """Результат извлечения метаданных из PDF"""
    page_count: Optional[int] = None
    publisher_candidates: List[PublisherCandidate] = []
    date_candidates: List[DateCandidate] = []
    
    # Дополнительная информация
    raw_metadata: dict = {}  # сырые метаданные для отладки
    
class PublisherCreate(BaseModel):
    """Создание нового издателя"""
    name: str = Field(..., min_length=1, max_length=255)

class PublisherResponse(BaseModel):
    """Ответ с издателем"""
    id: int
    name: str
    created_at: datetime
    
    class Config:
        orm_mode = True

class ApplyMetadataPayload(BaseModel):
    """Применение выбранных метаданных к книге"""
    page_count: Optional[int] = None
    publisher_name: Optional[str] = Field(None, description="Название издателя (автоматически сопоставится с существующими или создастся новый)")
    publication_year: Optional[str] = Field(None, pattern=r"^\d{4}$", description="Год публикации (YYYY)")
