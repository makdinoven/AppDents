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
    # Удаляем префикс "Dr." или "Prof." в начале строки
    cleaned = re.sub(r'^(dr\.?\s*|prof\.?\s*)+', '', name, flags=re.IGNORECASE)
    # Удаляем суффикс "Dr." или "Prof." в конце строки
    cleaned = re.sub(r'(\s*(dr\.?|prof\.?))+$', '', cleaned, flags=re.IGNORECASE)
    # Заменяем множественные пробелы одним
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()

@router.post("/remove_dr_and_prof_and_merge")
def remove_dr_and_prof_and_merge_authors(db: Session = Depends(get_db)):
    """
    1. Обходит всех авторов и вычисляет очищённое имя (без префиксов/суффиксов "Dr." и "Prof.").
    2. Группирует авторов по очищённому имени.
    3. Для каждой группы, если найдено более одного автора, оставляет автора с минимальным id (основного),
       обновляет его имя (если требуется), обновляет связи в таблице landing_authors для всех дубликатов и удаляет их.
    """
    # Получаем всех авторов
    authors = db.query(Author).all()

    # Группируем по очищённому имени
    mapping = defaultdict(list)
    for author in authors:
        new_name = clean_name(author.name)
        mapping[new_name].append(author)

    # Обрабатываем группы
    for cleaned_name, authors_list in mapping.items():
        if len(authors_list) > 1:
            # Сортируем по id, чтобы выбрать автора с минимальным id как основного
            authors_list.sort(key=lambda a: a.id)
            main_author = authors_list[0]
            # Если имя основного автора отличается, обновляем его
            if main_author.name != cleaned_name:
                main_author.name = cleaned_name
                db.add(main_author)
            # Для остальных в группе обновляем связи и удаляем запись
            for dup_author in authors_list[1:]:
                # Обновляем связи в таблице landing_authors, заменяя dup_author.id на main_author.id
                db.execute(text("""
                    UPDATE landing_authors
                    SET author_id = :main_id
                    WHERE author_id = :dup_id
                """), {"main_id": main_author.id, "dup_id": dup_author.id})
                # Удаляем дубликат
                db.delete(dup_author)
        else:
            # Если группа состоит из одного автора, можно обновить его имя, если оно отличается
            author = authors_list[0]
            new_name = clean_name(author.name)
            if author.name != new_name:
                author.name = new_name
                db.add(author)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error during cleanup: {e}")

    return {"detail": "Cleanup done. 'Dr.' and 'Prof.' removed and duplicates merged."}