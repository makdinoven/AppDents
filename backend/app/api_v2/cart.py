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

@router.get("", response_model=CartResponse)
def my_cart(
    db: Session        = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1) Получаем/создаём корзину
    cart = get_or_create_cart(db, current_user)

    # 2) Жадная загрузка ОБОИХ типов
    cart = (
        db.query(Cart)
          .options(
              # курсовые лендинги
              selectinload(Cart.items)
                .selectinload(CartItem.landing)
                  .selectinload(Landing.authors),
              selectinload(Cart.items)
                .selectinload(CartItem.landing)
                  .selectinload(Landing.courses),
              # книжные лендинги
              selectinload(Cart.items)
                .selectinload(CartItem.book_landing)
                  .selectinload(BookLanding.books)
                    .selectinload(Book.authors),
          )
          .filter(Cart.id == cart.id)
          .first()
    )

    # 3) Сортировка по id убыв.
    cart.items = sorted(cart.items or [], key=lambda it: it.id, reverse=True)

    # 4) Тоталы по цене позиций (price)
    total_new = sum(_item_price(item) for item in cart.items)
    # Если нужна «старая» сумма — берём old_price из связей:
    total_old = 0.0
    for it in cart.items:
        if it.item_type == CartItemType.LANDING and it.landing:
            total_old += _safe_price(it.landing.old_price)
        elif it.item_type == CartItemType.BOOK and it.book_landing:
            total_old += _safe_price(it.book_landing.old_price)

    count = len(cart.items or [])
    disc_curr = _calc_discount(count)
    disc_next = _calc_discount(count + 1)
    discounted = total_new * (1 - disc_curr)
    final_with_balance = max(discounted - (current_user.balance or 0.0), 0.0)

    # 5) Сериализация items
    items = [_serialize_cart_item(it) for it in cart.items]

    return {
        "total_amount": round(discounted, 2),
        "total_old_amount": round(total_old, 2),
        "total_new_amount": round(total_new, 2),
        "current_discount": round(disc_curr * 100, 2),
        "next_discount": round(disc_next * 100, 2),
        "total_amount_with_balance_discount": round(final_with_balance, 2),
        "updated_at": cart.updated_at,
        "items": items,
    }

# ─────────── КУРСОВЫЕ ЛЕНДИНГИ ───────────

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
    cs.add_book_landing(db, current_user, landing_id)
    logger.info(
        "[CART] POST add BOOK-LANDING user_id=%s book_landing_id=%s",
        current_user.id, landing_id
    )
    return my_cart(db, current_user)

@router.delete("/book-landings/{landing_id}", response_model=CartResponse,
               summary="Удалить книжный лендинг из корзины")
def remove_book_landing_from_cart(
    landing_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cs.remove_book_landing(db, current_user, landing_id)
    logger.info(
        "[CART] DELETE BOOK-LANDING user_id=%s book_landing_id=%s",
        current_user.id, landing_id
    )
    return my_cart(db, current_user)

# ─────────── Предпросмотр (для гостей): пока оставим только курс-лендинги ───────────

@router.post(
    "/preview",
    response_model=CartResponse,
    summary="Предпросмотр корзины (без сохранения в БД, пока только курсовые лендинги)",
)
def cart_preview(
    landing_ids: List[int] = Body(..., embed=True, example=[101, 102, 103]),
    db: Session = Depends(get_db),
):
    uniq_ids, seen = [], set()
    for lid in landing_ids:
        if lid not in seen:
            uniq_ids.append(lid)
            seen.add(lid)
    if not uniq_ids:
        raise HTTPException(400, "landing_ids array is empty")

    landings = (
        db.query(Landing)
          .options(
              selectinload(Landing.authors),
              selectinload(Landing.courses),
          )
          .filter(Landing.id.in_(uniq_ids))
          .all()
    )
    if len(landings) != len(uniq_ids):
        missing = set(uniq_ids) - {l.id for l in landings}
        raise HTTPException(404, f"Landing(s) not found: {sorted(missing)}")

    landing_by_id = {l.id: l for l in landings}
    ordered = [landing_by_id[lid] for lid in uniq_ids]

    total_new = sum(_safe_price(l.new_price) for l in ordered)
    total_old = sum(_safe_price(l.old_price) for l in ordered)

    count = len(ordered)
    disc_curr = _calc_discount(count)
    disc_next = _calc_discount(count + 1)
    discounted = total_new * (1 - disc_curr)

    now = datetime.utcnow()
    items: List[Dict[str, Any]] = []
    for l in ordered:
        items.append({
            "id": 0,
            "item_type": "LANDING",
            "added_at": now,
            "landing": LandingInCart.from_orm(l),
        })

    return {
        "total_amount": round(discounted, 2),
        "total_old_amount": round(total_old, 2),
        "total_new_amount": round(total_new, 2),
        "current_discount": round(disc_curr * 100, 2),
        "next_discount": round(disc_next * 100, 2),
        "total_amount_with_balance_discount": 0,
        "updated_at": now,
        "items": items,
    }
