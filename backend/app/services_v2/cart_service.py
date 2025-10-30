import logging
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, selectinload
from ..models.models_v2 import Cart, CartItem, CartItemType, Landing, User, BookLanding, Book

log = logging.getLogger(__name__)

def _safe_price(v) -> float:
    try:
        return float(v)
    except Exception:
        return 0.0

def get_or_create_cart(db: Session, user: User) -> Cart:
    cart = db.query(Cart).filter(Cart.user_id == user.id).first()
    if not cart:
        cart = Cart(user_id=user.id, total_amount=0.0)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


def _recalc_total(cart: Cart) -> None:
    """
    Пересчитывает итог по всем позициям корзины (LANDING + BOOK).
    Скидка применяется на уровне роута получения корзины (как и было),
    поэтому здесь просто суммируем валовые цены.
    """
    total = 0.0
    for i in cart.items:
        total += _safe_price(getattr(i, "price", 0.0))

    cart.total_amount = round(total, 2)
    cart.updated_at = datetime.utcnow()

# ────────────────────────────────────────────────────────────────────────
# Публичное API
# ────────────────────────────────────────────────────────────────────────
def add_landing(db: Session, user: User, landing_id: int) -> Cart:
    cart   = get_or_create_cart(db, user)
    landing = db.query(Landing).get(landing_id)
    if not landing:
        raise ValueError("Landing not found")

    if any(i.landing_id == landing_id for i in cart.items):
        return cart                                  # уже в корзине

    item = CartItem(
        cart_id   = cart.id,
        item_type = CartItemType.LANDING,
        landing_id= landing_id,
        price     = _safe_price(landing.new_price),
        added_at = datetime.utcnow(),
    )
    db.add(item)
    _recalc_total(cart)
    db.commit()
    db.refresh(cart)
    return cart

def remove_by_landing(db: Session, user: User, landing_id: int) -> Cart:
    cart = get_or_create_cart(db, user)
    item = next((i for i in cart.items if i.landing_id == landing_id), None)
    if not item:
        raise HTTPException(404, "Лендинг не найден в корзине")
    db.delete(item)
    _recalc_total(cart)
    db.commit()
    db.refresh(cart)
    return cart

def clear_cart(db: Session, user: User):
    """
    Полностью очищает корзину пользователя и обнуляет сумму.
    """
    cart = get_or_create_cart(db, user)
    if not cart.items:
        return cart                    # корзина уже пуста

    # удаляем все позиции
    for item in list(cart.items):
        db.delete(item)

    cart.total_amount = 0.0
    cart.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(cart)
    return cart

def remove_landing_raw(db: Session, cart: Cart, landing_id: int) -> None:
    item = next((i for i in cart.items if i.landing_id == landing_id), None)
    if item:
        db.delete(item)

def remove_silent(db: Session, user: User, landing_id: int) -> Cart:
    """Удаляет landing без HTTP-исключений и пересчёта ошибок."""
    cart = get_or_create_cart(db, user)
    remove_landing_raw(db, cart, landing_id)
    _recalc_total(cart)
    db.commit()
    db.refresh(cart)
    return cart

def _book_min_price(db: Session, book_id: int, language: str | None = None) -> float:
    """
    Возвращает минимальную цену книги по НЕ скрытым лендингам.
    Если language передан — сначала пытаемся найти по языку,
    иначе берём минимальную среди всех.
    """
    q = db.query(BookLanding).filter(
        BookLanding.book_id == book_id,
        BookLanding.is_hidden.is_(False),
        BookLanding.new_price.isnot(None),
    )
    if language:
        by_lang = q.filter(BookLanding.language == language.upper()).order_by(BookLanding.new_price.asc()).first()
        if by_lang:
            return float(by_lang.new_price)

    any_lang = q.order_by(BookLanding.new_price.asc()).first()
    if not any_lang:
        raise HTTPException(status_code=400, detail="No visible book landings with price")
    return float(any_lang.new_price)

