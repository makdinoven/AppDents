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
    api_key: str = Query(..., alias="api_key", description="BoomStream API key для этого проекта")
):
    """
    Мигрирует все видео из проекта BoomStream в ваш S3.
    project_slug  — идентификатор проекта в BoomStream,
    api_key       — API-ключ для этого проекта.
    """
    BOOM_API_BASE = "https://api.boomstream.com/v1"

    # 1) Получаем метаданные проекта
    resp = requests.get(
        f"{BOOM_API_BASE}/projects/{project_slug}",
        headers={"Authorization": f"Bearer {api_key}"}
    )
    if resp.status_code == 404:
        raise HTTPException(404, detail="Проект не найден в BoomStream")
    resp.raise_for_status()
    meta = resp.json()  # Ожидаем: {"title": "...", "folders": [...], "lessons": [...]}

    project_title = meta.get("title") or project_slug
    project_dir   = slugify(project_title)
    results: list = []

    def process_lesson(lesson: Dict[str, Any], prefix: str):
        link = lesson.get("video_link")
        if not link:
            results.append({ "path": prefix, "error": "нет video_link" })
            return

        m = re.search(r"/([^/]+)$", link)
        if not m:
            results.append({ "video_link": link, "error": "не распознан slug видео" })
            return

        video_slug = m.group(1)
        try:
            # 2) Запрашиваем download_url
            dl_resp = requests.get(
                f"{BOOM_API_BASE}/videos/{video_slug}/download-url",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            dl_resp.raise_for_status()
            download_url = dl_resp.json().get("download_url")
            if not download_url:
                raise ValueError("download_url отсутствует в ответе")

            # 3) Стримим видео
            stream = requests.get(download_url, stream=True)
            stream.raise_for_status()

            # 4) Загружаем в S3
            key = f"video/{project_dir}/{prefix}/{video_slug}.mp4".strip("/")
            s3.upload_fileobj(
                Fileobj   = stream.raw,
                Bucket    = S3_BUCKET,
                Key       = key,
                ExtraArgs = {"ContentType": stream.headers.get("content-type", "video/mp4")}
            )

            url = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{key}"
            logger.info(f"[OK] {key}")
            results.append({
                "video_slug": video_slug,
                "s3_key":     key,
                "url":        url
            })

        except (requests.HTTPError, ValueError) as e:
            logger.error(f"BoomStream error ({video_slug}): {e}")
            results.append({ "video_slug": video_slug, "error": f"BoomStream: {e}" })
        except (BotoCoreError, ClientError) as e:
            logger.error(f"S3 error ({video_slug}): {e}")
            results.append({ "video_slug": video_slug, "error": f"S3: {e}" })

    def traverse_folder(folder: Dict[str, Any], cur_prefix: str):
        name = slugify(folder.get("name", ""))
        new_prefix = f"{cur_prefix}/{name}".strip("/")
        for lesson in folder.get("lessons", []):
            process_lesson(lesson, new_prefix)
        for sub in folder.get("folders", []):
            traverse_folder(sub, new_prefix)

    # Обрабатываем корневые уроки
    for lesson in meta.get("lessons", []):
        process_lesson(lesson, project_dir)

    # Рекурсивно обходим папки
    for folder in meta.get("folders", []):
        traverse_folder(folder, project_dir)

    return {
        "project":  project_title,
        "migrated": results
    }
