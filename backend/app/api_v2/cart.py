from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, selectinload
from ..db.database import get_db
from ..dependencies.auth import get_current_user
from ..models.models_v2 import User, Cart, CartItem, Landing, CartItemType
from ..schemas_v2.cart import CartResponse
from ..services_v2.cart_service import get_or_create_cart, _safe_price
from ..services_v2 import cart_service as cs

router = APIRouter()

def _calc_discount(n: int) -> float:
    """
    Возвращает дробную скидку для n курсов:
      0–1 courses -> 0%
      2 -> 5%; 3 -> 10%; 4 -> 15%
      >4 -> 15% + (n-4)*2.5%
    """
    if n < 2:
        return 0.0
    if n <= 4:
        return 0.05 * (n - 1)
    return 0.15 + 0.025 * (n - 4)

@router.get("", response_model=CartResponse)
def my_cart(
    db: Session        = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1) Получаем или создаём корзину
    cart = get_or_create_cart(db, current_user)

    # 2) Жадно подгружаем все связи
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
    # 3) Считаем суммы по новым и старым ценам
    total_new = sum(item.price for item in cart.items)
    total_old = sum(
        _safe_price(item.landing.old_price or 0)
        for item in cart.items if item.landing
    )

    # 4) Собираем уникальные course_ids
    count = sum(1 for item in cart.items
                if item.type == CartItemType.LANDING)

    # 5) Вычисляем текущую и следующую скидку
    disc_curr = _calc_discount(count)
    disc_next = _calc_discount(count + 1)

    # 6) Итоговая сумма с учётом скидки и баланса
    discounted = total_new * (1 - disc_curr)
    final_pay = max(discounted - current_user.balance, 0.0)

    # 7) Возвращаем dict под Pydantic
    return {
        "total_amount": round(discounted, 2),
        "total_old_amount": total_old,
        "current_discount": round(disc_curr * 100, 2),
        "next_discount": round(disc_next * 100, 2),
        "total_amount_with_balance_discount": final_pay,
        "updated_at": cart.updated_at,
        "items": cart.items,
    }

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