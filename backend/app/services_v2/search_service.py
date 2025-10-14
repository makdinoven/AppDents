from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import or_
import math

from ..models.models_v2 import Author, Landing, BookLanding, Book

# === Настройки скоринга ===
TITLE_WEIGHT = 1.0   # видимое название
SLUG_WEIGHT  = 0.35  # slug/page_name имеет пониженный вес

# === Утилиты ===
def _ilike(s: str) -> str:
    return f"%{s.strip()}%"

def _norm(s: Optional[str]) -> str:
    return (s or "").strip().lower()

def clip(text: str | None, limit: int = 100, keep_words: bool = True, ellipsis: str = "…") -> str:
    if not text:
        return ""
    text = text.strip()
    if len(text) <= limit:
        return text
    if keep_words:
        cut = text.rfind(" ", 0, limit)
        if cut == -1:
            cut = limit - len(ellipsis)
        return text[:cut].rstrip() + ellipsis
    # жёсткая обрезка посимвольно
    return text[: limit - len(ellipsis)] + ellipsis

def _first_book(bl):
    """Вернёт первую связанную книгу у BookLanding, либо None."""
    try:
        bs = getattr(bl, "books", None) or []
        return bs[0] if bs else None
    except Exception:
        return None

def safe_price(v) -> float:
    """Парсинг цены в float; нечисловые значения -> +inf."""
    try:
        if v is None:
            return float("inf")
        if isinstance(v, (int, float)):
            return float(v)
        s = str(v).strip().replace(",", ".")
        return float(s)
    except Exception:
        return float("inf")

def _text_score(field: Optional[str], q: str, tokens: List[str]) -> int:
    """Скоринг текста: exact > startswith > contains + бонусы за токены."""
    if not field:
        return 0
    f = _norm(field)
    base = 0
    if f == q:
        base += 100
    elif f.startswith(q):
        base += 60
    elif q in f:
        base += 30
    for t in tokens:
        if t and t in f:
            base += 8
    return base

def _authors_score(authors: List["Author"], q: str, tokens: List[str], scale: float = 1.0) -> int:
    sc = 0
    for a in authors or []:
        sc += int(_text_score(a.name, q, tokens) * scale)
    return sc

def _author_content_counts_like_detail(a: Author, langs: Optional[List[str]]) -> tuple[int, int]:
    """
    Подсчёт (courses_count, books_count) по логике из get_author_full_detail:
    - landings: убираем скрытые, применяем фильтр языков;
      считаем min цену по каждому course_id, оставляем лендинги,
      у которых цена не хуже min для всех их курсов; собираем уникальные course_id.
    - books: считаем книги, у которых есть хотя бы один видимый book_landing
      нужного языка с конечной (числовой) ценой.
    """
    # --- 1) ЛЕНДИНГИ АВТОРА (курсы) ---
    visible_landings: List[Landing] = []
    for l in (a.landings or []):
        if l.is_hidden:
            continue
        if langs and (l.language or "").upper() not in langs:
            continue
        visible_landings.append(l)

    # min цена по каждому course_id
    min_price_by_course: Dict[int, float] = {}
    for l in visible_landings:
        price = safe_price(l.new_price)
        for c in (l.courses or []):
            cid = c.id
            prev = min_price_by_course.get(cid, float("inf"))
            if price < prev:
                min_price_by_course[cid] = price

    # оставляем лендинги, цена которых не выше min для любого их курса
    kept_landings: List[Landing] = []
    for l in visible_landings:
        price = safe_price(l.new_price)
        # если у лендинга есть хоть один курс с более дешёвым лендингом — выкидываем
        if any(price > min_price_by_course.get(c.id, float("inf")) for c in (l.courses or [])):
            continue
        kept_landings.append(l)

    # уникальные course_id из оставшихся лендингов
    course_ids = set()
    for l in kept_landings:
        for c in (l.courses or []):
            if getattr(c, "id", None) is not None:
                course_ids.add(c.id)
    courses_count = len(course_ids)

    # --- 2) КНИГИ АВТОРА ---
    books_count = 0
    for b in (getattr(a, "books", []) or []):
        # видимые книжные лендинги нужного языка
        visible_bl = []
        for bl in (b.landings or []):
            if bl.is_hidden:
                continue
            if langs and (bl.language or "").upper() not in langs:
                continue
            visible_bl.append(bl)

        if not visible_bl:
            continue

        # минимальная цена по книге среди видимых лендингов
        price_min = min(safe_price(bl.new_price) for bl in visible_bl)
        if price_min == float("inf"):
            # у книги нет валидной цены ни на одном видимом лендинге — не считаем такую книгу
            continue

        books_count += 1

    return courses_count, books_count

