from sqlalchemy.orm import Session
from typing import List
from ..models.models_v2 import Author

def list_authors_simple(db: Session) -> List[Author]:
    return db.query(Author.id, Author.name).all()
