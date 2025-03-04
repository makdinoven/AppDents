from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from ..db.database import get_db
from ..schemas_v2.author import AuthorSimpleResponse
from ..services_v2.author_service import list_authors_simple

router = APIRouter()

@router.get("/", response_model=List[AuthorSimpleResponse])
def get_authors(db: Session = Depends(get_db)):
    return list_authors_simple(db)
