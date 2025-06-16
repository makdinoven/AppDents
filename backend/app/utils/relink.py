import re
from urllib.parse import urlparse, urlunparse

_UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)

def convert_storage_url(url: str) -> str:
    """Меняет хост *selstorage* или *s3.twcstorage* на cdn.dent-s.com
    и, если надо, выбрасывает первый сегмент-UUID."""
    if not url:
        return url

    p = urlparse(url)
    host, path = p.netloc, p.path.lstrip("/")

    if host.endswith(".selstorage.ru"):
        # Просто меняем хост, путь оставляем полностью
        new_path = path

    elif host == "s3.twcstorage.ru":
        # Если первый сегмент похож на UUID — убираем его
        head, *tail = path.split("/", 1)
        new_path = tail[0] if _UUID.fullmatch(head) and tail else path

    else:                       # остальные домены не трогаем
        return url

    # Собираем новый url
    new_parts = p._replace(netloc="cdn.dent-s.com", path="/" + new_path)
    return urlunparse(new_parts)