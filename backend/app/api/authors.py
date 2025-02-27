# api/authors.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..schemas.author import AuthorCreate, AuthorUpdate, AuthorResponse
from ..services.author_service import create_author, update_author, delete_author, search_authors
from ..db.database import get_db
from ..dependencies.role_checker import require_roles
from ..models.models import User, Author

router = APIRouter()

@router.post(
    "/",
    response_model=AuthorResponse,
    summary="Add new  author",
    description="Create a new author with input data."
)
def add_author(author: AuthorCreate, db: Session = Depends(get_db), current_admin: User = Depends(require_roles("admin"))):
    try:
        new_author = create_author(db, author)
        return new_author
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.put(
    "/{author_id}",
    response_model=AuthorResponse,
    summary="Update author",
    description="Update author using id"
)
def update_author_endpoint(author_id: int, author: AuthorUpdate, db: Session = Depends(get_db)):
    try:
        updated_author = update_author(db, author_id, author)
        return updated_author
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.delete(
    "/{author_id}",
    response_model=AuthorResponse,
    summary="Delete author",
    description="Delete author using id"
)
def delete_author_endpoint(author_id: int, db: Session = Depends(get_db)):
    try:
        deleted_author = delete_author(db, author_id)
        return deleted_author
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get(
    "/search",
    response_model=List[AuthorResponse],
    summary="Search authors",
    description="Search authors by name."
)
def search_authors_endpoint(query: str = Query(..., description="Строка для поиска по имени автора"), db: Session = Depends(get_db)):
    authors = search_authors(db, query)
    return authors

class AuthorIdName(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True

router = APIRouter()

@router.get(
    "/list",
    response_model=List[AuthorIdName],
    summary="List all authors (id and name)",
    description="Возвращает список авторов с их id и именем"
)
def list_authors(db: Session = Depends(get_db)):
    authors = db.query(Author.id, Author.name).all()
    # Преобразуем список кортежей в список словарей для валидации pydantic
    result = [{"id": author.id, "name": author.name} for author in authors]
    return result