def add_book_landing(db: Session, user: User, book_landing_id: int) -> Cart:
    """
    Кладём в корзину КНИЖНЫЙ ЛЕНДИНГ как item_type=BOOK.
    Цена позиции = new_price этого лендинга.
    """
    cart = get_or_create_cart(db, user)

    # уже в корзине?
    exists = (
        db.query(CartItem)
          .filter(
              CartItem.cart_id == cart.id,
              CartItem.item_type == CartItemType.BOOK,
              CartItem.book_landing_id == book_landing_id,
          )
          .first()
    )
    if exists:
        log.info("[CART] BOOK landing %s already in cart %s", book_landing_id, cart.id)
        return cart

    # ⟵ заменили books_bundle → books
    bl = (
        db.query(BookLanding)
          .options(selectinload(BookLanding.books))
          .get(book_landing_id)
    )

    if not bl or bl.is_hidden:
        raise HTTPException(status_code=404, detail="Book landing not found or hidden")
    if bl.new_price is None:
        raise HTTPException(status_code=400, detail="Book landing has no price")

    item = CartItem(
        cart_id=cart.id,
        item_type=CartItemType.BOOK,
        book_landing_id=bl.id,
        price=float(bl.new_price),
        added_at=datetime.utcnow(),
    )
    db.add(item)

    _recalc_total(cart)
    db.commit()
    db.refresh(cart)

    # лог тоже на новые связи
    log.info(
        "[CART] user=%s added BOOK landing %s (price=%.2f, books=%s)",
        user.id, bl.id, float(bl.new_price), [b.id for b in (bl.books or [])]
    )
    return cart


def remove_book_landing(db: Session, user: User, book_landing_id: int) -> Cart:
    cart = get_or_create_cart(db, user)
    item = (
        db.query(CartItem)
          .filter(CartItem.cart_id == cart.id,
                  CartItem.item_type == CartItemType.BOOK,
                  CartItem.book_landing_id == book_landing_id)
          .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Book landing not in cart")

    db.delete(item)
    _recalc_total(cart)
    db.commit()
    db.refresh(cart)
    log.info("[CART] user=%s removed BOOK landing %s", user.id, book_landing_id)
    return cart


def remove_book_silent(db: Session, user: User, book_landing_id: int) -> Cart:
    """
    Тихо убирает книжный лендинг из корзины по book_landing_id (без исключений).
    """
    cart = get_or_create_cart(db, user)
    item = (
        db.query(CartItem)
          .filter(
              CartItem.cart_id == cart.id,
              CartItem.item_type == CartItemType.BOOK,
              CartItem.book_landing_id == book_landing_id
          )
          .first()
    )
    if item:
        db.delete(item)
        _recalc_total(cart)
        db.commit()
        db.refresh(cart)
    return cart

def add_book_landing_to_cart(db: Session, user: User, book_landing_id: int) -> Cart:
    """
    Добавить КНИЖНЫЙ ЛЕНДИНГ в корзину пользователя (тип позиции = BOOK).
    Цена позиции берется из new_price BookLanding.
    """
    # 1) получить/создать корзину
    from .cart_service import get_or_create_cart   # если функция в этом же файле — уберите импорт
    cart = get_or_create_cart(db, user)

    # 2) проверить, нет ли уже такого item
    exists = (
        db.query(CartItem)
          .filter(
              CartItem.cart_id == cart.id,
              CartItem.item_type == CartItemType.BOOK,
              CartItem.book_landing_id == book_landing_id,
          )
          .first()
    )
    if exists:
        log.info("[CART][BOOK] already in cart: user=%s cart=%s book_landing=%s",
                 user.id, cart.id, book_landing_id)
        return cart

    # 3) проверить наличие и валидность лендинга
    bl = (
        db.query(BookLanding)
          .options(selectinload(BookLanding.books))
          .get(book_landing_id)
    )
    if not bl or bl.is_hidden:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Book landing not found or hidden")
    if bl.new_price is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Book landing has no price")

    # 4) создать CartItem
    item = CartItem(
        cart_id=cart.id,
        item_type=CartItemType.BOOK,
        book_landing_id=bl.id,
        price=float(bl.new_price),      # фиксируем текущую цену в позиции
        added_at=datetime.utcnow(),
    )
    db.add(item)

    # 5) обновим updated_at корзины (и при желании пересчет total, если храните)
    cart.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(cart)
    log.info("[CART][BOOK] added: user=%s cart=%s book_landing=%s price=%.2f",
             user.id, cart.id, bl.id, float(bl.new_price))
    return cart


def remove_book_landing_from_cart(db: Session, user: User, book_landing_id: int) -> Cart:
    """
    Удалить КНИЖНЫЙ ЛЕНДИНГ из корзины пользователя (по book_landing_id).
    """
    from .cart_service import get_or_create_cart   # если функция в этом же файле — уберите импорт
    cart = get_or_create_cart(db, user)

    deleted = (
        db.query(CartItem)
          .filter(
              CartItem.cart_id == cart.id,
              CartItem.item_type == CartItemType.BOOK,
              CartItem.book_landing_id == book_landing_id,
          )
          .delete(synchronize_session=False)
    )

    if deleted:
        log.info("[CART][BOOK] removed: user=%s cart=%s book_landing=%s",
                 user.id, cart.id, book_landing_id)

    cart.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(cart)
    return cart
