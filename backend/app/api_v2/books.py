from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..dependencies.role_checker import require_roles
from ..models.models_v2 import User
from ..schemas_v2.book import (
    BookCreate, BookUpdate, BookResponse,
    BookLandingCreate, BookLandingUpdate, BookLandingResponse,
)
from ..services_v2 import book_service

router = APIRouter()

# ─────────────── КНИГИ ───────────────────────────────────────────────────────
@router.post("/", response_model=BookResponse)
def create_new_book(
    payload: BookCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    return book_service.create_book(db, payload)

@router.put("/{book_id}", response_model=BookResponse)
def update_book_route(
    book_id: int,
    payload: BookUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    return book_service.update_book(db, book_id, payload)

@router.delete("/{book_id}", response_model=dict)
def delete_book_route(
    book_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    book_service.delete_book(db, book_id)
    return {"detail": "Book deleted successfully"}

# ─────────────── ЛЕНДИНГИ КНИГИ ─────────────────────────────────────────────
@router.post("/landing", response_model=BookLandingResponse)
def create_book_landing_route(
    payload: BookLandingCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    return book_service.create_book_landing(db, payload)

@router.put("/landing/{landing_id}", response_model=BookLandingResponse)
def update_book_landing_route(
    landing_id: int,
    payload: BookLandingUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    return book_service.update_book_landing(db, landing_id, payload)

@router.delete("/landing/{landing_id}", response_model=dict)
def delete_book_landing_route(
    landing_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    book_service.delete_book_landing(db, landing_id)
    return {"detail": "Book landing deleted successfully"}
