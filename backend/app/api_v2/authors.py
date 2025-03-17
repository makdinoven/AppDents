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
    # Удаляем префикс "Dr." или "Prof." в начале имени
    cleaned = re.sub(r'^(dr\.?\s*|prof\.?\s*)+', '', name, flags=re.IGNORECASE)
    # Удаляем суффикс "Dr." или "Prof." в конце имени
    cleaned = re.sub(r'(\s*(dr\.?|prof\.?))+$', '', cleaned, flags=re.IGNORECASE)
    # Заменяем несколько пробелов одним и обрезаем крайние пробелы
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()

@router.post("/remove_dr_and_prof_and_merge")
def remove_dr_and_prof_and_merge_authors(db: Session = Depends(get_db)):
    """
    1. Удаляет префиксы и суффиксы "Dr." и "Prof." из поля name авторов.
    2. Находит дубликаты (авторы с одинаковым очищённым именем) и сливает их:
       - Обновляет связи в таблице landing_authors, заменяя дубликаты на основного автора (с минимальным id).
       - Удаляет дубликаты из таблицы authors.
    """
    try:
        # Этап 1: Очистка имен с использованием одного UPDATE IGNORE-запроса
        db.execute(text("""
            UPDATE IGNORE authors
            SET name = TRIM(
                REGEXP_REPLACE(
                  REGEXP_REPLACE(
                    REGEXP_REPLACE(name, '^(dr\\.?\\s*|prof\\.?\\s*)+', ''),
                    '(dr\\.?\\s*|prof\\.?\\s*)+$', ''
                  ),
                  '\\s+', ' '
                )
            )
            WHERE name COLLATE utf8mb4_general_ci REGEXP '^(dr\\.?\\s*|prof\\.?\\s*)'
               OR name COLLATE utf8mb4_general_ci REGEXP '(dr\\.?\\s*|prof\\.?\\s*)$';
        """))
        db.commit()

        # Этап 2: Поиск дубликатов и их слияние
        rows = db.execute(text("""
            SELECT id, name FROM authors
            ORDER BY name;
        """)).fetchall()

        grouped_by_name = defaultdict(list)
        for row in rows:
            grouped_by_name[row.name].append(row.id)

        for name, ids in grouped_by_name.items():
            if len(ids) > 1:
                main_id = min(ids)  # выбираем автора с минимальным id как основного
                for dup_id in ids:
                    if dup_id == main_id:
                        continue
                    # Обновляем связи в таблице landing_authors, чтобы ссылки с дубликатного id
                    # ссылались на основного автора
                    db.execute(text("""
                        UPDATE landing_authors
                        SET author_id = :main_id
                        WHERE author_id = :dup_id;
                    """), {"main_id": main_id, "dup_id": dup_id})
                    # Удаляем дубликат из таблицы authors
                    db.execute(text("""
                        DELETE FROM authors
                        WHERE id = :dup_id;
                    """), {"dup_id": dup_id})
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error during cleanup: {e}")

    return {"detail": "Cleanup done. 'Dr.' and 'Prof.' removed and duplicates merged."}