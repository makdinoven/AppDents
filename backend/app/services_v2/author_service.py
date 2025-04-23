from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from ..models.models_v2 import Author
from ..schemas_v2.author import AuthorCreate, AuthorUpdate


def list_authors_simple(db: Session, language: Optional[str] = None) -> List[dict]:
    query = db.query(Author.id, Author.name, Author.language, Author.photo)
    if language:
        query = query.filter(Author.language == language)
    authors = query.all()
    # Преобразуем результат в список словарей
    return [{"id": a.id, "name": a.name, "language": a.language, "photo": a.photo} for a in authors]

def get_author_detail(db: Session, author_id: int) -> Author:
    author = db.query(Author).filter(Author.id == author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    return author

def create_author(db: Session, author_data: AuthorCreate) -> Author:
    new_author = Author(
        name=author_data.name,
        description=author_data.description,
        photo=author_data.photo,
        language=author_data.language  # устанавливаем язык
    )
    db.add(new_author)
    db.commit()
    db.refresh(new_author)
    return new_author

def update_author(db: Session, author_id: int, update_data: AuthorUpdate) -> Author:
    author = db.query(Author).filter(Author.id == author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    if update_data.name is not None:
        author.name = update_data.name
    if update_data.description is not None:
        author.description = update_data.description
    if update_data.photo is not None:
        author.photo = update_data.photo
    if update_data.language is not None:
        author.language = update_data.language
    db.commit()
    db.refresh(author)
    return author

def delete_author(db: Session, author_id: int) -> None:
    author = db.query(Author).filter(Author.id == author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    # Очистка связи с лендингами (ассоциативная таблица landing_authors)
    author.landings = []
    db.delete(author)
    db.commit()

def get_author_full_detail(db: Session, author_id: int) -> dict:
    # Достаём автора вместе с лендингами, тегами и курсами
    author = (
        db.query(Author)
          .filter(Author.id == author_id)
          .first()
    )
    if not author:
        return None

    # Подготовим данные по каждому лендингу
    landings_data = []
    all_course_ids = set()
    total_new_price = 0.0
    total_old_price = 0.0

    for l in author.landings:
        # Приводим новую цену к float
        try:
            price = float(l.new_price)
            old_price = float(l.old_price)
        except Exception:
            price = 0.0
            old_price = 0.0
        total_new_price += price
        total_old_price += old_price

        # Список курсов в этом лендинге
        course_ids = [c.id for c in l.courses]
        all_course_ids.update(course_ids)

        # Список авторов этого лендинга
        authors_info = [
            {
                "id": a.id,
                "name": a.name,
                "photo": a.photo
            }
            for a in l.authors
        ]

        landings_data.append({
            "id": l.id,
            "landing_name": l.landing_name,
            "slug": l.page_name,
            "old_price": l.old_price,
            "new_price": l.new_price,
            "main_image": l.preview_photo,
            "first_tag": l.tags[0].name if l.tags else None,
            "course_ids": course_ids,
            "authors": authors_info,
        })

    return {
        "id": author.id,
        "name": author.name,
        "description": author.description,
        "photo": author.photo,
        "language": author.language,
        "landings": landings_data,
        "course_ids": list(all_course_ids),
        "total_new_price": total_new_price,
        "total_old_price": total_old_price,
        "landing_count": len(landings_data),
    }
