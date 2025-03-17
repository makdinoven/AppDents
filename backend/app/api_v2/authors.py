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
    Удаляет префиксы и суффиксы "Dr." и "Prof." (без учета регистра, с любыми пробелами)
    Например:
      "Dr. Enrico Agliardi" -> "Enrico Agliardi"
      "Filippo Fontana  Dr." -> "Filippo Fontana"
      "Nate FarleyDr"       -> "Nate Farley"
    """
    # Удаляем префикс
    cleaned = re.sub(r'^(dr\.?\s*|prof\.?\s*)+', '', name, flags=re.IGNORECASE)
    # Удаляем суффикс
    cleaned = re.sub(r'(\s*(dr\.?|prof\.?))+$', '', cleaned, flags=re.IGNORECASE)
    # Заменяем множественные пробелы одним
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()

@router.post("/remove_dr_and_prof_and_merge")
def remove_dr_and_prof_and_merge_authors(db: Session = Depends(get_db)):
    """
    1. Обновляет имена авторов, удаляя префиксы и суффиксы "Dr." и "Prof.".
    2. Группирует авторов по очищенному имени.
    3. Для групп с дубликатами:
       - оставляет автора с минимальным id как основного (обновляя его имя),
       - обновляет связи (например, в landing_authors) с дубликатами,
       - удаляет дубликаты.
    """
    # Этап 1: Обновление всех имен через Python (без SQL REGEXP)
    authors = db.query(Author).all()
    for author in authors:
        new_name = clean_name(author.name)
        if new_name != author.name:
            author.name = new_name
            db.add(author)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating authors: {e}")

    # Этап 2: Группировка авторов по очищенному имени
    rows = db.query(Author.id, Author.name).order_by(Author.name).all()
    grouped_by_name = defaultdict(list)
    for row in rows:
        grouped_by_name[row.name].append(row.id)

    # Этап 3: Слияние дубликатов (для каждой группы, где более одного автора)
    for name, ids in grouped_by_name.items():
        if len(ids) > 1:
            # Сортируем по id, чтобы выбрать автора с минимальным id
            ids.sort()
            main_id = ids[0]
            # Обновляем основного автора (если нужно) и фиксируем изменения для группы
            db.execute(text("UPDATE authors SET name = :name WHERE id = :id"), {"name": name, "id": main_id})
            db.commit()
            # Для каждого дубликата:
            for dup_id in ids[1:]:
                # Обновляем связи в таблице landing_authors (замена dup_id на main_id)
                db.execute(text("""
                    UPDATE landing_authors
                    SET author_id = :main_id
                    WHERE author_id = :dup_id
                """), {"main_id": main_id, "dup_id": dup_id})
                # Удаляем дубликат
                db.execute(text("DELETE FROM authors WHERE id = :dup_id"), {"dup_id": dup_id})
            db.commit()

    return {"detail": "Cleanup done. 'Dr.' and 'Prof.' removed and duplicates merged."}