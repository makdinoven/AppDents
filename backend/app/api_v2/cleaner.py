from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.database import get_async_db, SessionLocal
from ..services_v2.cleaner_service import  clean_landings_old_data
from ..services_v2.migration_service import run_migration, migrate_courses, migrate_landings, migrate_users

router = APIRouter()

@router.post("/clean/landings")
async def clean_landings_data(db: AsyncSession = Depends(get_async_db)):
    """
    Роут для очистки HTML-тегов в полях таблицы landings_old.
    Запускается процесс выборки всех записей, очистки нужных полей и обновления данных.
    """
    try:
        result = await clean_landings_old_data(db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при очистке данных: {str(e)}")

@router.post("/migrate")
async def run_migration(db: AsyncSession = Depends(get_async_db)) -> dict:
    """
    Запускает миграцию в следующем порядке:
      1. courses_old → courses,
      2. landings_old → landings (+ landing_course, landing_authors),
      3. users_old → users (+ users_courses).
    Это гарантирует, что при создании записей в landing_course все курсы уже существуют.
    """
    try:
        courses_migrated = await migrate_courses(db)
        landings_migrated = await migrate_landings(db)
        users_migrated = await migrate_users(db)
        return {
            "courses_migrated": courses_migrated,
            "landings_migrated": landings_migrated,
            "users_migrated": users_migrated
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Migration error: {str(e)}")