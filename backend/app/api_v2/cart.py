from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session, selectinload
from typing import List, Set

from ..db.database import get_db
from ..dependencies.auth import get_current_user
from ..models.models_v2 import User, CartItemType, Cart, CartItem, Landing
from ..services_v2 import cart_service as cs
from ..services_v2.stripe_service import create_checkout_session    # ← уже есть:contentReference[oaicite:0]{index=0}:contentReference[oaicite:1]{index=1}
from ..schemas_v2.cart import CartResponse
from ..services_v2.cart_service import get_or_create_cart

router = APIRouter()

# ── CRUD ────────────────────────────────────────────────────────────────
@router.get("", response_model=CartResponse)
def my_cart(
    db: Session         = Depends(get_db),
    current_user: User  = Depends(get_current_user),
):
    # 1) убедимся, что корзина есть
    cart = get_or_create_cart(db, current_user)

    # 2) подгружаем все нужные связи
    cart = (
        db.query(Cart)
          .options(
             selectinload(Cart.items)
               .selectinload(CartItem.landing)
                 .selectinload(Landing.authors),
             selectinload(Cart.items)
               .selectinload(CartItem.landing)
                 .selectinload(Landing.courses),
          )
          .filter(Cart.id == cart.id)
          .first()
    )
    return cart

@router.post("/landing/{landing_id}", response_model=CartResponse)
def add_landing(
    landing_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return cs.add_landing(db, current_user, landing_id)

@router.delete("/item/{item_id}", response_model=CartResponse)
def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return cs.remove_item(db, current_user, item_id)

@router.delete("/clear", response_model=CartResponse)
def clear(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return cs.clear_cart(db, current_user)

# ── Checkout ────────────────────────────────────────────────────────────
class CartCheckoutIn(BaseModel):
    region      : str
    success_url : str = "https://app.com/payment-success"
    cancel_url  : str = "https://app.com/payment-cancel"
    fbp         : str | None = None
    fbc         : str | None = None

@router.post("/checkout")
def cart_checkout(
    data: CartCheckoutIn,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cart = cs._get_or_create_cart(db, current_user)
    if not cart.items:
        raise HTTPException(400, "Корзина пуста")

    # 1. Собираем все course_ids из лендингов корзины
    course_ids: List[int] = []
    course_names: List[str] = []
    for it in cart.items:
        if it.item_type != CartItemType.LANDING:
            continue                    # на будущее (BOOK и т.д.)

        for c in it.landing.courses:
            course_ids.append(c.id)
            course_names.append(c.name)

    course_ids = list(dict.fromkeys(course_ids))      # dedup с сохранением порядка
    if not course_ids:
        raise HTTPException(400, "В корзине нет курсов для покупки")

    # 2. Создаём Stripe-сессию через _уже существующую_ функцию
    checkout_url = create_checkout_session(
        db=db,
        email=current_user.email,
        course_ids=course_ids,
        product_name="Cart: " + ", ".join(course_names),
        price_cents=int(cart.total_amount * 100),
        region=data.region,
        success_url=data.success_url,
        cancel_url=data.cancel_url,
        request=request,
        fbp=data.fbp,
        fbc=data.fbc,
    )
    return {"checkout_url": checkout_url}
