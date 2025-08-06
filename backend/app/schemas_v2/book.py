from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl, constr, validator
from datetime import datetime

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

# ---------- ↓ Payload’ы CRUD лендинга книги ----------------------------------------
class BookLandingCreate(BaseModel):
    book_id:      int
    page_name:    constr(regex=r"^[a-zA-Z0-9\-]+$")
    language:     constr(to_upper=True,
                         regex="^(EN|RU|ES|PT|AR|IT)$") = "EN"
    landing_name: Optional[str]
    old_price:    Optional[str]
    new_price:    Optional[str]
    description:  Optional[str]
    preview_photo: Optional[HttpUrl]
    preview_pdf:   Optional[HttpUrl]
    preview_imgs:  Optional[List[HttpUrl]]
    is_hidden:     bool = False

class BookLandingUpdate(BookLandingCreate):
    page_name: Optional[str] = None
    book_id:   Optional[int] = None

class BookLandingResponse(BaseModel):
    id:          int
    book_id:     int
    page_name:   str
    landing_name: Optional[str]
    old_price:    Optional[str]
    new_price:    Optional[str]
    description:  Optional[str]
    preview_photo: Optional[HttpUrl]
    preview_pdf:   Optional[HttpUrl]
    preview_imgs:  Optional[List[HttpUrl]]
    sales_count:   int
    is_hidden:     bool

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
