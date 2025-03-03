from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from ..db.database import get_db
from ..services_v2.landing_service  import list_landings, get_landing_detail, create_landing, update_landing
from ..schemas_v2.landing import LandingListResponse, LandingDetailResponse, LandingCreate, LandingUpdate

router = APIRouter()

@router.get("/list", response_model=List[LandingListResponse])
def get_landing_listing(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, gt=0),
    db: Session = Depends(get_db)
):
    landings = list_landings(db, skip=skip, limit=limit)
    return landings

@router.get("/detail/{landing_id}", response_model=LandingDetailResponse)
def get_landing_by_id(landing_id: int, db: Session = Depends(get_db)):
    landing = get_landing_detail(db, landing_id)
    return landing

@router.post("/", response_model=LandingListResponse)
def create_new_landing(
    landing_data: LandingCreate,
    db: Session = Depends(get_db)
):
    new_landing = create_landing(db, landing_data)
    return new_landing

@router.put("/{landing_id}", response_model=LandingDetailResponse)
def update_landing_full(
    landing_id: int,
    update_data: LandingUpdate,
    db: Session = Depends(get_db)
):
    updated_landing = update_landing(db, landing_id, update_data)
    return updated_landing
