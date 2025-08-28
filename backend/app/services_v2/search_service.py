from typing import Iterable, List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_
import math

from ..models.models_v2 import Author, Landing, BookLanding, Book  # поля языка и связи существуют
# Author.language, Landing.language, BookLanding.language; Landing.authors; BookLanding.book; Book.authors

# ------------------------ утилиты ------------------------
TITLE_WEIGHT = 1.0
SLUG_WEIGHT  = 0.35

def _ilike(s: str) -> str:
    return f"%{s.strip()}%"

def _norm(s: Optional[str]) -> str:
    return (s or "").strip().lower()

def _text_score(field: Optional[str], q: str, tokens: List[str]) -> int:
    """Сильный скоринг текста: exact > startswith > contains + бонусы за токены."""
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
    # токены (минимальные «подсказки»)
    for t in tokens:
        if t and t in f:
            base += 8
    return base

def _authors_score(authors: List["Author"], q: str, tokens: List[str], scale: float = 1.0) -> int:
    sc = 0
    for a in authors or []:
        sc += int(_text_score(a.name, q, tokens) * scale)
    return sc

# ------------------------ основной поиск ------------------------

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
    - Фильтр языков влияет и на счётчики, и на выдачу.
    - Фильтр типов влияет ТОЛЬКО на выдачу (счётчики — без учёта типов).
    - Без лимита: возвращаются все результаты (в трёх массивах).
    """
    q_like = _ilike(q)
    qn = _norm(q)
    tokens = [t for t in qn.split() if t]

    langs: Optional[List[str]] = None
    if languages:
        langs = [x.strip().upper() for x in languages if x and x.strip()]

    # --- 1) Поиск базовых совпадений ---
    authors_q = db.query(Author).filter(Author.name.ilike(q_like))
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
                  Landing.page_name.ilike(q_like),   # slug с пониженным весом в скоринге (а не в фильтре)
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
          .join(BookLanding.book)
          .outerjoin(Book.authors)
          .filter(BookLanding.is_hidden.is_(False))
          .filter(
              or_(
                  BookLanding.landing_name.ilike(q_like),
                  BookLanding.page_name.ilike(q_like),  # slug с пониженным весом в скоринге
                  Book.title.ilike(q_like),
                  Author.name.ilike(q_like),
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
              .join(BookLanding.book)
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

    # --- 3) Нормализуем все найденные элементы и считаем счётчики (без учёта фильтра типов!) ---
    scored_items: List[Dict[str, Any]] = []

    # Авторы
    for a in authors:
        score = _text_score(a.name, qn, tokens)
        scored_items.append({
            "type": "author",
            "id": a.id,
            "name": a.name,
            "photo": a.photo,
            "language": a.language,
            "_score": score,
            "_tie": (0, a.id),
        })

    # Курсы (лендинги) — пониженный вес slug
    for l in landings:
        title_s = _text_score(l.landing_name, qn, tokens)
        slug_s  = _text_score(l.page_name, qn, tokens)
        score   = int(TITLE_WEIGHT * title_s + SLUG_WEIGHT * slug_s)
        score  += _authors_score(list(l.authors or []), qn, tokens, scale=0.8)
        # необязательный «толчок» популярности, если поле есть
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
        title_s      = _text_score(bl.landing_name, qn, tokens)
        book_title_s = _text_score(bl.book.title if bl.book else None, qn, tokens)
        slug_s       = _text_score(bl.page_name, qn, tokens)
        score        = max(title_s, book_title_s) + int(SLUG_WEIGHT * slug_s)
        book_authors = list((bl.book.authors if bl.book else []) or [])
        score       += _authors_score(book_authors, qn, tokens, scale=0.8)
        scored_items.append({
            "type": "book_landing",
            "id": bl.id,
            "landing_name": bl.landing_name,
            "page_name": bl.page_name,
            "preview_photo": bl.preview_photo,
            "old_price": bl.old_price,
            "new_price": bl.new_price,
            "language": bl.language,
            "book_title": bl.book.title if bl.book else None,
            "cover_url": bl.book.cover_url if bl.book else None,
            "authors": [{"id": au.id, "name": au.name, "photo": au.photo, "language": au.language} for au in book_authors],
            "_score": score,
            "_tie": (2, bl.id),
        })

    # Счётчики (зависят только от текста запроса и языков)
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

    returned = len(filtered_items)   # отдали всё
    # чтобы не ломать существующий контракт схемы:
    limit_value = returned           # считаем, что «лимит = total» (никакого урезания)
    truncated = False

    return {
        "counts": counts_all,        # зависит только от языка (и q), не от типов
        "total": total_all,
        "returned": returned,
        "limit": limit_value,
        "truncated": truncated,
        "authors": authors_out,
        "landings": landings_out,
        "book_landings": book_landings_out,
    }

