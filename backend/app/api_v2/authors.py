import re
from collections import defaultdict

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import List, Optional
from ..db.database import get_db
from ..dependencies.role_checker import require_roles
from ..models.models_v2 import User, Author
from ..schemas_v2.author import AuthorSimpleResponse, AuthorResponse, AuthorCreate, AuthorUpdate
from ..services_v2.author_service import list_authors_simple, get_author_detail, create_author, update_author, \
    delete_author

router = APIRouter()

@router.get("/", response_model=List[AuthorSimpleResponse])
def get_authors(language: Optional[str] = Query(None, description="Filter by language (EN, RU, ES)"),
                db: Session = Depends(get_db)):
    return list_authors_simple(db, language)

@router.get("/detail/{author_id}", response_model=AuthorResponse)
def get_author(author_id: int, db: Session = Depends(get_db)):
    return get_author_detail(db, author_id)

@router.post("/", response_model=AuthorResponse)
def create_new_author(
    author_data: AuthorCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin"))
):
    return create_author(db, author_data)

@router.put("/{author_id}", response_model=AuthorResponse)
def update_author_route(
    author_id: int,
    update_data: AuthorUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin"))
):
    return update_author(db, author_id, update_data)

@router.delete("/{author_id}", response_model=dict)
def delete_author_route(
    author_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin"))
):
    delete_author(db, author_id)
    return {"detail": "Author deleted successfully"}

def clean_name(name: str) -> str:
    """
    Удаляет префикс и суффикс "Dr." или "Prof." из имени.
    Например:
      "Dr. Enrico Agliardi" -> "Enrico Agliardi"
      "Filippo Fontana  Dr." -> "Filippo Fontana"
      "Nate FarleyDr"       -> "Nate Farley"
    """
    # Удаляем префикс (начало строки)
    cleaned = re.sub(r'^(dr\.?\s*|prof\.?\s*)+', '', name, flags=re.IGNORECASE)
    # Удаляем суффикс (конец строки)
    cleaned = re.sub(r'(\s*(dr\.?|prof\.?))+$', '', cleaned, flags=re.IGNORECASE)
    # Заменяем множественные пробелы одним
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()

@router.post("/remove_dr_and_prof_and_merge")
def remove_dr_and_prof_and_merge_authors(db: Session = Depends(get_db)):
    """
    1. Обходит всех авторов и обновляет поле name, удаляя в начале или в конце любые варианты "Dr." и "Prof.".
    2. После обновления ищет дубликаты (авторы с одинаковым очищённым именем) и, если найдено более одной записи, оставляет автора с минимальным id,
       а для остальных:
         - обновляет связи (например, в landing_authors),
         - удаляет дубликаты из таблицы authors.
    """
    # Этап 1: Очистка имен
    authors = db.query(Author).all()
    changed = False
    for author in authors:
        new_name = clean_name(author.name)
        if new_name != author.name:
            author.name = new_name
            changed = True
    if changed:
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error updating authors: {e}")

    # Этап 2: Поиск дубликатов и слияние
    rows = db.query(Author.id, Author.name).order_by(Author.name).all()
    grouped_by_name = defaultdict(list)
    for row in rows:
        grouped_by_name[row.name].append(row.id)

    for name, ids in grouped_by_name.items():
        if len(ids) > 1:
            main_id = min(ids)  # выбираем автора с минимальным id как основного
            for dup_id in ids:
                if dup_id == main_id:
                    continue
                # Обновляем связи в таблице landing_authors: заменяем dup_id на main_id
                db.execute(text("""
                    UPDATE landing_authors
                    SET author_id = :main_id
                    WHERE author_id = :dup_id
                """), {"main_id": main_id, "dup_id": dup_id})
                # Удаляем дубликат из таблицы authors
                db.execute(text("""
                    DELETE FROM authors
                    WHERE id = :dup_id
                """), {"dup_id": dup_id})
    db.commit()

    return {"detail": "Cleanup done. 'Dr.' and 'Prof.' removed and duplicates merged."}