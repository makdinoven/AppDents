"""
Утилиты для работы с IP-адресами.
"""
import ipaddress
import logging
from fastapi import Request

logger = logging.getLogger(__name__)


def get_client_ip(request: Request) -> str:
    """
    Корректно извлекает IP клиента, учитывая возможный прокси перед сервисом.
    """
    xfwd = request.headers.get("X-Forwarded-For", "").strip()
    if xfwd:
        return xfwd.split(",")[0].strip()
    return request.client.host if request.client else "0.0.0.0"

# Диапазоны IP-адресов ботов Facebook/Meta
# https://developers.facebook.com/docs/sharing/webmasters/crawler/
FACEBOOK_BOT_PREFIXES_V6 = [
    "2a03:2880::",  # Основной диапазон Meta (2a03:2880::/32)
]

FACEBOOK_BOT_PREFIXES_V4 = [
    "66.220.144.",
    "66.220.145.",
    "66.220.146.",
    "66.220.147.",
    "66.220.148.",
    "66.220.149.",
    "66.220.150.",
    "66.220.151.",
    "66.220.152.",
    "66.220.153.",
    "66.220.154.",
    "66.220.155.",
    "66.220.156.",
    "66.220.157.",
    "66.220.158.",
    "66.220.159.",
    "69.63.176.",
    "69.63.177.",
    "69.63.178.",
    "69.63.179.",
    "69.63.180.",
    "69.63.181.",
    "69.63.182.",
    "69.63.183.",
    "69.63.184.",
    "69.63.185.",
    "69.63.186.",
    "69.63.187.",
    "69.63.188.",
    "69.63.189.",
    "69.63.190.",
    "69.63.191.",
    "69.171.224.",
    "69.171.225.",
    "69.171.226.",
    "69.171.227.",
    "69.171.228.",
    "69.171.229.",
    "69.171.230.",
    "69.171.231.",
    "69.171.232.",
    "69.171.233.",
    "69.171.234.",
    "69.171.235.",
    "69.171.236.",
    "69.171.237.",
    "69.171.238.",
    "69.171.239.",
    "69.171.240.",
    "69.171.241.",
    "69.171.242.",
    "69.171.243.",
    "69.171.244.",
    "69.171.245.",
    "69.171.246.",
    "69.171.247.",
    "69.171.248.",
    "69.171.249.",
    "69.171.250.",
    "69.171.251.",
    "69.171.252.",
    "69.171.253.",
    "69.171.254.",
    "69.171.255.",
    "173.252.64.",
    "173.252.65.",
    "173.252.66.",
    "173.252.67.",
    "173.252.68.",
    "173.252.69.",
    "173.252.70.",
    "173.252.71.",
    "173.252.72.",
    "173.252.73.",
    "173.252.74.",
    "173.252.75.",
    "173.252.76.",
    "173.252.77.",
    "173.252.78.",
    "173.252.79.",
    "173.252.80.",
    "173.252.81.",
    "173.252.82.",
    "173.252.83.",
    "173.252.84.",
    "173.252.85.",
    "173.252.86.",
    "173.252.87.",
    "173.252.88.",
    "173.252.89.",
    "173.252.90.",
    "173.252.91.",
    "173.252.92.",
    "173.252.93.",
    "173.252.94.",
    "173.252.95.",
    "31.13.24.",
    "31.13.25.",
    "31.13.26.",
    "31.13.27.",
    "31.13.64.",
    "31.13.65.",
    "31.13.66.",
    "31.13.67.",
    "31.13.68.",
    "31.13.69.",
    "31.13.70.",
    "31.13.71.",
    "31.13.72.",
    "31.13.73.",
    "31.13.74.",
    "31.13.75.",
    "31.13.76.",
    "31.13.77.",
    "31.13.78.",
    "31.13.79.",
    "31.13.80.",
    "31.13.81.",
    "31.13.82.",
    "31.13.83.",
    "31.13.84.",
    "31.13.85.",
    "31.13.86.",
    "31.13.87.",
    "31.13.88.",
    "31.13.89.",
    "31.13.90.",
    "31.13.91.",
    "31.13.92.",
    "31.13.93.",
    "31.13.94.",
    "31.13.95.",
]

# Сети Meta в формате CIDR для точной проверки IPv6
META_IPV6_NETWORKS = [
    ipaddress.ip_network("2a03:2880::/32"),
]


