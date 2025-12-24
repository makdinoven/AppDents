from __future__ import annotations

import hashlib
import re
import unicodedata
from urllib.parse import unquote


_SAFE_CHARS_RE = re.compile(r"[^a-z0-9._-]+")
_DASH_RE = re.compile(r"-{2,}")


# Минимально достаточная транслитерация RU/UA/BG базовой кириллицы.
# Цель: стабильные key без '%', пробелов и нелатинских символов.
_CYR_MAP = {
    "а": "a",  "б": "b",  "в": "v",  "г": "g",  "д": "d",
    "е": "e",  "ё": "e",  "ж": "zh", "з": "z",  "и": "i",
    "й": "y",  "к": "k",  "л": "l",  "м": "m",  "н": "n",
    "о": "o",  "п": "p",  "р": "r",  "с": "s",  "т": "t",
    "у": "u",  "ф": "f",  "х": "h",  "ц": "ts", "ч": "ch",
    "ш": "sh", "щ": "sch", "ъ": "",  "ы": "y",  "ь": "",
    "э": "e",  "ю": "yu", "я": "ya",
    "і": "i",  "ї": "yi", "є": "ye", "ґ": "g",
}


def _sha1_short(s: str, n: int = 12) -> str:
    return hashlib.sha1(s.encode("utf-8", "ignore")).hexdigest()[:n]


def transliterate_to_ascii(s: str) -> str:
    """
    Превращает строку в максимально «ASCII-похожую»:
    - кириллица -> латиница по таблице;
    - диакритика убирается (NFKD);
    - остальное — как получится (может стать пусто).
    """
    if not s:
        return ""

    out = []
    for ch in s:
        low = ch.lower()
        if low in _CYR_MAP:
            out.append(_CYR_MAP[low])
        else:
            out.append(ch)
    s2 = "".join(out)

    # Убираем диакритику, оставляем только совместимые символы
    s3 = unicodedata.normalize("NFKD", s2)
    s3 = "".join(c for c in s3 if not unicodedata.combining(c))
    return s3


def slugify_segment(seg: str) -> str:
    """
    Делает сегмент пути безопасным для S3 key:
    - unquote уже должен быть сделан снаружи;
    - пробелы и разделители -> '-';
    - кириллица -> латиница;
    - оставляем [a-z0-9._-].
    """
    if not seg:
        return ""

    # Нормализация пробелов/подчёркиваний
    s = seg.strip().replace(" ", "-").replace("\t", "-").replace("_", "-")
    s = transliterate_to_ascii(s)
    s = s.lower()

    # Убираем «плохие» символы
    s = _SAFE_CHARS_RE.sub("-", s)
    s = _DASH_RE.sub("-", s).strip("-")
    return s


def canonicalize_s3_key(key: str) -> str:
    """
    Приводим key к каноническому виду по всему пути:
    - снимаем URL encoding (%20 и т.п.)
    - нормализуем каждый сегмент
    - сохраняем расширение, если оно было (например .mp4)
    - пустые сегменты заменяем на sha1-хэш
    """
    raw = unquote((key or "").lstrip("/"))
    if not raw:
        return raw

    parts = [p for p in raw.split("/") if p not in ("", ".", "..")]
    if not parts:
        return _sha1_short(raw)

    norm_parts: list[str] = []
    for i, p in enumerate(parts):
        # Последний сегмент: сохраняем расширение если есть
        if i == len(parts) - 1 and "." in p and not p.startswith("."):
            base, ext = p.rsplit(".", 1)
            base_s = slugify_segment(base)
            ext_s = slugify_segment(ext)
            if not base_s:
                base_s = _sha1_short(p)
            if not ext_s:
                ext_s = ext.lower()  # fallback
            norm_parts.append(f"{base_s}.{ext_s}")
            continue

        seg_s = slugify_segment(p)
        if not seg_s:
            seg_s = _sha1_short(p)
        norm_parts.append(seg_s)

    return "/".join(norm_parts)


