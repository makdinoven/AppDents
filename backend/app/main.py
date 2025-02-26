from fastapi import FastAPI
from app.api import test, users, landings, authors, courses, payments, parser
from fastapi.middleware.cors import CORSMiddleware
from .db.database import init_db


def create_app() -> FastAPI:
    app = FastAPI()

    origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5173",    
    "http://127.0.0.1",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "https://dent-s.com",
    "https://www.dent-s.com",
    "https://mail.dent-s.com",
]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Подключаем роуты
    app.include_router(test.router, prefix="/test")
    app.include_router(users.router, prefix="/users", tags=["Users"])
    app.include_router(landings.router, prefix="/landings", tags=["Landing"])
    app.include_router(authors.router, prefix="/authors", tags=["Authors"])
    app.include_router(courses.router, prefix="/courses", tags=["Courses"])
    app.include_router(payments.router, prefix="/payments", tags=["Payments"])
    app.include_router(parser.router, prefix="/parser", tags=["Parser"])

    @app.on_event("startup")
    async def startup_event():
        init_db()

    return app

app = create_app()
