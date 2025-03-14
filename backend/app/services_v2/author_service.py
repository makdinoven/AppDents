from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..models.models_v2 import Author
from ..schemas_v2.author import AuthorCreate, AuthorUpdate


def list_authors_simple(db: Session) -> List[Author]:
    return db.query(Author.id, Author.name).all()

def get_author_detail(db: Session, author_id: int) -> Author:
    author = db.query(Author).filter(Author.id == author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    return author

def create_author(db: Session, author_data: AuthorCreate) -> Author:
    new_author = Author(
        name=author_data.name,
        description=author_data.description,
        photo=author_data.photo
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