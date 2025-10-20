# API для извлечения и применения метаданных из PDF книг
import logging
import os
import tempfile
import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from botocore.exceptions import ClientError

from ..db.database import get_db
from ..dependencies.role_checker import require_roles
from ..models.models_v2 import User, Book, BookFile, BookFileFormat, Publisher
from ..schemas_v2.book import (
    PDFMetadataExtracted, PublisherCandidate, DateCandidate,
    ApplyMetadataPayload, PublisherResponse
)

# S3
import boto3
from botocore.config import Config

S3_ENDPOINT    = os.getenv("S3_ENDPOINT", "https://s3.timeweb.com")
S3_BUCKET      = os.getenv("S3_BUCKET", "cdn.dent-s.com")
S3_REGION      = os.getenv("S3_REGION", "ru-1")
S3_PUBLIC_HOST = os.getenv("S3_PUBLIC_HOST", "https://cdn.dent-s.com")

s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    region_name=S3_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    config=Config(signature_version="s3", s3={"addressing_style": "path"}),
)

router = APIRouter()
log = logging.getLogger(__name__)


def _key_from_url(url: str) -> str:
    """Извлекает S3 key из CDN URL"""
    from urllib.parse import urlparse, unquote
    if url.startswith("s3://"):
        return urlparse(url).path.lstrip("/")
    p = urlparse(url)
    path = unquote(p.path.lstrip("/"))
    if path.startswith(f"{S3_BUCKET}/"):
        return path[len(S3_BUCKET) + 1 :]
    return path


