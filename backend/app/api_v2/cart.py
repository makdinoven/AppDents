# app/api/cart.py
# Полная версия роутера корзины с учётом книг
# ВНИМАНИЕ: если у вас другой путь импорта — поправьте только импорты ниже.
import os
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

# ↓ импортируйте ваши зависимости ровно так, как у вас в проекте
from  ..services_v2.cart_service import (
    get_or_create_cart,
    add_book_landing as cs_add_book,
    remove_book_landing as cs_remove_book,
)
from ..models.models_v2 import (
    Cart,
    CartItem,
    CartItemType,  # Enum('LANDING','BOOK') — как договорились
    Landing,
    Book,
    User, BookLanding,
)
from .users import get_current_user           # если у вас другой путь — поправьте
from ..db.database import get_db                        # idem

logger = logging.getLogger(__name__)
router = APIRouter()


# ────────────────────────── ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ─────────────────────────

def _safe_price(v) -> float:
    try:
        return float(v or 0)
    except Exception:
        return 0.0


def _calc_discount(count_courses: int) -> float:
    """
    Возвращает скидку (в долях, 0..1) ТОЛЬКО по числу курсов.
    Таблицу можно задать через ENV DISCOUNT_TABLE, например:
      DISCOUNT_TABLE="1:0,2:0.05,3:0.10,5:0.15"
    Если ENV нет — дефолт: 1→0; 2→5%; 3→10%; 5→15%.
    Выбирается максимальный ключ <= count_courses.
    """
    ds_env = os.getenv("DISCOUNT_TABLE", "1:0,2:0.05,3:0.10,5:0.15")
    try:
        table = {}
        for pair in ds_env.split(","):
            k, v = pair.split(":")
            table[int(k.strip())] = float(v.strip())
        best_key = max([k for k in table.keys() if k <= count_courses], default=0)
        return table.get(best_key, 0.0)
    except Exception as exc:
        logger.warning("DISCOUNT_TABLE parse error '%s': %s", ds_env, exc)
        return 0.0


def _serialize_landing(db: Session, landing_id: int) -> Optional[dict]:
    l = db.query(Landing).get(landing_id)
    if not l:
        logger.warning("[CART] landing_id=%s not found", landing_id)
        return None
    # Сериализуем «лёгкую» карточку лендинга (не меняйте поля, если фронт их ждёт)
    return {
        "id": l.id,
        "slug": getattr(l, "slug", None),
        "landing_name": getattr(l, "landing_name", None),
        "main_image": getattr(l, "main_image", None),
    }


def _serialize_book(db: Session, book_id: int) -> Optional[dict]:
    b = db.query(Book).get(book_id)
    if not b:
        logger.warning("[CART] book_id=%s not found", book_id)
        return None
    return {
        "id": b.id,
        "title": b.title,
        "slug": b.slug,
        "cover_url": b.cover_url,
    }
def _serialize_book_landing_and_book(db: Session, book_landing_id: int) -> Optional[dict]:
    """
    Возвращает краткую карточку КНИГИ по book_landing_id (т.е. сериализуем саму книгу,
    которая привязана к лендингу). Сейчас у BookLanding одна книга (book_id).
    """
    bl = db.query(BookLanding).get(book_landing_id)
    if not bl:
        logger.warning("[CART] book_landing_id=%s not found", book_landing_id)
        return None

    book = db.query(Book).get(bl.book_id)
    if not book:
        logger.warning("[CART] Book not found for book_landing_id=%s (book_id=%s)", book_landing_id, bl.book_id)
        return None

    # фронту достаточно карточки книги; цену берём из item.price
    return {
        "id": book.id,
        "title": book.title,
        "slug": book.slug,
        "cover_url": book.cover_url,
        # если нужно — можно добавить поля лендинга:
        # "landing_name": bl.landing_name,
        # "page_name": bl.page_name,
    }

