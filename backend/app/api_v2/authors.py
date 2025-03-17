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
    Удаляет префиксы и суффиксы "Dr." и "Prof." независимо от регистра и лишних пробелов.
    Примеры:
      "Dr. Enrico Agliardi" -> "Enrico Agliardi"
      "Filippo Fontana  Dr." -> "Filippo Fontana"
      "Nate FarleyDr"       -> "Nate Farley"
      "DrEnrico"           -> "Enrico"
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
    1. Загружает всех авторов и вычисляет очищённое имя (без "Dr." и "Prof.").
    2. Группирует записи по этому имени.
    3. Для групп с дубликатами:
         - Если уже существует запись с name равным очищённому, она становится основным.
         - Иначе выбирается запись с минимальным id, и её имя обновляется до очищённого.
         - Для остальных записей в группе:
             - Обновляются связи в таблице landing_authors (замена их author_id на id основного автора)
             - Удаляются дубликатные записи.
    4. Для групп с единственной записью, если имя отличается от очищённого – обновляется.
    """
    authors = db.query(Author).all()
    grouped = defaultdict(list)
    for author in authors:
        cleaned = clean_name(author.name)
        grouped[cleaned].append(author)

    for cleaned_name, group in grouped.items():
        if len(group) > 1:
            # Если есть более одной записи с этим очищённым именем
            # Попытаемся найти запись, у которой имя уже равно cleaned_name
            main_author = None
            for a in group:
                if a.name == cleaned_name:
                    main_author = a
                    break
            # Если ни одна запись не имеет уже очищённое имя – выбираем автора с минимальным id
            if main_author is None:
                main_author = min(group, key=lambda a: a.id)
                # Обновляем имя основного автора только если его имя отличается
                main_author.name = cleaned_name
                db.add(main_author)
                try:
                    db.commit()
                except Exception as e:
                    db.rollback()
                    raise HTTPException(status_code=500, detail=f"Error updating main author: {e}")


            # Для всех остальных записей в группе обновляем связи и удаляем их
            for dup_author in group:
                if dup_author.id == main_author.id:
                    continue
                # Обновляем связи в таблице landing_authors
                db.execute(text("""
                    UPDATE landing_authors
                    SET author_id = :main_id
                    WHERE author_id = :dup_id
                """), {"main_id": main_author.id, "dup_id": dup_author.id})
                db.delete(dup_author)
            try:
                db.commit()
            except Exception as e:
                db.rollback()
                raise HTTPException(status_code=500, detail=f"Error merging duplicates: {e}")
        else:
            # Группа из одной записи – если имя отличается, обновляем
            only_author = group[0]
            if only_author.name != cleaned_name:
                only_author.name = cleaned_name
                db.add(only_author)
                try:
                    db.commit()
                except Exception as e:
                    db.rollback()
                    raise HTTPException(status_code=500, detail=f"Error updating author: {e}")

    return {"detail": "Cleanup done. 'Dr.' and 'Prof.' removed and duplicates merged."}