# app/core/analytics.py
import requests
from app.core.config import settings  # если используете конфиг

def send_search_to_analytics(
    query: str,
    path: str | None,
    created_at,
) -> None:
    """
    Отправка поискового запроса во внешнюю аналитику.
    Сейчас пример через HTTP POST, но можно заменить на что угодно.
    """
    # Если пока аналитику не подключили — можно вообще оставить pass
    if not getattr(settings, "ANALYTICS_ENDPOINT", None):
        return

    requests.post(
        settings.ANALYTICS_ENDPOINT,
        json={
            "event": "search_query",
            "query": query,
            "path": path,
            "created_at": created_at.isoformat(),
        },
        timeout=2,
    )
