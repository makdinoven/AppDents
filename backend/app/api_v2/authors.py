import re
import unicodedata
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


def basic_clean_name(name: str) -> str:
    """
    Убирает из строки name приставки/суффиксы Dr./Prof. (в любом регистре) и множественные пробелы.
    Примеры:
      "Dr. Enrico Agliardi"  -> "Enrico Agliardi"
      "Filippo Fontana  Dr." -> "Filippo Fontana"
      "Kent HowellDr"        -> "Kent Howell"
      "DrEnrico"             -> "Enrico"
    """
    # Удаляем возможные префиксы Dr./Prof. в начале
    cleaned = re.sub(r'^(?:dr\.?\s*|prof\.?\s*)+', '', name, flags=re.IGNORECASE)
    # Удаляем возможные суффиксы Dr./Prof. в конце
    cleaned = re.sub(r'(?:\s*(?:dr\.?|prof\.?))+$', '', cleaned, flags=re.IGNORECASE)
    # Заменяем множественные пробелы одним
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

# ----- Шаг 2: функция для «глубокой» нормализации, чтобы учитывать акценты и т. д. -----

def normalize_for_key(s: str) -> str:
    """
    Приводит строку s к виду, который максимально нейтрализует различия,
    которые MySQL колляция (case-insensitive, accent-insensitive и т.п.) может считать «одинаковыми».

    1. Удаляем префиксы Dr./Prof., лишние пробелы (через basic_clean_name).
    2. Приводим к NFKD (или NFKC) unicode формату, чтобы отделить диакритику (акценты) от базовых символов.
    3. Убираем все Combining Marks (напр. акценты, тильды), чтобы "Mãlo" -> "Malo".
    4. Приводим всё к нижнему регистру.
    5. (Опционально) можно убрать и другие невидимые символы (ZERO WIDTH SPACE и пр.).
    """
    # Сначала обычная очистка Dr./Prof.
    cleaned = basic_clean_name(s)

    # Нормализуем в NFKD (или NFKC — смотрите, что подходит для ваших данных)
    normed = unicodedata.normalize('NFKD', cleaned)
    # Убираем символы, принадлежащие категории "Mn" (Mark, Nonspacing), т.е. акценты, тильды и т.д.
    # Превращаем результат обратно в str
    without_accents = ''.join(ch for ch in normed if unicodedata.category(ch) != 'Mn')

    # Приводим к нижнему регистру
    lowercased = without_accents.lower()

    # Можно убрать «длинные» пробелы или невидимые символы, если боитесь, что они затесались:
    # Для простоты ограничимся trim() и заменим множественные пробелы на один
    final = re.sub(r'\s+', ' ', lowercased).strip()

    return final

# ----- Основной роут -----

@router.post("/remove_dr_and_prof_and_merge")
def remove_dr_and_prof_and_merge(db: Session = Depends(get_db)):
    """
    1. Считываем всех авторов.
    2. Для каждого считаем «ключ нормализации» (normalize_for_key).
    3. Группируем авторов по этому ключу.
    4. Для каждой группы (т. е. «по сути одинаковые» имена с точки зрения колляции):
       - Определяем «финальное» имя, которое хотим записать в authors.name,
         например: делаем .title() от «очищенной строки без акцентов» (или оставляем как-то иначе).
       - Проверяем, нет ли уже в базе (вне этой группы) автора с таким финальным именем:
         * Если есть, он станет «главным».
         * Если нет, возьмём автора с минимальным id из группы и проставим ему финальное имя.
       - Остальных авторов в группе сливаем: переносим связи landing_authors и удаляем из authors.
    5. Один общий commit в конце.
    """

    all_authors = db.query(Author).all()

    # Сгруппируем их по «ключу нормализации»
    grouped = defaultdict(list)
    for author in all_authors:
        group_key = normalize_for_key(author.name)
        grouped[group_key].append(author)

    # Готовим список всех операций по слиянию
    for group_key, authors_list in grouped.items():
        # Определим «очищенное» имя (без Dr./Prof., без лишних пробелов, но ещё до удаления акцентов)
        # Можно использовать просто basic_clean_name(authors_list[0].name)
        # Но для красоты возьмём «оригинал» первого автора, почистим Dr./Prof., пробелы:
        raw_cleaned = basic_clean_name(authors_list[0].name)

        # Определяем «финальное» имя для записи в БД
        # Например, сделаем каждое слово с заглавной буквы (title).
        # Если вам важен регистр «как в оригинале», можно придумать другую логику.
        final_name = raw_cleaned.title()

        # 1) Сначала проверяем: нет ли уже в БД (среди всех авторов, не только в этой группе)
        #    автора с таким именем. Если он есть, возьмём его как «главного».
        #    Почему это нужно? Потому что могли быть случаи, когда в БД уже существует
        #    какая-то запись c name = "Paulo Malo", а наши авторы были "dr. paulo malo" и "Paulo  Malo" и т.д.
        existing_main = (
            db.query(Author)
              .filter(Author.name == final_name)
              .first()
        )

        if existing_main:
            # Этот existing_main — может быть, даже не в нашей группе,
            # но мы хотим «слить» наших авторов на него.
            main_author = existing_main
        else:
            # Иначе берём автора с минимальным id в группе
            main_author = min(authors_list, key=lambda a: a.id)
            # Если у него имя != final_name, назначаем
            if main_author.name != final_name:
                main_author.name = final_name
                db.add(main_author)
                # Не коммитим пока, делаем всё в одной транзакции

        # 2) Теперь переносим связи у всех остальных авторов в группе на main_author
        for dup in authors_list:
            if dup.id == main_author.id:
                continue
            db.execute(
                text("""
                    UPDATE landing_authors
                    SET author_id = :main_id
                    WHERE author_id = :dup_id
                """),
                {"main_id": main_author.id, "dup_id": dup.id}
            )
            db.delete(dup)

    # Когда все группы обработаны, делаем один общий commit
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при финальном сохранении: {exc}"
        )

    return {"detail": "Очистка и слияние авторов завершены."}