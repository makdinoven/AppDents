from sys import prefix
from fastapi import FastAPI
# from app.api import test, users, landings, authors, courses, payments, parser, cleaner, transfer
from .api_v2 import cleaner, users, courses, landings, authors, photo, stripe
from fastapi.middleware.cors import CORSMiddleware
from .db.database import init_db


def create_app() -> FastAPI:
    app = FastAPI()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # # Подключаем роуты
    # app.include_router(test.router, prefix="")
    # app.include_router(users.router, prefix="/users", tags=["Users"])
    # app.include_router(landings.router, prefix="/landings", tags=["Landing"])
    # app.include_router(authors.router, prefix="/authors", tags=["Authors"])
    # app.include_router(courses.router, prefix="/courses", tags=["Courses"])
    # app.include_router(payments.router, prefix="/payments", tags=["Payments"])
    # app.include_router(parser.router, prefix="/parser", tags=["Parser"])
    # app.include_router(cleaner.router, prefix="/cleaner", tags=["Cleaner"])
    # app.include_router(transfer.router, prefix="/transfer", tags=["Transfer"])

    app.include_router(cleaner.router, prefix="/api/cleaner", tags=["cleaner"])
    app.include_router(users.router, prefix="/api/users", tags=["users"])
    app.include_router(courses.router, prefix="/api/courses", tags=["courses"])
    app.include_router(landings.router, prefix="/api/landings", tags=["landings"])
    app.include_router(authors.router, prefix="/api/authors", tags=["authors"])
    app.include_router(photo.router, prefix="/api/photo", tags=["photo"])
    app.include_router(stripe.router, prefix="/api/stripe", tags=["stripe"])

    @app.on_event("startup")
    async def startup_event():
        init_db()

    return app

app = create_app()
