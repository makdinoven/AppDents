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

import re
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from collections import defaultdict
from ..db.database import get_db
from ..models.models_v2 import Author

router = APIRouter(prefix="/authors_cleanup", tags=["authors_cleanup"])

def clean_name(name: str) -> str:
    """
    Удаляет префиксы и суффиксы "Dr." и "Prof." (с учетом различных вариантов пробелов и регистра)
    Например:
      "Dr. Enrico Agliardi" -> "Enrico Agliardi"
      "Filippo Fontana  Dr." -> "Filippo Fontana"
      "Nate FarleyDr"       -> "Nate Farley"
    """
    # Удаляем префикс
    cleaned = re.sub(r'^(dr\.?\s*|prof\.?\s*)+', '', name, flags=re.IGNORECASE)
    # Удаляем суффикс
    cleaned = re.sub(r'(\s*(dr\.?|prof\.?))+$', '', cleaned, flags=re.IGNORECASE)
    # Заменяем множественные пробелы одним и обрезаем крайние пробелы
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()

@router.post("/remove_dr_and_prof_and_merge")
def remove_dr_and_prof_and_merge_authors(db: Session = Depends(get_db)):
    """
    1. Группирует всех авторов по очищённому имени (без префиксов/суффиксов "Dr." и "Prof.").
    2. Если для одного очищённого имени найдено более одной записи, оставляет автора с минимальным id,
       обновляет его имя (если требуется) и переводит все связи в landing_authors на него,
       а дубликаты удаляет.
    """
    # Получаем всех авторов
    authors = db.query(Author).all()

    # Группируем авторов по "очищённому" имени
    grouped = defaultdict(list)
    for author in authors:
        cleaned = clean_name(author.name)
        grouped[cleaned].append(author)

    # Обрабатываем каждую группу
    for cleaned_name, authors_list in grouped.items():
        if len(authors_list) == 1:
            # Если только один автор с таким именем, обновляем его имя (если отличается)
            author = authors_list[0]
            if author.name != cleaned_name:
                author.name = cleaned_name
                db.add(author)
        else:
            # Если группа содержит дубликаты, оставляем автора с минимальным id
            authors_list.sort(key=lambda a: a.id)
            main_author = authors_list[0]
            if main_author.name != cleaned_name:
                main_author.name = cleaned_name
                db.add(main_author)
            # Для остальных переводим связи и удаляем их
            for dup_author in authors_list[1:]:
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
        raise HTTPException(status_code=500, detail=f"Error during cleanup: {e}")

    return {"detail": "Cleanup done. 'Dr.' and 'Prof.' removed and duplicates merged."}
