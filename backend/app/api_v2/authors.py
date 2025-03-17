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
    Удаляет из строки name приставки/суффиксы 'Dr.' или 'Prof.' (с любым регистром и пробелами).
    Примеры:
      "Dr. Enrico Agliardi"  -> "Enrico Agliardi"
      "Filippo Fontana  Dr." -> "Filippo Fontana"
      "Kent HowellDr"        -> "Kent Howell"
    """
    # Удаляем возможные префиксы Dr./Prof. в начале
    cleaned = re.sub(r'^(?:dr\.?\s*|prof\.?\s*)+', '', name, flags=re.IGNORECASE)
    # Удаляем возможные суффиксы Dr./Prof. в конце
    cleaned = re.sub(r'(?:\s*(?:dr\.?|prof\.?))+$', '', cleaned, flags=re.IGNORECASE)
    # Заменяем множественные пробелы одним
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

@router.post("/remove_dr_and_prof_and_merge")
def remove_dr_and_prof_and_merge_authors(db: Session = Depends(get_db)):
    """
    1. Считывает всех авторов из БД.
    2. «Очищает» имена от 'Dr.'/'Prof.' и приводит к нижнему регистру, чтобы сформировать ключ группировки.
    3. Для каждой группы авторов:
        - Определяем «финальное» имя (например, делаем title() от ключа группировки).
        - Находим «главного» автора:
            * Если кто-то уже имеет это finаl_name — берём его.
            * Иначе берём автора с min(id) и присваиваем ему final_name.
        - Остальных авторов «сливаем» (обновляем landing_authors, удаляем их из authors).
    4. Делаем commit один раз в самом конце, чтобы не было промежуточных конфликтов.
    """
    all_authors = db.query(Author).all()

    # Сформируем словарь: ключ = cleaned_name.lower(), значение = список Author
    grouped_authors = defaultdict(list)
    for author in all_authors:
        # Очищенное имя без Dr./Prof.
        base_clean = clean_name(author.name)
        # Приводим к нижнему регистру, чтобы учесть возможные отличия в регистре
        group_key = base_clean.lower()
        grouped_authors[group_key].append(author)

    # Перебираем группы
    for group_key, authors_list in grouped_authors.items():
        # Определим «финальное» имя, которое хотим хранить в поле name
        # Например, делаем каждое слово с заглавной буквы (title):
        final_name = group_key.title()  # "paulo malo" -> "Paulo Malo"

        # Ищем в этой группе автора, у которого уже установлено имя == final_name
        main_author = None
        for a in authors_list:
            if a.name == final_name:
                main_author = a
                break

        # Если в группе нет автора с таким именем, берём автора с минимальным id
        # и назначаем ему final_name (только если не совпадает)
        if not main_author:
            main_author = min(authors_list, key=lambda a: a.id)
            if main_author.name != final_name:
                main_author.name = final_name
                db.add(main_author)
                # Заметим, что пока не коммитим отдельно

        # Теперь сливаем остальных авторов из группы
        for a in authors_list:
            if a.id == main_author.id:
                continue  # пропускаем «главного»

            # Перенести все связи из landing_authors на main_author
            db.execute(
                text("""
                    UPDATE landing_authors
                    SET author_id = :main_id
                    WHERE author_id = :dup_id
                """),
                {"main_id": main_author.id, "dup_id": a.id}
            )
            # Удалить «дубликатного» автора
            db.delete(a)

    # Теперь, когда все группы обработаны, делаем один коммит.
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при финальном сохранении: {e}"
        )

    return {"detail": "Очистка завершена: Dr./Prof. удалены, дубликаты объединены."}