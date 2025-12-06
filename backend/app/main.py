
from fastapi import FastAPI
from .api_v2 import users, courses, landings, authors, photo, stripe, wallet, boomstream_migration, cart, helpers, \
    health_checkers, smart_validations, clip_generator, slider, books, book_admin, media, search, book_metadata, \
    ad_control, book_ad_control, policy, video_repair, creatives, book_assets, summary_generator,course_request, filters

from fastapi.middleware.cors import CORSMiddleware
from .middlewares.rate_limiter import RateLimitMiddleware
from .middlewares.monitoring import MonitoringMiddleware

from .db.database import init_db
from .services_v2 import wallet_service


def create_app() -> FastAPI:
    app = FastAPI()

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Rate Limiting: 100 запросов в минуту с одного IP (Sliding Window)
    # Исключения: пути, которые не подлежат rate limiting
    excluded_paths = [
        r"^/api/books/\d+/pdf$",  # Скачивание PDF книг
        r"^/api/validations/check-email$",  # Проверка email
    ]
    app.add_middleware(
        RateLimitMiddleware, 
        max_requests=100, 
        window_seconds=60,
        excluded_paths=excluded_paths
    )
    
    # Monitoring: отслеживание ошибок и медленных запросов
    app.add_middleware(MonitoringMiddleware)
    app.include_router(users.router, prefix="/api/users", tags=["users"])
    app.include_router(courses.router, prefix="/api/courses", tags=["courses"])
    app.include_router(landings.router, prefix="/api/landings", tags=["landings"])
    app.include_router(authors.router, prefix="/api/authors", tags=["authors"])
    app.include_router(photo.router, prefix="/api/photo", tags=["photo"])
    app.include_router(media.router, prefix="/api/media", tags=["media"])
    app.include_router(stripe.router, prefix="/api/stripe", tags=["stripe"])
    app.include_router(wallet.router, prefix="/api/wallet", tags=["wallet"])
    app.include_router(cart.router, prefix="/api/cart", tags=["cart"])
    app.include_router(books.router, prefix="/api/books", tags=["books"])
    app.include_router(book_admin.router, prefix="/api/book_admin", tags=["book_admin"])
    app.include_router(filters.router, prefix="/api", tags=["filters"])
    app.include_router(book_metadata.router, prefix="/api/book-metadata", tags=["book_metadata"])
    app.include_router(slider.router, prefix="/api/slider", tags=["slider"])
    app.include_router(clip_generator.router, prefix="/api/clip_generator", tags=["clip_generator"])
    app.include_router(smart_validations.router, prefix="/api/validations", tags=["smart_validations"])

    app.include_router(boomstream_migration.router, prefix="/api/boomstream", tags=["boomstream"])

    app.include_router(helpers.router, prefix="/api/helpers", tags=["helpers"])

    app.include_router(health_checkers.router, prefix="/api/healthcheckers", tags=["Health Checkers"])
    app.include_router(search.router, prefix="/api/search", tags=["search"])
    app.include_router(ad_control.router, prefix="/api/ad_control", tags=["Ad-Control"])
    app.include_router(video_repair.router, prefix="/api/video_help", tags=["Video help"])
    app.include_router(book_ad_control.router, prefix="/api/book_ad_control", tags=["Book Ad Analytics"])
    app.include_router(policy.router, prefix="/api/policy", tags=["Policy"])
    app.include_router(creatives.router, tags=["creatives"])
    app.include_router(book_assets.router, prefix="/api/books", tags=["book_assets"])
    app.include_router(summary_generator.router, prefix="/api/summary_generator", tags=["summary generator"])
    app.include_router(course_request.router,prefix="/api/request", tags=["requests"])


    @app.on_event("startup")
    def on_startup():
        init_db()

    return app



app = create_app()
