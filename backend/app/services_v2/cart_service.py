from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session
from ..models.models_v2 import Cart, CartItem, CartItemType, Landing, User

def _safe_price(v) -> float:
    try:
        return float(v)
    except Exception:
        return 0.0

def get_or_create_cart(db: Session, user: User) -> Cart:
    if user.cart:
        return user.cart
    cart = Cart(user_id=user.id)
    db.add(cart)
    db.commit()
    db.refresh(cart)
    return cart

def _recalc_total(cart: Cart) -> None:
    cart.total_amount = sum(i.price for i in cart.items)

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



