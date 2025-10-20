# app/api_v2/cart.py

from datetime import datetime
from math import ceil
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, Body, HTTPException
from sqlalchemy.orm import Session, selectinload

from ..db.database import get_db
from ..dependencies.auth import get_current_user
from ..models.models_v2 import (
    User, Cart, CartItem, Landing, BookLanding, CartItemType, Author, Book
)
from ..schemas_v2.cart import (
    CartResponse, CartItemOut, LandingInCart,
    # Добавьте это в схемы (аналогично LandingInCart):
    # BookLandingInCart
)
from ..services_v2.cart_service import (
    add_book_landing_to_cart as svc_add_book_landing,
    remove_book_landing_from_cart as svc_remove_book_landing,
)
from ..services_v2.cart_service import get_or_create_cart, _safe_price
from ..services_v2 import cart_service as cs

import logging
logger = logging.getLogger(__name__)

router = APIRouter()

MAX_COURSES_FOR_DISCOUNT = 24
_EXTRA_STEP = 0.02

def _calc_discount(n: int) -> float:
    if n < 2:
        return 0.0
    n = min(n, MAX_COURSES_FOR_DISCOUNT)
    if n <= 5:
        return 0.03 * (n - 1)
    return 0.12 + _EXTRA_STEP * (n - 5)

def _item_price(item: CartItem) -> float:
    """
    Источник истины — поле price в CartItem.
    Если его вдруг нет/None, аккуратно падёмся к связанным сущностям.
    """
    if item.price is not None:
        return _safe_price(item.price)
    if item.item_type == CartItemType.LANDING and item.landing:
        return _safe_price(item.landing.new_price)
    if item.item_type == CartItemType.BOOK and item.book_landing:
        return _safe_price(item.book_landing.new_price)
    return 0.0

def _serialize_cart_item(item: CartItem) -> Dict[str, Any]:
    """
    Преобразует CartItem в dict под CartItemOut: либо с полем "landing",
    либо с полем "book_landing".
    """
    base = {
        "id": item.id,
        "item_type": item.item_type.value if hasattr(item.item_type, "value") else str(item.item_type),
        "added_at": item.added_at or datetime.utcnow(),
    }

    if item.item_type == CartItemType.LANDING and item.landing:
        return {
            **base,
            "landing": LandingInCart.from_orm(item.landing),
        }

    if item.item_type == CartItemType.BOOK and item.book_landing:
        # Если сделали BookLandingInCart — используйте его, иначе вернём «лёгкую» структуру
        bl = item.book_landing
        # авторы и один «главный» обложка берутся из привязанных книг
        authors_map = {}
        cover = None
        for b in (bl.books or []):
            if not cover and b.cover_url:
                cover = b.cover_url
            for a in (b.authors or []):
                if a.id not in authors_map:
                    authors_map[a.id] = {"id": a.id, "name": a.name, "photo": a.photo}

        return {
            **base,
            "book_landing": {
                "id": bl.id,
                "landing_name": bl.landing_name,
                "page_name": bl.page_name,
                "language": bl.language,
                "old_price": str(bl.old_price) if bl.old_price is not None else None,
                "new_price": str(bl.new_price) if bl.new_price is not None else None,
                "main_image": cover,
                "authors": list(authors_map.values()),
            },
        }

    # fallback — пустая «заглушка», чтобы ответ не падал
    return base

def _first_cover_from_book_landing(bl: BookLanding) -> str | None:
    # берём обложку первой привязанной книги (если есть)
    for b in bl.books or []:
        if b.cover_url:
            return b.cover_url
    return None

def _authors_from_book_landing(bl: BookLanding) -> list[dict]:
    seen = set()
    out = []
    for b in bl.books or []:
        for a in b.authors or []:
            if a.id not in seen:
                seen.add(a.id)
                out.append({"id": a.id, "name": a.name, "photo": a.photo})
    return out

def _book_ids(bl: BookLanding) -> list[int]:
    return [b.id for b in (bl.books or [])]

def _book_extra_info(bl: BookLanding) -> dict:
    """Собирает дополнительную информацию о книгах: страницы, издатели, года"""
    total_pages = 0
    publishers_set = set()
    years_set = set()
    
    for b in bl.books or []:
        if hasattr(b, "page_count") and b.page_count:
            total_pages += b.page_count
        if hasattr(b, "publishers"):
            for p in b.publishers or []:
                publishers_set.add(p.name)
        if hasattr(b, "publication_date") and b.publication_date:
            # извлекаем год из строки формата "YYYY-MM-DD" или просто "YYYY"
            year = b.publication_date[:4] if len(b.publication_date) >= 4 else b.publication_date
            if year:
                years_set.add(year)
    
    return {
        "total_pages": total_pages if total_pages > 0 else None,
        "publishers": sorted(list(publishers_set)),
        "publication_years": sorted(list(years_set)),
    }

