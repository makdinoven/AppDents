
from fastapi import FastAPI
from .api_v2 import users, courses, landings, authors, photo, stripe, wallet, boomstream_migration, cart, helpers, \
    health_checkers
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

    # # Подключаем роуты
    # app.include_router(test.router, prefix="")
    # app.include_router(users.router, prefix="/users", tags=["Users"])
    # app.include_router(landings.router, prefix="/landings", tags=["Landing"])
    # app.include_router(authors.router, prefix="/authors", tags=["Authors"])
    # app.include_router(courses.router, prefix="/courses", tags=["CoursesSection"])
    # app.include_router(payments.router, prefix="/payments", tags=["Payments"])
    # app.include_router(parser.router, prefix="/parser", tags=["Parser"])
    # app.include_router(cleaner.router, prefix="/cleaner", tags=["Cleaner"])
    # app.include_router(transfer.router, prefix="/transfer", tags=["Transfer"])

    # app.include_router(cleaner.router, prefix="/api/cleaner", tags=["cleaner"])
    app.include_router(users.router, prefix="/api/users", tags=["users"])
    app.include_router(courses.router, prefix="/api/courses", tags=["courses"])
    app.include_router(landings.router, prefix="/api/landings", tags=["landings"])
    app.include_router(authors.router, prefix="/api/authors", tags=["authors"])
    app.include_router(photo.router, prefix="/api/photo", tags=["photo"])
    app.include_router(stripe.router, prefix="/api/stripe", tags=["stripe"])
    app.include_router(wallet.router, prefix="/api/wallet", tags=["wallet"])

    app.include_router(cart.router, prefix="/api/cart", tags=["cart"])

    app.include_router(boomstream_migration.router, prefix="/api/boomstream", tags=["boomstream"])

    app.include_router(helpers.router, prefix="/api/helpers", tags=["helpers"])

    app.include_router(health_checkers.router, prefix="/api/healthcheckers", tags=["Health Checkers"])



    # app.include_router(utils.router, prefix="/api/utils", tags=["utils"])
    # app.include_router(migrate_user.router, prefix="/api/migrate", tags=["migrate"])
    #
    # app.include_router(tilda_migrate.router, prefix="/api/tilda", tags=["new_server_tilda"])

    @app.on_event("startup")
    def on_startup():
        init_db()

    return app



app = create_app()
