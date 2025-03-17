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
    Удаляет из строки `name` приставки и суффиксы Dr./Prof. (игнорируя регистр и пробелы).
    Убирает множественные пробелы.
    Примеры:
      "Dr. Enrico Agliardi"     -> "Enrico Agliardi"
      "Filippo Fontana  Dr."    -> "Filippo Fontana"
      "Nate FarleyDr"           -> "Nate Farley"
      "DrEnrico"                -> "Enrico"
    """
    # Удаляем префикс(ы) "Dr." или "Prof." в начале строки
    cleaned = re.sub(r'^(?:dr\.?\s*|prof\.?\s*)+', '', name, flags=re.IGNORECASE)
    # Удаляем суффикс(ы) "Dr." или "Prof." в конце строки
    cleaned = re.sub(r'(?:\s*(?:dr\.?|prof\.?))+$', '', cleaned, flags=re.IGNORECASE)
    # Заменяем множественные пробелы одним пробелом
    cleaned = re.sub(r'\s+', ' ', cleaned)
    # Убираем пробелы по краям
    return cleaned.strip()


@router.post("/remove_dr_and_prof_and_merge")
def remove_dr_and_prof_and_merge_authors(db: Session = Depends(get_db)):
    """
    1. Загружает всех авторов и вычисляет «очищённое» имя (без "Dr." и "Prof.").
    2. Группирует записи по этому очищённому имени (но с учётом приведения к нижнему регистру
       для избежания проблемы, когда в БД могут быть имена, отличающиеся только регистром).
    3. Для групп с дубликатами:
         - Если уже существует запись с name равным очищённому, она становится «главной».
         - Иначе выбирается запись с минимальным id, и её имя обновляется до «очищённого».
         - Для остальных записей в группе:
             - Обновляются связи в таблице `landing_authors` (замена их `author_id` на id «главного» автора).
             - Удаляются дубликатные записи из таблицы `authors`.
    4. Для групп с единственной записью, если имя отличается от «очищённого»:
         - Проверяем, нет ли в таблице `authors` уже автора с таким «очищённым» именем
           (чтобы избежать конфликта уникального индекса).
           - Если есть — переносим связи на уже существующего и удаляем текущего.
           - Если нет — просто обновляем имя текущего автора.
    """

    # 1. Считываем всех авторов
    authors = db.query(Author).all()

    # 2. Группируем по «очищённому» имени, но в нижнем регистре для ключа
    grouped = defaultdict(list)
    for author in authors:
        raw_cleaned = clean_name(author.name)
        grouping_key = raw_cleaned.lower()  # ключ группировки
        grouped[grouping_key].append(author)

    # 3-4. Обрабатываем группы
    for grouping_key, group in grouped.items():
        # «эталонное» очищённое имя без Dr./Prof. (в том виде, как хотим хранить его в БД)
        # Здесь используем имя первого автора, «очищенное» от приставок:
        # Или, например, можно взять у автора с минимальным id — на ваше усмотрение
        cleaned_name = clean_name(group[0].name)

        if len(group) > 1:
            # --- Группа с дубликатами ---
            # Пытаемся найти автора, у которого уже name == cleaned_name
            main_author = None
            for a in group:
                if a.name == cleaned_name:
                    main_author = a
                    break

            # Если никто из группы не имеет совпадающее имя — выбираем автора с минимальным id
            if main_author is None:
                main_author = min(group, key=lambda a: a.id)
                # Обновляем имя «главного» автора (только если отличается)
                if main_author.name != cleaned_name:
                    main_author.name = cleaned_name
                    db.add(main_author)
                    try:
                        db.commit()
                    except Exception as e:
                        db.rollback()
                        raise HTTPException(
                            status_code=500,
                            detail=f"Ошибка при обновлении имени основного автора (id={main_author.id}): {e}"
                        )

            # Все остальные авторы в группе сливаем на main_author
            for dup_author in group:
                if dup_author.id == main_author.id:
                    continue
                # Переносим связи из landing_authors
                db.execute(
                    text("""
                        UPDATE landing_authors
                        SET author_id = :main_id
                        WHERE author_id = :dup_id
                    """),
                    {"main_id": main_author.id, "dup_id": dup_author.id}
                )
                # Удаляем «дубликатного» автора
                db.delete(dup_author)

            try:
                db.commit()
            except Exception as e:
                db.rollback()
                raise HTTPException(
                    status_code=500,
                    detail=f"Ошибка при слиянии дубликатов для имени '{cleaned_name}': {e}"
                )

        else:
            # --- Группа из одного автора ---
            only_author = group[0]
            raw_cleaned = clean_name(only_author.name)
            # Если имя уже совпадает с «очищённым», ничего делать не нужно
            if only_author.name == raw_cleaned:
                continue

            # Иначе нужно обновить имя, но сначала проверить,
            # нет ли уже другого автора с таким именем (во избежание Duplicate entry)
            existing_author = (
                db.query(Author)
                .filter(Author.name == raw_cleaned)
                .first()
            )
            if existing_author and existing_author.id != only_author.id:
                # Значит, такой автор уже есть в БД:
                # Сливаем (переносим связи и удаляем текущего)
                db.execute(
                    text("""
                        UPDATE landing_authors
                        SET author_id = :main_id
                        WHERE author_id = :dup_id
                    """),
                    {"main_id": existing_author.id, "dup_id": only_author.id}
                )
                db.delete(only_author)
            else:
                # Просто переименовываем
                only_author.name = raw_cleaned
                db.add(only_author)

            try:
                db.commit()
            except Exception as e:
                db.rollback()
                raise HTTPException(
                    status_code=500,
                    detail=f"Ошибка при обновлении (или слиянии) автора id={only_author.id}: {e}"
                )

    return {"detail": "Очистка завершена. Приставки Dr./Prof. удалены, дубликаты объединены."}