def _serialize_book_landing_and_book(db: Session, book_landing_id: int) -> Optional[dict]:
    """
    Возвращает краткую карточку КНИГИ по book_landing_id (т.е. сериализуем саму книгу,
    которая привязана к лендингу). Сейчас у BookLanding одна книга (book_id).
    """
    bl = db.query(BookLanding).get(book_landing_id)
    if not bl:
        logger.warning("[CART] book_landing_id=%s not found", book_landing_id)
        return None

    book = db.query(Book).get(bl.book_id)
    if not book:
        logger.warning("[CART] Book not found for book_landing_id=%s (book_id=%s)", book_landing_id, bl.book_id)
        return None

    # фронту достаточно карточки книги; цену берём из item.price
    return {
        "id": book.id,
        "title": book.title,
        "slug": book.slug,
        "cover_url": book.cover_url,
        # если нужно — можно добавить поля лендинга:
        # "landing_name": bl.landing_name,
        # "page_name": bl.page_name,
    }


# ──────────────────────────────── GET /api/cart ─────────────────────────────

@router.get("", summary="Получить текущую корзину пользователя")
def get_cart(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Возвращает корзину со всеми позициями.
    Правила:
      • скидка считается ТОЛЬКО по курсам (LANDING).
      • книги (BOOK) прибавляются поверх, не влияя на скидку.
    """
    cart: Cart = get_or_create_cart(db, user)

    # Собираем элементы
    items: List[dict] = []
    courses_sum = 0.0
    books_sum = 0.0
    courses_count = 0
    books_count = 0

    for it in (cart.items or []):
        item_type = it.item_type.value if hasattr(it.item_type, "value") else str(it.item_type)
        price = _safe_price(getattr(it, "price", 0.0))

        if item_type == "LANDING":
            # Курсовая позиция
            ser = _serialize_landing(db, it.landing_id)
            if not ser:
                # битая ссылка — пропускаем
                continue
            courses_sum += price
            courses_count += 1
            items.append({
                "id": it.id,
                "price": price,
                "item_type": "LANDING",
                "landing": ser,
                "book": None,
            })


        elif item_type == "BOOK":
            # Книжный лендинг. В позиции price = цена ЭТОГО book_landin
            ser = _serialize_book_landing_and_book(db, it.book_landing_id)

            if not ser:
                continue

            books_sum += price
            books_count += 1
            items.append({
                "id": it.id,
                "price": price,
                "item_type": "BOOK",
                "landing": None,
                "book": ser,  # карточка самой КНИГИ
                # если фронту нужно знать какой именно лендинг был добавлен:
                "book_landing_id": it.book_landing_id,

            })

        else:
            logger.warning("[CART] Unknown item_type=%s, item_id=%s", item_type, it.id)

    # Скидка — ТОЛЬКО по курсам
    current_discount = _calc_discount(courses_count)
    next_discount = _calc_discount(courses_count + 1)

    discount_value = round(courses_sum * current_discount, 2)
    total_amount = round((courses_sum - discount_value) + books_sum, 2)

    # Не меняем БД в GET, но если хотите — можно синхронизировать cart.total_amount тут
    response = {
        "id": cart.id,
        "total_amount": total_amount,
        "subtotal_courses": round(courses_sum, 2),
        "subtotal_books": round(books_sum, 2),
        "courses_count": courses_count,
        "books_count": books_count,
        "current_discount": current_discount,
        "next_discount": next_discount,
        "items": items,
    }

    logger.debug(
        "[CART] GET user_id=%s cart_id=%s courses=%s books=%s total=%s",
        user.id, cart.id, courses_count, books_count, total_amount
    )
    return response


# ───────────────────── ДОП. ЭНДПОИНТЫ ДЛЯ КНИГ (для удобства) ───────────────

@router.post("/book-landings/{landing_id}", summary="Добавить книжный лендинг в корзину")
def add_book_landing_to_cart(
    landing_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cart = cs_add_book(db, user, landing_id)
    logger.info("[CART] POST add BOOK-LANDING user_id=%s book_landing_id=%s cart_id=%s", user.id, landing_id, cart.id)
    return get_cart(db=db, user=user)


@router.delete("/book-landings/{landing_id}", summary="Удалить книжный лендинг из корзины")
def remove_book_landing_from_cart(
    landing_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cart = cs_remove_book(db, user, landing_id)
    logger.info("[CART] DELETE BOOK-LANDING user_id=%s book_landing_id=%s cart_id=%s", user.id, landing_id, cart.id)
    return get_cart(db=db, user=user)

