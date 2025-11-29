import telegram
from ..core.config import settings
import logging
from datetime import datetime
from html import escape

logger = logging.getLogger(__name__)


async def send_error_notification(
    method: str,
    url: str,
    status_code: int,
    error_type: str,
    traceback_text: str,
    domain: str,
    client_ip: str
) -> bool:
    """Отправляет уведомление об ошибке в Telegram с первыми 5 и последними 5 строками трейса"""
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_MONITORING_CHAT_ID:
        logger.warning("Telegram monitoring not configured, skipping error notification")
        return False
    
    try:
        # Разбиваем трейсбек на строки
        traceback_lines = traceback_text.strip().split('\n')
        
        # Берём первые 5 и последние 5 строк
        first_lines = '\n'.join(traceback_lines[:5]) if len(traceback_lines) > 5 else traceback_text
        last_lines = '\n'.join(traceback_lines[-5:]) if len(traceback_lines) > 10 else ''
        
        # Форматируем сообщение
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        message = f"""🚨 <b>{status_code} Internal Server Error</b>

🌐 <b>Сайт:</b> {escape(domain)}
📍 <b>{method}</b> {escape(url)}
🔴 <b>Ошибка:</b> {escape(error_type)}
📍 <b>IP:</b> {escape(client_ip)}

📝 <b>Traceback (первые 5 строк):</b>
<pre>{escape(first_lines)}</pre>"""

        if last_lines and len(traceback_lines) > 10:
            message += f"""

📝 <b>Traceback (последние 5 строк):</b>
<pre>{escape(last_lines)}</pre>"""
        
        message += f"""

⏰ {timestamp}"""
        
        bot = telegram.Bot(settings.TELEGRAM_BOT_TOKEN)
        async with bot:
            await bot.send_message(
                chat_id=settings.TELEGRAM_MONITORING_CHAT_ID,
                text=message,
                parse_mode='HTML'
            )
        
        logger.info(f"Error notification sent to Telegram for {method} {url}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send error notification to Telegram: {e}")
        return False


async def send_slow_request_notification(
    method: str,
    url: str,
    duration: float,
    domain: str,
    client_ip: str
) -> bool:
    """Отправляет уведомление о медленном запросе в Telegram"""
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_MONITORING_CHAT_ID:
        logger.warning("Telegram monitoring not configured, skipping slow request notification")
        return False
    
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        message = f"""⚠️ <b>Slow Request</b>

🌐 <b>Сайт:</b> {escape(domain)}
📍 <b>{method}</b> {escape(url)}
⏱️ <b>Время:</b> {duration:.1f}s
📍 <b>IP:</b> {escape(client_ip)}

⏰ {timestamp}"""
        
        bot = telegram.Bot(settings.TELEGRAM_BOT_TOKEN)
        async with bot:
            await bot.send_message(
                chat_id=settings.TELEGRAM_MONITORING_CHAT_ID,
                text=message,
                parse_mode='HTML'
            )
        
        logger.info(f"Slow request notification sent to Telegram for {method} {url} ({duration:.1f}s)")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send slow request notification to Telegram: {e}")
        return False


async def send_rate_limit_notification(
    client_ip: str,
    domain: str,
    request_count: int,
    max_requests: int,
    user_email: str = None,
    user_id: int = None,
    time_until_available: float = 0,
    last_requests: list = None
) -> bool:
    """Отправляет уведомление о превышении rate limit в Telegram с последними 10 запросами"""
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_MONITORING_CHAT_ID:
        logger.warning("Telegram monitoring not configured, skipping rate limit notification")
        return False
    
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Форматируем информацию о пользователе
        if user_email and user_id:
            user_info = f"{escape(user_email)} (ID: {user_id})"
        elif user_id:
            user_info = f"User ID: {user_id}"
        else:
            user_info = "Не авторизован"
        
        message = f"""🛑 <b>Rate Limit Exceeded</b>

📍 <b>IP:</b> {escape(client_ip)}
🌐 <b>Домен:</b> {escape(domain)}
👤 <b>Пользователь:</b> {user_info}
📊 <b>Запросы:</b> {request_count}/{max_requests} за последние 60 сек
⏱️ <b>Блокировка:</b> ~{int(time_until_available)} сек (динамическая)"""

        # Добавляем информацию о последних 10 запросах
        if last_requests:
            message += "\n\n📋 <b>Последние 10 запросов:</b>\n"
            for i, req in enumerate(last_requests, 1):
                # seconds_ago уже вычислено в момент превышения лимита
                seconds_ago = req.get('seconds_ago', 0)
                message += f"{i}. <code>{escape(req['method'])} {escape(req['url'])}</code> ({seconds_ago}s назад)\n"
        
        message += f"\n⏰ {timestamp}"
        
        bot = telegram.Bot(settings.TELEGRAM_BOT_TOKEN)
        async with bot:
            await bot.send_message(
                chat_id=settings.TELEGRAM_MONITORING_CHAT_ID,
                text=message,
                parse_mode='HTML'
            )
        
        logger.info(f"Rate limit notification sent to Telegram for IP {client_ip}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send rate limit notification to Telegram: {e}")
        return False

