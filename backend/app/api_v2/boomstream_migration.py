import os
import re
import logging
from typing import Dict, Any

import boto3
import requests
from fastapi import FastAPI, HTTPException, Query, APIRouter
from botocore.exceptions import BotoCoreError, ClientError


# — Конфиг AWS из ENV —
AWS_REGION = os.getenv("AWS_REGION")
AWS_KEY    = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET = os.getenv("AWS_SECRET_ACCESS_KEY")
S3_BUCKET  = os.getenv("S3_BUCKET")
S3_PUBLIC_URL = os.getenv("S3_PUBLIC_URL")

for var in ("AWS_REGION", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "S3_BUCKET"):
    if not globals()[var]:
        raise RuntimeError(f"Не задано окружение {var}")

# — Инициализируем S3-клиент —
s3 = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_KEY,
    aws_secret_access_key=AWS_SECRET
)

router = APIRouter()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", "_", text)
    text = re.sub(r"[^a-z0-9_\-]", "", text)
    return text


@router.post("/migrate/{project_slug}")
def migrate_project(
        project_slug: str,
        api_key: str = Query(..., alias="api_key")
):
    BOOM_API_BASE = "https://api.boomstream.com/v1"
    # 1) Метаданные проекта
    resp = requests.get(
        f"{BOOM_API_BASE}/projects/{project_slug}",
        headers={"Authorization": f"Bearer {api_key}"}
    )
    if resp.status_code == 404:
        raise HTTPException(404, "Проект не найден")
    resp.raise_for_status()
    meta = resp.json()

    project_dir = slugify(meta.get("title", project_slug))
    results = []

    def process_lesson(lesson: Dict[str, Any], prefix: str):
        link = lesson.get("video_link", "")
        m = re.search(r"/([^/]+)$", link)
        if not m:
            return results.append({"video_link": link, "error": "невалидный slug"})
        vid = m.group(1)

        # download-url
        dl = requests.get(
            f"{BOOM_API_BASE}/videos/{vid}/download-url",
            headers={"Authorization": f"Bearer {api_key}"}
        );
        dl.raise_for_status()
        url = dl.json().get("download_url")
        if not url:
            return results.append({"video_slug": vid, "error": "нет download_url"})

        # стримим и заливаем
        stream = requests.get(url, stream=True);
        stream.raise_for_status()
        key = f"video/{project_dir}/{prefix}/{vid}.mp4".strip("/")
        try:
            s3.upload_fileobj(
                Fileobj=stream.raw,
                Bucket=S3_BUCKET,
                Key=key,
                ExtraArgs={"ContentType": stream.headers.get("content-type", "video/mp4")}
            )
            file_url = f"{S3_PUBLIC_URL}/{key}"
            logging.info(f"Uploaded {key}")
            results.append({"video_slug": vid, "s3_key": key, "url": file_url})
        except (BotoCoreError, ClientError) as e:
            results.append({"video_slug": vid, "error": f"S3: {e}"})

    def traverse(folder: Dict[str, Any], prefix: str):
        name = slugify(folder.get("name", ""))
        newp = f"{prefix}/{name}".strip("/")
        for lesson in folder.get("lessons", []):
            process_lesson(lesson, newp)
        for sub in folder.get("folders", []):
            traverse(sub, newp)

    # корневые уроки
    for lesson in meta.get("lessons", []):
        process_lesson(lesson, project_dir)
    # папки
    for fld in meta.get("folders", []):
        traverse(fld, project_dir)

    return {"project": meta.get("title"), "migrated": results}