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
    Удаляет префиксы и суффиксы "Dr." и "Prof." из имени автора.
    Например:
      "Dr. Enrico Agliardi" -> "Enrico Agliardi"
      "Filippo Fontana  Dr." -> "Filippo Fontana"
      "Nate FarleyDr"       -> "Nate Farley"
      "DrEnrico"           -> "Enrico" (если так)
    """
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
    1. Группирует авторов по очищённому имени (без "Dr." и "Prof.").
    2. Если для одного имени найдено более одного автора, оставляет автора с минимальным id,
       обновляет его имя (если требуется) и переносит связи, а дубликаты удаляет.
    """
    # Извлекаем всех авторов
    authors = db.query(Author).all()

    # Группируем по очищённому имени
    grouped = defaultdict(list)
    for author in authors:
        cleaned = clean_name(author.name)
        grouped[cleaned].append(author)

    # Обрабатываем группы
    for cleaned_name, author_list in grouped.items():
        if len(author_list) > 1:
            # Если группа содержит дубликаты, выбираем автора с минимальным id как основного
            author_list.sort(key=lambda a: a.id)
            main_author = author_list[0]
            # Обновляем имя основного автора, если оно отличается
            if main_author.name != cleaned_name:
                main_author.name = cleaned_name
                db.add(main_author)
                db.commit()  # фиксируем изменения для основного автора
            # Для остальных авторов в группе обновляем связи и удаляем записи
            for dup_author in author_list[1:]:
                db.execute(text("""
                    UPDATE landing_authors
                    SET author_id = :main_id
                    WHERE author_id = :dup_id
                """), {"main_id": main_author.id, "dup_id": dup_author.id})
                db.delete(dup_author)
            db.commit()
        else:
            # Если группа состоит из одного автора, обновляем его имя, если нужно
            only_author = author_list[0]
            if only_author.name != cleaned_name:
                only_author.name = cleaned_name
                db.add(only_author)
                db.commit()
    return {"detail": "Cleanup done. 'Dr.' and 'Prof.' removed and duplicates merged."}