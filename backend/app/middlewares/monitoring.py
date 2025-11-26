from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import time
import asyncio
import traceback
import logging
from ..utils.telegram_monitor import send_error_notification, send_slow_request_notification

logger = logging.getLogger(__name__)


class MonitoringMiddleware(BaseHTTPMiddleware):
    """
    Middleware для мониторинга производительности и ошибок.
    - Отправляет уведомления о 500 ошибках в Telegram
    - Отправляет уведомления о медленных запросах (>5 секунд)
    - Не изменяет существующие логи
    """
    
    # Эндпоинты, исключённые из мониторинга производительности
    PERFORMANCE_EXCLUDE_PATTERNS = [
        "/api/courses/detail/",
    ]
    
    # Порог для медленных запросов (в секундах)
    SLOW_REQUEST_THRESHOLD = 5.0
    
    def __init__(self, app):
        super().__init__(app)
    
    def _get_client_ip(self, request: Request) -> str:
        """Получает IP клиента из заголовков или напрямую"""
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _should_exclude_performance_monitoring(self, url: str) -> bool:
        """Проверяет, нужно ли исключать URL из мониторинга производительности"""
        for pattern in self.PERFORMANCE_EXCLUDE_PATTERNS:
            if pattern in url:
                return True
        return False
    
    async def dispatch(self, request: Request, call_next):
        """Обрабатывает каждый запрос"""
        start_time = time.time()
        response = None
        error_occurred = False
        error_info = None
        
        try:
            # Выполняем запрос
            response = await call_next(request)
            
            # Проверяем статус код ответа
            if response.status_code >= 500:
                error_occurred = True
                error_info = {
                    "type": f"{response.status_code} Error",
                    "traceback": f"HTTP {response.status_code} response from endpoint"
                }
            
        except Exception as e:
            # Необработанное исключение
            error_occurred = True
            error_info = {
                "type": type(e).__name__,
                "traceback": traceback.format_exc()
            }
            # Пробрасываем исключение дальше, чтобы FastAPI обработал его
            raise
        
        finally:
            # Вычисляем время выполнения
            duration = time.time() - start_time
            
            # Получаем информацию о запросе
            method = request.method
            url = str(request.url.path)
            domain = request.headers.get("host", "unknown")
            client_ip = self._get_client_ip(request)
            
            # Отправляем уведомление об ошибке
            if error_occurred and error_info:
                status_code = response.status_code if response else 500
                asyncio.create_task(send_error_notification(
                    method=method,
                    url=url,
                    status_code=status_code,
                    error_type=error_info["type"],
                    traceback_text=error_info["traceback"],
                    domain=domain,
                    client_ip=client_ip
                ))
            
            # Проверяем медленные запросы (только если не исключён из мониторинга)
            if (duration > self.SLOW_REQUEST_THRESHOLD and 
                not self._should_exclude_performance_monitoring(url)):
                asyncio.create_task(send_slow_request_notification(
                    method=method,
                    url=url,
                    duration=duration,
                    domain=domain,
                    client_ip=client_ip
                ))
        
        return response

