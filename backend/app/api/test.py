from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class TestResponse(BaseModel):
    message: str

@router.get("/test/", response_model=TestResponse)
def read_test_slash():
    return {"message": "Hello, World!"}


@router.get("/test", response_model=TestResponse)
def read_test_no_slash():
    return {"message": "Hello, World!"}
