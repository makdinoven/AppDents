from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from collections import defaultdict
from time import time
import asyncio
import logging
from ..utils.telegram_monitor import send_rate_limit_notification

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate Limiting Middleware с алгоритмом Sliding Window.
    Ограничивает количество запросов с одного IP до max_requests за window_seconds.
    """
    
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # Словарь: {ip: [timestamp1, timestamp2, ...]}
        self.request_times = defaultdict(list)
        # Для очистки старых записей
        self.last_cleanup = time()
        self.cleanup_interval = 300  # Очистка каждые 5 минут
        
    def _cleanup_old_entries(self):
        """Удаляет старые записи из памяти"""
        current_time = time()
        if current_time - self.last_cleanup > self.cleanup_interval:
            cutoff_time = current_time - self.window_seconds * 2
            
            # Удаляем IP, у которых все запросы старше cutoff_time
            ips_to_remove = []
            for ip, timestamps in self.request_times.items():
                # Удаляем старые timestamps
                timestamps[:] = [ts for ts in timestamps if ts > cutoff_time]
                if not timestamps:
                    ips_to_remove.append(ip)
            
            for ip in ips_to_remove:
                del self.request_times[ip]
            
            self.last_cleanup = current_time
            logger.debug(f"Rate limiter cleanup: removed {len(ips_to_remove)} IPs")
    
    def _get_client_ip(self, request: Request) -> str:
        """Получает IP клиента из заголовков или напрямую"""
        # Nginx передаёт реальный IP в X-Real-IP или X-Forwarded-For
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Если заголовков нет, берём из request.client
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _get_user_info(self, request: Request) -> tuple:
        """Извлекает информацию о пользователе из request.state если есть"""
        # FastAPI может сохранять информацию о пользователе в request.state
        # после аутентификации через dependencies
        user_email = getattr(request.state, "user_email", None)
        user_id = getattr(request.state, "user_id", None)
        return user_email, user_id
    
    async def dispatch(self, request: Request, call_next):
        """Обрабатывает каждый запрос"""
        # Периодическая очистка
        self._cleanup_old_entries()
        
        client_ip = self._get_client_ip(request)
        current_time = time()
        
        # Получаем timestamps для этого IP
        timestamps = self.request_times[client_ip]
        
        # Удаляем timestamps старше window_seconds (Sliding Window)
        cutoff_time = current_time - self.window_seconds
        timestamps[:] = [ts for ts in timestamps if ts > cutoff_time]
        
        # Проверяем лимит
        if len(timestamps) >= self.max_requests:
            # Лимит превышен
            # Вычисляем время до доступности (когда самый старый запрос выйдет из окна)
            oldest_timestamp = timestamps[0]
            time_until_available = self.window_seconds - (current_time - oldest_timestamp)
            
            # Получаем информацию о пользователе
            user_email, user_id = self._get_user_info(request)
            domain = request.headers.get("host", "unknown")
            
            # Отправляем уведомление в Telegram (неблокирующе)
            asyncio.create_task(send_rate_limit_notification(
                client_ip=client_ip,
                domain=domain,
                request_count=len(timestamps),
                max_requests=self.max_requests,
                user_email=user_email,
                user_id=user_id,
                time_until_available=time_until_available
            ))
            
            logger.warning(
                f"Rate limit exceeded for IP {client_ip}: "
                f"{len(timestamps)}/{self.max_requests} requests in {self.window_seconds}s"
            )
            
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Try again later.",
                    "retry_after": int(time_until_available)
                },
                headers={"Retry-After": str(int(time_until_available))}
            )
        
        # Добавляем текущий запрос
        timestamps.append(current_time)
        
        # Пропускаем запрос дальше
        response = await call_next(request)
        return response

