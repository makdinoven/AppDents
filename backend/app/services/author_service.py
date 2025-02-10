# services/authors.py
from typing import List

from sqlalchemy.orm import Session
from ..models.models import Author
from ..schemas.author import AuthorCreate, AuthorUpdate

def create_author(db: Session, author_data: AuthorCreate) -> Author:
    author = Author(
        name=author_data.name,
        description=author_data.description,
        photo=author_data.photo
    )
    db.add(author)
    db.commit()
    db.refresh(author)
    return author

def update_author(db: Session, author_id: int, author_data: AuthorUpdate) -> Author:
    author = db.query(Author).filter(Author.id == author_id).first()
    if not author:
        raise ValueError("Автор не найден")
    if author_data.name is not None:
        author.name = author_data.name
    if author_data.description is not None:
        author.description = author_data.description
    if author_data.photo is not None:
        author.photo = author_data.photo
    db.commit()
    db.refresh(author)
    return author

def delete_author(db: Session, author_id: int) -> Author:
    author = db.query(Author).filter(Author.id == author_id).first()
    if not author:
        raise ValueError("Автор не найден")
    db.delete(author)
    db.commit()
    return author

def search_authors(db: Session, query: str) -> List[Author]:
    """
    Выполняет поиск авторов по части имени (регистронезависимый поиск).
    """
    # Используем оператор ilike для регистронезависимого поиска
    authors = db.query(Author).filter(Author.name.ilike(f"%{query}%")).all()
    return authors
