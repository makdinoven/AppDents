import os
import uuid
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException, status


router = APIRouter()

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./assets/img/preview_img")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif"}

DOMAIN = "https://dent-s.com"
def get_absolute_url(filename: str) -> str:
    return f"{DOMAIN}/assets/img/preview_img/{filename}"


@router.post("/photo", status_code=status.HTTP_201_CREATED)
async def upload_photo(file: UploadFile = File(...)):
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid file type")

    unique_filename = f"{uuid.uuid4().hex}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {e}")

    return {"url": get_absolute_url(unique_filename)}
