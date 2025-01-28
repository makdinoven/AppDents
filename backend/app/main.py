
import uvicorn
from fastapi import FastAPI
from app.models.models import Base
from app.db.database import engine
from app.api import test, users


def create_app() -> FastAPI:
    app = FastAPI(title="My Courses API")

    # Создаём таблицы (только если не используете Alembic)
    Base.metadata.create_all(bind=engine)

    # Подключаем роуты
    app.include_router(test.router, prefix="")  # /test
    app.include_router(users.router, prefix="/users")  # /users

    return app


app = create_app()