def _extract_pdf_metadata_pypdf(pdf_path: str) -> PDFMetadataExtracted:
    """
    Извлекает метаданные из PDF используя pypdf.
    Возвращает кандидатов для издателя, даты и точное количество страниц.
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        try:
            from PyPDF2 import PdfReader
        except ImportError:
            raise HTTPException(500, "pypdf or PyPDF2 not installed")
    
    try:
        reader = PdfReader(pdf_path)
        info = reader.metadata or {}
        
        result = PDFMetadataExtracted()
        
        # 1. Page count (самое надёжное)
        result.page_count = len(reader.pages)
        
        # 2. Publisher candidates из разных полей
        publisher_candidates = []
        
        # Creator часто содержит издателя
        if info.get("/Creator"):
            creator = str(info["/Creator"]).strip()
            if creator and len(creator) > 2:
                publisher_candidates.append(PublisherCandidate(
                    value=creator,
                    source="Creator",
                    confidence="high" if "publish" in creator.lower() or "verlag" in creator.lower() else "medium"
                ))
        
        # Author иногда тоже издатель
        if info.get("/Author"):
            author = str(info["/Author"]).strip()
            if author and len(author) > 2:
                # Эвристика: если содержит "GmbH", "Ltd", "Inc", "Publishing" — скорее издатель
                is_publisher = any(kw in author for kw in ["GmbH", "Ltd", "Inc", "Publishing", "Verlag", "Press"])
                publisher_candidates.append(PublisherCandidate(
                    value=author,
                    source="Author",
                    confidence="medium" if is_publisher else "low"
                ))
        
        # Producer (ПО, но иногда издатель)
        if info.get("/Producer"):
            producer = str(info["/Producer"]).strip()
            if producer and len(producer) > 2 and not any(sw in producer.lower() for sw in ["adobe", "microsoft", "foxit", "pdf"]):
                publisher_candidates.append(PublisherCandidate(
                    value=producer,
                    source="Producer",
                    confidence="low"
                ))
        
        result.publisher_candidates = publisher_candidates
        
        # 3. Date candidates
        date_candidates = []
        
        # CreationDate
        if info.get("/CreationDate"):
            raw_date = str(info["/CreationDate"])
            # Формат: D:20221029175742-04'00'
            year_match = re.search(r"(\d{4})", raw_date)
            if year_match:
                year = year_match.group(1)
                date_candidates.append(DateCandidate(
                    value=year,
                    source="CreationDate",
                    confidence="medium"  # не всегда = год публикации книги
                ))
        
        # ModDate
        if info.get("/ModDate"):
            raw_date = str(info["/ModDate"])
            year_match = re.search(r"(\d{4})", raw_date)
            if year_match:
                year = year_match.group(1)
                date_candidates.append(DateCandidate(
                    value=year,
                    source="ModDate",
                    confidence="low"  # дата модификации PDF, не публикации
                ))
        
        result.date_candidates = date_candidates
        
        # Сырые метаданные для отладки
        result.raw_metadata = {k.lstrip("/"): str(v) for k, v in info.items()}
        
        return result
        
    except Exception as e:
        log.error(f"Failed to extract metadata: {e}")
        raise HTTPException(500, f"Failed to extract PDF metadata: {str(e)}")


@router.get("/{book_id}/extract-metadata", 
            response_model=PDFMetadataExtracted,
            summary="Извлечь метаданные из PDF книги")
def extract_book_metadata(
    book_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles("admin")),
):
    """
    Извлекает метаданные из PDF файла книги:
    - Количество страниц (page_count) — точное значение
    - Кандидаты издателей из полей Creator, Author, Producer
    - Кандидаты дат из CreationDate, ModDate
    
    Перед вызовом убедитесь, что PDF загружен (есть BookFile с форматом PDF).
    """
    book = db.query(Book).get(book_id)
    if not book:
        raise HTTPException(404, "Book not found")
    
    # Проверка существования PDF
    pdf_file = (
        db.query(BookFile)
          .filter(BookFile.book_id == book.id, BookFile.file_format == BookFileFormat.PDF)
          .first()
    )
    if not pdf_file:
        raise HTTPException(400, "No PDF file found for this book. Upload PDF first.")
    
    # Скачать PDF из S3
    pdf_key = _key_from_url(pdf_file.s3_url)
    
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        try:
            s3.download_file(S3_BUCKET, pdf_key, tmp.name)
        except ClientError as e:
            raise HTTPException(500, f"Failed to download PDF from S3: {e}")
        
        # Извлечь метаданные
        metadata = _extract_pdf_metadata_pypdf(tmp.name)
        
        # Удалить временный файл
        os.unlink(tmp.name)
    
    return metadata


@router.post("/{book_id}/apply-metadata",
             summary="Применить выбранные метаданные к книге")
def apply_book_metadata(
    book_id: int,
    payload: ApplyMetadataPayload,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles("admin")),
):
    """
    Применяет выбранные админом метаданные к книге:
    - page_count — сохраняется напрямую
    - publisher — либо связывает с существующим (publisher_id), либо создаёт нового (new_publisher_name)
    - publication_year — сохраняется в publication_date
    """
    book = db.query(Book).get(book_id)
    if not book:
        raise HTTPException(404, "Book not found")
    
    changes = []
    
    # 1. Page count
    if payload.page_count is not None:
        book.page_count = payload.page_count
        changes.append(f"page_count={payload.page_count}")
    
    # 2. Publisher
    if payload.publisher_id is not None:
        publisher = db.query(Publisher).get(payload.publisher_id)
        if not publisher:
            raise HTTPException(400, f"Publisher with id={payload.publisher_id} not found")
        
        # Добавляем издателя (если ещё не добавлен)
        if publisher not in book.publishers:
            book.publishers.append(publisher)
            changes.append(f"added publisher '{publisher.name}'")
    
    elif payload.new_publisher_name:
        # Создаём нового издателя (или используем существующего с таким именем)
        name = payload.new_publisher_name.strip()
        existing = db.query(Publisher).filter(Publisher.name == name).first()
        
        if existing:
            if existing not in book.publishers:
                book.publishers.append(existing)
                changes.append(f"linked to existing publisher '{existing.name}'")
        else:
            new_pub = Publisher(name=name)
            db.add(new_pub)
            db.flush()  # получить ID
            book.publishers.append(new_pub)
            changes.append(f"created new publisher '{name}'")
    
    # 3. Publication year
    if payload.publication_year:
        book.publication_date = payload.publication_year
        changes.append(f"publication_year={payload.publication_year}")
    
    db.commit()
    db.refresh(book)
    
    log.info("[METADATA] Applied to book_id=%s: %s", book_id, ", ".join(changes))
    
    return {
        "message": "Metadata applied successfully",
        "book_id": book.id,
        "changes": changes,
        "page_count": book.page_count,
        "publishers": [{"id": p.id, "name": p.name} for p in book.publishers],
        "publication_date": book.publication_date,
    }


@router.get("/publishers", 
            response_model=list[PublisherResponse],
            summary="Список всех издателей")
def list_publishers(
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles("admin")),
):
    """Возвращает список всех издателей для выбора в UI"""
    publishers = db.query(Publisher).order_by(Publisher.name).all()
    return publishers

