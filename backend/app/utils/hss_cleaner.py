import re
from html import escape

URL_RE = re.compile(r"(?P<url>(https?://[^\s<]+|www\.[^\s<]+))", re.IGNORECASE)


def _make_safe_anchor(url: str) -> str:
    href = url if url.lower().startswith(("http://", "https://")) else "http://" + url
    href = href.strip()
    safe_href = escape(href, quote=True)
    disp = url if len(url) < 120 else url[:80] + "…" + url[-30:]
    disp = escape(disp)
    return f'<a href="{safe_href}" target="_blank" rel="noopener noreferrer">{disp}</a>'


def sanitize_and_linkify(raw_text: str, max_length: int = 3000) -> str:
    """Удаляет XSS и делает ссылки кликабельными (http, https, www)."""
    if not isinstance(raw_text, str):
        raw_text = str(raw_text or "")
    text = raw_text.strip()
    if len(text) > max_length:
        text = text[:max_length] + "..."

    parts = []
    last = 0
    for m in URL_RE.finditer(text):
        s, e = m.span()
        parts.append(escape(text[last:s]))
        parts.append(_make_safe_anchor(m.group("url")))
        last = e
    parts.append(escape(text[last:]))
    html_fragment = "<p>" + "</p><p>".join("".join(parts).splitlines()) + "</p>"
    return html_fragment
