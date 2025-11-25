import telegram
from ..core.config import settings
import logging

logger = logging.getLogger(__name__)


async def send_telegram_message(text: str) -> bool:
    """Отправляет сообщение в Telegram группу"""
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        logger.warning("Telegram not configured, skipping Telegram notification")
        return False
    
    try:
        bot = telegram.Bot(settings.TELEGRAM_BOT_TOKEN)
        async with bot:
            await bot.send_message(
                chat_id=settings.TELEGRAM_CHAT_ID,
                text=text,
                parse_mode='HTML'
            )
        logger.info(f"Telegram message sent successfully to chat {settings.TELEGRAM_CHAT_ID}")
        return True
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {e}")
        return False