# === Основная функция ===
def search_everything(
    db: Session,
    *,
    q: str,
    types: Optional[List[str]] = None,        # ["authors", "landings", "book_landings"]
    languages: Optional[List[str]] = None,    # ["EN","RU","ES","PT","AR","IT"]
) -> Dict[str, Any]:
    """
    Глобальный поиск с «умом»:
    - Ищет авторов/курсы(лендинги)/книжные лендинги.
    - Если найден автор, добавляет его курсы и книжные лендинги.
    - Фильтр языков влияет на счётчики и выдачу.
    - Фильтр типов влияет ТОЛЬКО на выдачу (счётчики — без учёта типов).
    - Без лимита: возвращаем все результаты (в трёх массивах).
    - Снижен вес совпадения по slug (page_name).
    """
    q_like = _ilike(q)
    qn = _norm(q)
    tokens = [t for t in qn.split() if t]

    langs: Optional[List[str]] = None
    if languages:
        langs = [x.strip().upper() for x in languages if x and x.strip()]

    # --- 1) Поиск базовых совпадений ---
    # Авторы — с предзагрузкой нужных связей, чтобы корректно посчитать courses_count/books_count
    authors_q = (
        db.query(Author)
          .options(
              selectinload(Author.landings).selectinload(Landing.courses),
              selectinload(Author.books).selectinload(Book.landings),
          )
          .filter(Author.name.ilike(q_like))
    )
    if langs:
        authors_q = authors_q.filter(Author.language.in_(langs))
    authors = authors_q.all()

    landings_q = (
        db.query(Landing)
          .outerjoin(Landing.authors)
          .filter(Landing.is_hidden.is_(False))
          .filter(
              or_(
                  Landing.landing_name.ilike(q_like),
                  Landing.page_name.ilike(q_like),   # slug в фильтре остаётся; вес режем в скоринге
                  Author.name.ilike(q_like),
              )
          )
          .distinct()
    )
    if langs:
        landings_q = landings_q.filter(Landing.language.in_(langs))
    landings = landings_q.all()

    book_landings_q = (
        db.query(BookLanding)
        .join(BookLanding.books)  # <-- books (многие-к-многим / один-ко-многим)
        .outerjoin(Book.authors)
        .filter(BookLanding.is_hidden.is_(False))
        .filter(
            or_(
                BookLanding.landing_name.ilike(q_like),
                BookLanding.page_name.ilike(q_like),
                Book.title.ilike(q_like),  # по названию книги
                Author.name.ilike(q_like),  # по авторам книги
            )
        )
        .distinct()
    )
    if langs:
        book_landings_q = book_landings_q.filter(BookLanding.language.in_(langs))
    book_landings = book_landings_q.all()

    # --- 2) «Ум»: если нашли авторов — доклеиваем их контент ---
    if authors:
        author_ids = [a.id for a in authors]

        extra_landings_q = (
            db.query(Landing)
              .join(Landing.authors)
              .filter(Landing.is_hidden.is_(False), Author.id.in_(author_ids))
              .distinct()
        )
        if langs:
            extra_landings_q = extra_landings_q.filter(Landing.language.in_(langs))
        extra_landings = extra_landings_q.all()

        extra_book_landings_q = (
            db.query(BookLanding)
            .join(BookLanding.books)
            .join(Book.authors)
            .filter(BookLanding.is_hidden.is_(False), Author.id.in_(author_ids))
            .distinct()
        )
        if langs:
            extra_book_landings_q = extra_book_landings_q.filter(BookLanding.language.in_(langs))
        extra_book_landings = extra_book_landings_q.all()

        # дедупликация по id
        l_ids = {l.id for l in landings}
        for l in extra_landings:
            if l.id not in l_ids:
                landings.append(l)
        bl_ids = {bl.id for bl in book_landings}
        for bl in extra_book_landings:
            if bl.id not in bl_ids:
                book_landings.append(bl)

    # --- 3) Нормализуем, считаем счётчики (без учёта фильтра типов) и скорим ---
    scored_items: List[Dict[str, Any]] = []

    # Авторы — добавляем courses_count / books_count по «детальной» логике
    for a in authors:
        score = _text_score(a.name, qn, tokens)
        courses_count, books_count = _author_content_counts_like_detail(a, langs)

        scored_items.append({
            "type": "author",
            "id": a.id,
            "name": a.name,
            "photo": a.photo,
            "language": a.language,
            "description": clip(a.description, 100),
            "courses_count": courses_count,
            "books_count": books_count,
            "_score": score,
            "_tie": (0, a.id),
        })

    # Курсы (лендинги) — пониженный вес slug
    for l in landings:
        title_s = _text_score(l.landing_name, qn, tokens)
        slug_s  = _text_score(l.page_name, qn, tokens)
        score   = int(TITLE_WEIGHT * title_s + SLUG_WEIGHT * slug_s)
        score  += _authors_score(list(l.authors or []), qn, tokens, scale=0.8)
        try:
            score += int(math.log10(max(int(getattr(l, "sales_count", 0) or 0), 1)))
        except Exception:
            pass
        scored_items.append({
            "type": "landing",
            "id": l.id,
            "landing_name": l.landing_name,
            "page_name": l.page_name,
            "preview_photo": l.preview_photo,
            "old_price": l.old_price,
            "new_price": l.new_price,
            "language": l.language,
            "authors": [{"id": au.id, "name": au.name, "photo": au.photo, "language": au.language} for au in (l.authors or [])],
            "_score": score,
            "_tie": (1, l.id),
        })

    # Книжные лендинги — пониженный вес slug, приоритет видимых названий
    for bl in book_landings:
        b = _first_book(bl)

        title_s = _text_score(bl.landing_name, qn, tokens)
        book_title_s = _text_score(b.title if b else None, qn, tokens)
        slug_s = _text_score(bl.page_name, qn, tokens)
        score = max(title_s, book_title_s) + int(SLUG_WEIGHT * slug_s)

        book_authors = list((b.authors if b else []) or [])
        scored_items.append({
            "type": "book_landing",
            "id": bl.id,
            "landing_name": bl.landing_name,
            "page_name": bl.page_name,
            "preview_photo": b.cover_url,
            "old_price": bl.old_price,
            "new_price": bl.new_price,
            "language": bl.language,
            "book_title": b.title if b else None,
            "cover_url": b.cover_url if b else None,
            "authors": [{"id": au.id, "name": au.name, "photo": au.photo, "language": au.language} for au in
                        book_authors],
            "_score": score,
            "_tie": (2, bl.id),
        })

    # Счётчики (зависят только от q и languages)
    counts_all = {
        "authors":      sum(1 for it in scored_items if it["type"] == "author"),
        "landings":     sum(1 for it in scored_items if it["type"] == "landing"),
        "book_landings":sum(1 for it in scored_items if it["type"] == "book_landing"),
    }
    total_all = sum(counts_all.values())

    # --- 4) Фильтр по типам влияет только на выдачу, не на counts ---
    filtered_items = scored_items
    if types:
        tset = {t.lower() for t in types}
        type_map = {"authors": "author", "landings": "landing", "book_landings": "book_landing"}
        tset = {type_map.get(t, t) for t in tset}
        filtered_items = [it for it in scored_items if it["type"] in tset]

    # --- 5) Сортировка и раскладка по массивам, БЕЗ ЛИМИТА ---
    filtered_items.sort(key=lambda it: (-it["_score"], it["_tie"]))

    authors_out: List[Dict[str, Any]] = []
    landings_out: List[Dict[str, Any]] = []
    book_landings_out: List[Dict[str, Any]] = []

    def _strip_private(it: Dict[str, Any]) -> Dict[str, Any]:
        return {k: v for k, v in it.items() if not k.startswith("_")}

    for it in filtered_items:
        if it["type"] == "author":
            authors_out.append(_strip_private(it))
        elif it["type"] == "landing":
            landings_out.append(_strip_private(it))
        else:
            book_landings_out.append(_strip_private(it))

    returned = len(filtered_items)   # отдаём всё
    return {
        "counts": counts_all,        # только язык (и q), НЕ зависят от types
        "total": total_all,
        "returned": returned,
        "limit": returned,           # для совместимости со схемой
        "truncated": False,
        "authors": authors_out,
        "landings": landings_out,
        "book_landings": book_landings_out,
    }