@router.get("", response_model=CartResponse)
def my_cart(
    db: Session        = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cart = get_or_create_cart(db, current_user)

    cart = (
        db.query(Cart)
        .options(
            # КУРСЫ (как было)
            selectinload(Cart.items)
            .selectinload(CartItem.landing)
            .selectinload(Landing.authors),
            selectinload(Cart.items)
            .selectinload(CartItem.landing)
            .selectinload(Landing.courses),

            # КНИЖНЫЕ ЛЕНДИНГИ — ДОБАВИТЬ:
            selectinload(Cart.items)
            .selectinload(CartItem.book_landing)
            .selectinload(BookLanding.books)
            .selectinload(Book.authors),
            # Подгружаем также publishers для книг
            selectinload(Cart.items)
            .selectinload(CartItem.book_landing)
            .selectinload(BookLanding.books)
            .selectinload(Book.publishers),
        )
        .filter(Cart.id == cart.id)
        .first()
    )

    # отсортируем элементы
    cart.items = sorted(cart.items, key=lambda it: it.id, reverse=True)

    # --- суммы: учитываем и LANDING, и BOOK-LANDING
    def _price_of_item(it: CartItem) -> float:
        if it.landing is not None:
            return _safe_price(it.landing.new_price or 0)
        if it.book_landing is not None:
            return _safe_price(it.book_landing.new_price or 0)
        # fallback: цена из строки item.price (если она у тебя хранится) — опционально
        return _safe_price(it.price or 0)

    total_new = sum(_price_of_item(it) for it in cart.items)
    total_old = sum(
        _safe_price(it.landing.old_price) if it.landing is not None
        else _safe_price(it.book_landing.old_price) if it.book_landing is not None
        else 0
        for it in cart.items
    )

    count = sum(1 for it in cart.items if it.landing is not None)
    disc_curr = _calc_discount(count)
    disc_next = _calc_discount(count + 1)
    discounted = total_new * (1 - disc_curr)
    pay_with_balance = max(discounted - current_user.balance, 0.0)

    # --- Соберём items руками, чтобы в ответе были нужные поля
    def _landing_to_incart(l: Landing) -> dict:
        # твой текущий LandingInCart.from_orm(l) и так ок; оставлю явную форму
        return {
            "id": l.id,
            "page_name": l.page_name,
            "landing_name": l.landing_name,
            "preview_photo": l.preview_photo,
            "course_ids": [c.id for c in (l.courses or [])],
            "authors": [{"id": a.id, "name": a.name, "photo": a.photo} for a in (l.authors or [])],
            "old_price": str(l.old_price) if l.old_price is not None else None,
            "new_price": str(l.new_price) if l.new_price is not None else None,
        }

    def _book_landing_to_incart(bl: BookLanding) -> dict:
        # авторы = уник. из всех книг
        authors_map = {}
        for b in bl.books or []:
            for a in b.authors or []:
                authors_map[a.id] = {"id": a.id, "name": a.name, "photo": a.photo}
        authors = list(authors_map.values())

        # главная картинка — обложка первой книги (если есть)
        cover = None
        if bl.books:
            first = next((b for b in bl.books if getattr(b, "cover_url", None)), None)
            if first:
                cover = first.cover_url

        return {
            "id": bl.id,
            "page_name": bl.page_name,         # slug
            "landing_name": bl.landing_name,
            "cover": cover,                    # ⟵ вместо галереи (как ты просил раньше)
            "authors": authors,
            "old_price": str(bl.old_price) if bl.old_price is not None else None,
            "new_price": str(bl.new_price) if bl.new_price is not None else None,
            # опционально можно добавить tags или language, если нужно в UI
        }

    items_serialized = []
    for it in cart.items:
        if it.landing is not None:
            items_serialized.append({
                "id": it.id,
                "item_type": "LANDING",
                "added_at": it.added_at,
                "landing": _landing_to_incart(it.landing),
                "book_landing": None,     # для единообразия
            })
        elif it.book_landing is not None:
            bl = it.book_landing
            items_serialized.append({
                "id": it.id,
                "item_type": "BOOK",
                "added_at": it.added_at,
                "landing": None,  # для единообразия
                "book": {
                    "id": bl.id,
                    "page_name": bl.page_name,  # slug
                    "landing_name": bl.landing_name or "",  # название
                    "preview_photo": _first_cover_from_book_landing(bl),  # как у курсов
                    "book_ids": _book_ids(bl),  # ключ как ты просил
                    "authors": _authors_from_book_landing(bl),
                    "old_price": str(bl.old_price) if bl.old_price is not None else None,
                    "new_price": str(bl.new_price) if bl.new_price is not None else None,
                    **_book_extra_info(bl),  # добавляем доп. инфо о книгах
                },
            })
        else:
            # fallback на случай «битой» строки
            items_serialized.append({
                "id": it.id,
                "item_type": it.item_type.value if hasattr(it.item_type, "value") else it.item_type,
                "added_at": it.added_at,
                "landing": None,
                "book_landing": None,
            })

    return {
        "total_amount": round(discounted, 2),
        "total_old_amount": total_old,
        "total_new_amount": total_new,
        "current_discount": round(disc_curr * 100, 2),
        "next_discount": round(disc_next * 100, 2),
        "total_amount_with_balance_discount": round(pay_with_balance, 2),
        "updated_at": cart.updated_at,
        "items": items_serialized,
    }

@router.post("/landing/{landing_id}", response_model=CartResponse)
def add_landing(
    landing_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cs.add_landing(db, current_user, landing_id)
    return my_cart(db, current_user)

@router.delete("/landing/{landing_id}", response_model=CartResponse)
def delete_landing(
    landing_id: int,
    db: Session        = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cs.remove_by_landing(db, current_user, landing_id)
    return my_cart(db, current_user)

# ─────────── КНИЖНЫЕ ЛЕНДИНГИ ───────────

@router.post("/book-landings/{landing_id}", response_model=CartResponse,
             summary="Добавить книжный лендинг в корзину")
def add_book_landing_to_cart(
    landing_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc_add_book_landing(db, current_user, landing_id)
    # Возвращаем полную корзину тем же форматом, что /api/cart
    return my_cart(db=db, current_user=current_user)


@router.delete("/book-landings/{landing_id}", response_model=CartResponse,
               summary="Удалить книжный лендинг из корзины")
def remove_book_landing_from_cart(
    landing_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc_remove_book_landing(db, current_user, landing_id)
    return my_cart(db=db, current_user=current_user)

@router.post(
    "/preview",
    response_model=CartResponse,
    summary="Предпросмотр корзины (без сохранения в БД). Поддерживает курсовые и книжные лендинги.",
)
def cart_preview(
    cart_landing_ids: List[int] = Body(default=[], embed=True, description="ID курсовых лендингов"),
    cart_book_landing_ids: List[int] = Body(default=[], embed=True, description="ID книжных лендингов"),
    db: Session = Depends(get_db),
):
    """
    Возвращает тот же формат, что /api/cart, но:
      • ничего не создаётся в БД;
      • added_at = now;
      • скидка считается ТОЛЬКО по количеству курсовых лендингов.
    """

    # --- нормализуем вход, убираем дубликаты с сохранением порядка
    def _uniq(seq: List[int]) -> List[int]:
        seen = set()
        out = []
        for x in seq or []:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out

    landing_ids = _uniq(cart_landing_ids)
    book_landing_ids = _uniq(cart_book_landing_ids)

    if not landing_ids and not book_landing_ids:
        raise HTTPException(400, "Provide at least one of landing_ids or book_landing_ids")

    # --- тащим сущности одним махом
    landings: List[Landing] = []
    if landing_ids:
        landings = (
            db.query(Landing)
              .options(
                  selectinload(Landing.authors),
                  selectinload(Landing.courses),
              )
              .filter(Landing.id.in_(landing_ids))
              .all()
        )
        found = {l.id for l in landings}
        missing = [x for x in landing_ids if x not in found]
        if missing:
            raise HTTPException(404, f"Course landing(s) not found: {missing}")

    book_landings: List[BookLanding] = []
    if book_landing_ids:
        book_landings = (
            db.query(BookLanding)
              .options(
                  selectinload(BookLanding.books).selectinload(Book.authors),
                  selectinload(BookLanding.books).selectinload(Book.publishers),
              )
              .filter(BookLanding.id.in_(book_landing_ids))
              .all()
        )
        found = {b.id for b in book_landings}
        missing = [x for x in book_landing_ids if x not in found]
        if missing:
            raise HTTPException(404, f"Book landing(s) not found: {missing}")

    # --- упорядочим как пришло с фронта
    by_landing_id = {l.id: l for l in landings}
    ordered_landings = [by_landing_id[x] for x in landing_ids]

    by_book_landing_id = {b.id: b for b in book_landings}
    ordered_book_landings = [by_book_landing_id[x] for x in book_landing_ids]

    # --- суммы
    def _safe_str_price(x):  # локально, если _safe_price уже есть — лучше его
        return _safe_price(x) if x is not None else 0.0

    total_new = sum(_safe_str_price(l.new_price) for l in ordered_landings) + \
                sum(_safe_str_price(b.new_price) for b in ordered_book_landings)
    total_old = sum(_safe_str_price(l.old_price) for l in ordered_landings) + \
                sum(_safe_str_price(b.old_price) for b in ordered_book_landings)

    # скидка — только по курсовым
    count_courses = len(ordered_landings)
    disc_curr = _calc_discount(count_courses)
    disc_next = _calc_discount(count_courses + 1)

    discounted = total_new * (1 - disc_curr)

    # --- сборка items в том же формате, что /api/cart
    now = datetime.utcnow()
    items: List[Dict[str, Any]] = []

    # КУРСОВЫЕ ЛЕНДИНГИ
    for l in ordered_landings:
        items.append({
            "id": 0,
            "item_type": "LANDING",
            "added_at": now,
            "landing": {
                "id": l.id,
                "page_name": l.page_name,
                "landing_name": l.landing_name,
                "preview_photo": l.preview_photo,
                "course_ids": [c.id for c in (l.courses or [])],
                "authors": [{"id": a.id, "name": a.name, "photo": a.photo} for a in (l.authors or [])],
                "old_price": str(l.old_price) if l.old_price is not None else None,
                "new_price": str(l.new_price) if l.new_price is not None else None,
            },
            "book": None,
        })

    # КНИЖНЫЕ ЛЕНДИНГИ (делаем как в /api/cart → в поле "book")
    def _authors_from_book_landing(bl: BookLanding) -> list[dict]:
        seen = set()
        out = []
        for b in bl.books or []:
            for a in b.authors or []:
                if a.id not in seen:
                    seen.add(a.id)
                    out.append({"id": a.id, "name": a.name, "photo": a.photo})
        return out

    def _first_cover_from_book_landing(bl: BookLanding) -> str | None:
        for b in bl.books or []:
            if b.cover_url:
                return b.cover_url
        return None

    def _book_ids(bl: BookLanding) -> list[int]:
        return [b.id for b in (bl.books or [])]
    
    def _book_extra_info_local(bl: BookLanding) -> dict:
        """Локальная версия для cart_preview"""
        total_pages = 0
        publishers_set = set()
        years_set = set()
        
        for b in bl.books or []:
            if hasattr(b, "page_count") and b.page_count:
                total_pages += b.page_count
            if hasattr(b, "publishers"):
                for p in b.publishers or []:
                    publishers_set.add(p.name)
            if hasattr(b, "publication_date") and b.publication_date:
                year = b.publication_date[:4] if len(b.publication_date) >= 4 else b.publication_date
                if year:
                    years_set.add(year)
        
        return {
            "total_pages": total_pages if total_pages > 0 else None,
            "publishers": sorted(list(publishers_set)),
            "publication_years": sorted(list(years_set)),
        }

    for bl in ordered_book_landings:
        items.append({
            "id": 0,
            "item_type": "BOOK",
            "added_at": now,
            "landing": None,
            "book": {
                "id": bl.id,
                "page_name": bl.page_name,             # slug
                "landing_name": bl.landing_name or "",
                "preview_photo": _first_cover_from_book_landing(bl),
                "book_ids": _book_ids(bl),
                "authors": _authors_from_book_landing(bl),
                "old_price": str(bl.old_price) if bl.old_price is not None else None,
                "new_price": str(bl.new_price) if bl.new_price is not None else None,
                **_book_extra_info_local(bl),
            },
        })

    return {
        "total_amount": round(discounted, 2),
        "total_old_amount": round(total_old, 2),
        "total_new_amount": round(total_new, 2),
        "current_discount": round(disc_curr * 100, 2),
        "next_discount": round(disc_next * 100, 2),
        "total_amount_with_balance_discount": 0,  # превью без баланса
        "updated_at": now,
        "items": items,
    }

