
from fastapi import FastAPI
from .api_v2 import users, courses, landings, authors, photo, stripe, wallet, boomstream_migration, cart, helpers, \
    health_checkers, smart_validations, clip_generator, slider, books, search
from fastapi.middleware.cors import CORSMiddleware

from .db.database import init_db
from .services_v2 import wallet_service


def create_app() -> FastAPI:
    app = FastAPI()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(users.router, prefix="/api/users", tags=["users"])
    app.include_router(courses.router, prefix="/api/courses", tags=["courses"])
    app.include_router(landings.router, prefix="/api/landings", tags=["landings"])
    app.include_router(authors.router, prefix="/api/authors", tags=["authors"])
    app.include_router(photo.router, prefix="/api/photo", tags=["photo"])
    app.include_router(stripe.router, prefix="/api/stripe", tags=["stripe"])
    app.include_router(wallet.router, prefix="/api/wallet", tags=["wallet"])
    app.include_router(cart.router, prefix="/api/cart", tags=["cart"])
    app.include_router(books.router, prefix="/api/books", tags=["books"])
    app.include_router(slider.router, prefix="/api/slider", tags=["slider"])
    app.include_router(clip_generator.router, prefix="/api/clip_generator", tags=["clip_generator"])
    app.include_router(smart_validations.router, prefix="/api/validations", tags=["smart_validations"])

    app.include_router(boomstream_migration.router, prefix="/api/boomstream", tags=["boomstream"])

    app.include_router(helpers.router, prefix="/api/helpers", tags=["helpers"])

    app.include_router(health_checkers.router, prefix="/api/healthcheckers", tags=["Health Checkers"])

    app.include_router(search.router, prefix="/api/search", tags=["search"])


    @app.on_event("startup")
    def on_startup():
        init_db()

    return app



app = create_app()
