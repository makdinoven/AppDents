from sys import prefix
from fastapi import FastAPI
from app.models.models import Base
from app.db.database import engine
from app.api import test, users, landings, authors, courses, payments

def create_app() -> FastAPI:
    app = FastAPI()

    # Подключаем роуты
    app.include_router(test.router, prefix="")
    app.include_router(users.router, prefix="/users", tags=["Users"])
    app.include_router(landings.router, prefix="/landings", tags=["Landing"])
    app.include_router(authors.router, prefix="/authors", tags=["Authors"])
    app.include_router(courses.router, prefix="/courses", tags=["Courses"])
    app.include_router(payments.router, prefix="/payments", tags=["Payments"])

    return app

app = create_app()