def is_facebook_bot_ip(ip: str | None) -> bool:
    """
    Проверяет, принадлежит ли IP-адрес ботам Facebook/Meta.
    
    Args:
        ip: IP-адрес (IPv4 или IPv6)
        
    Returns:
        True если IP принадлежит Facebook/Meta ботам
    """
    if not ip:
        return False
    
    ip = ip.strip()
    
    try:
        addr = ipaddress.ip_address(ip)
        
        # Проверка IPv6
        if addr.version == 6:
            for network in META_IPV6_NETWORKS:
                if addr in network:
                    logger.debug("Facebook bot IPv6 detected: %s", ip)
                    return True
            return False
        
        # Проверка IPv4 по префиксам
        for prefix in FACEBOOK_BOT_PREFIXES_V4:
            if ip.startswith(prefix):
                logger.debug("Facebook bot IPv4 detected: %s", ip)
                return True
        
        return False
        
    except ValueError:
        # Невалидный IP
        logger.warning("Invalid IP address: %s", ip)
        return False


# ───────────────────────────────────────────────────────────────
# Фильтрация по User-Agent
# ───────────────────────────────────────────────────────────────

# Известные User-Agent строки ботов (проверяем через "in", регистронезависимо)
BOT_USER_AGENTS = [
    # Рекламные платформы
    "facebookexternalhit",      # Facebook link preview
    "facebot",                  # Facebook crawler
    "meta-externalagent",       # Meta
    "adsbot-google",            # Google Ads
    "mediapartners-google",     # Google AdSense
    "google-adwords",           # Google Ads
    "tiktok",                   # TikTok
    
    # Социальные сети (генерируют превью ссылок)
    "twitterbot",               # Twitter/X
    "linkedinbot",              # LinkedIn
    "telegrambot",              # Telegram
    "whatsapp",                 # WhatsApp
    "slackbot",                 # Slack
    "slack-imgproxy",           # Slack image proxy
    "discordbot",               # Discord
    "vkshare",                  # VK
    "pinterestbot",             # Pinterest
    "redditbot",                # Reddit
    "embedly",                  # Embedly (используется многими платформами)
    
    # Поисковые боты
    "googlebot",                # Google
    "google-inspectiontool",    # Google Search Console
    "bingbot",                  # Bing
    "yandexbot",                # Yandex
    "yandexmobilebot",          # Yandex Mobile
    "baiduspider",              # Baidu
    "duckduckbot",              # DuckDuckGo
    "sogou",                    # Sogou
    "exabot",                   # Exalead
    "ia_archiver",              # Alexa
    
    # SEO инструменты
    "ahrefsbot",                # Ahrefs
    "semrushbot",               # SEMrush
    "mj12bot",                  # Majestic
    "dotbot",                   # Moz
    "rogerbot",                 # Moz
    "screaming frog",           # Screaming Frog
    "seokicks",                 # SEOkicks
    "sistrix",                  # SISTRIX
    
    # Мониторинг и аптайм
    "pingdom",                  # Pingdom
    "uptimerobot",              # UptimeRobot
    "statuscake",               # StatusCake
    "site24x7",                 # Site24x7
    "checkmarknetwork",         # Checkmark
    "monitor.us",               # Monitor.us
    
    # Другие известные боты
    "petalbot",                 # Huawei/Petal
    "applebot",                 # Apple
    "bytespider",               # ByteDance
    "gptbot",                   # OpenAI GPT
    "chatgpt-user",             # ChatGPT
    "claudebot",                # Anthropic Claude
    "ccbot",                    # Common Crawl
    "archive.org_bot",          # Internet Archive
    "dataprovider",             # Data providers
    "headlesschrome",           # Headless Chrome (часто боты)
    "phantomjs",                # PhantomJS
    "python-requests",          # Python scripts
    "python-urllib",            # Python scripts
    "curl",                     # curl
    "wget",                     # wget
    "httpie",                   # HTTPie
    "postman",                  # Postman
]


def is_bot_user_agent(user_agent: str | None) -> bool:
    """
    Проверяет, является ли User-Agent ботом.
    
    Args:
        user_agent: Строка User-Agent из заголовка запроса
        
    Returns:
        True если User-Agent принадлежит известному боту
    """
    if not user_agent:
        return False
    
    ua_lower = user_agent.lower()
    
    for bot_ua in BOT_USER_AGENTS:
        if bot_ua in ua_lower:
            logger.debug("Bot User-Agent detected: %s (matched: %s)", user_agent[:100], bot_ua)
            return True
    
    return False


def is_bot_request(request: Request) -> bool:
    """
    Комплексная проверка: является ли запрос от бота.
    Проверяет и IP-адрес, и User-Agent.
    
    Args:
        request: FastAPI Request объект
        
    Returns:
        True если запрос от бота (по IP или User-Agent)
    """
    # Проверка по User-Agent (быстрее, проверяем первым)
    user_agent = request.headers.get("User-Agent", "")
    if is_bot_user_agent(user_agent):
        return True
    
    # Проверка по IP (для Facebook/Meta ботов которые могут менять UA)
    client_ip = get_client_ip(request)
    if is_facebook_bot_ip(client_ip):
        return True
    
    return False
