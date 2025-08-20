from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, Body, HTTPException
from sqlalchemy.orm import Session, selectinload
from ..db.database import get_db
from ..dependencies.auth import get_current_user
from ..models.models_v2 import User, Cart, CartItem, Landing, CartItemType
from ..schemas_v2.cart import CartResponse, CartItemOut, LandingInCart
from ..services_v2.cart_service import get_or_create_cart, _safe_price
from ..services_v2 import cart_service as cs

router = APIRouter()

MAX_COURSES_FOR_DISCOUNT = 24      # точка, на которой скидка фиксируется
_EXTRA_STEP = 0.025             # 2,5 % → 0.025 в дробном виде


def _calc_discount(n: int) -> float:
    """
    Возвращает дробную скидку для n курсов.

    Правила:
      ▸ 0–1 курс   → 0 %
      ▸ 2 курс     → 5 %
      ▸ 3 курс     → 10 %
      ▸ 4 курс     → 15 %
      ▸ 5 курс     → 20 %
      ▸ 6–25 курсов→ 20 % + 2,5 % за каждый курс сверх пяти
      ▸ >25        → такая же скидка, как при 25 (70 %)

    При n > 25 можно заменить "срез" на ValueError, если нужно жёсткое
    ограничение.
    """
    if n < 2:
        return 0.0

    n = min(n, MAX_COURSES_FOR_DISCOUNT)   # «срезаем» всё, что выше 25

    if n <= 5:
        return 0.03 * (n - 1)              # шаг 5 % до 5 курсов

    # линейно наращиваем от 20 % (при n=5) до 70 % (при n=25)
    return 0.12 + _EXTRA_STEP * (n - 5)

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
    cart.items = sorted(cart.items, key=lambda it: it.id, reverse=True)
    # 3) Считаем суммы по новым и старым ценам
    total_new = sum(
        _safe_price(item.landing.new_price or 0)
        for item in cart.items if item.landing
                    )
    total_old = sum(
        _safe_price(item.landing.old_price or 0)
        for item in cart.items if item.landing
    )

    # 4) Собираем уникальные course_ids
    count = sum(1 for item in cart.items)

    # 5) Вычисляем текущую и следующую скидку
    disc_curr = _calc_discount(count)
    disc_next = _calc_discount(count + 1)

    # 6) Итоговая сумма с учётом скидки и баланса
    discounted = total_new * (1 - disc_curr)
    final_pay = max(discounted - current_user.balance, 0.0)
    pay_with_balance = max(discounted - current_user.balance, 0.0)
    print(f"DEBUG: discounted={discounted}, balance={current_user.balance}")

    # 7) Возвращаем dict под Pydantic
    return {
        "total_amount": round(discounted, 2),
        "total_old_amount": total_old,
        "total_new_amount": total_new,
        "current_discount": round(disc_curr * 100, 2),
        "next_discount": round(disc_next * 100, 2),
        "total_amount_with_balance_discount": round(pay_with_balance,2),
        "updated_at": cart.updated_at,
        "items": cart.items,
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

@router.post(
    "/preview",
    response_model=CartResponse,
    summary="Предпросмотр корзины (без сохранения в БД)",
)
def cart_preview(
    landing_ids: List[int] = Body(..., embed=True, example=[101, 102, 103]),
    db: Session = Depends(get_db),
):
    """
    Возвращает все те же поля, что `/api/cart`, **но**:

    * корзина и элементы НЕ создаются в БД;
    * `added_at` = `datetime.utcnow()` (он фронту обычно не критичен);
    * `user_id` не нужен — работает для гостей.
    """

    # 1. Убираем дубликаты, сохраняем порядок
    uniq_ids = []
    seen = set()
    for lid in landing_ids:
        if lid not in seen:
            uniq_ids.append(lid)
            seen.add(lid)

    if not uniq_ids:
        raise HTTPException(400, "landing_ids array is empty")

    # 2. Тащим лендинги одним запросом + авторы + курсы
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

    # 3. Отсортируем в том же порядке, что пришёл с фронта
    landing_by_id = {l.id: l for l in landings}
    ordered = [landing_by_id[lid] for lid in uniq_ids]

    # 4. Считаем суммы
    total_new = sum(_safe_price(l.new_price) for l in ordered)
    total_old = sum(_safe_price(l.old_price) for l in ordered)

    count = len(ordered)
    disc_curr = _calc_discount(count)
    disc_next = _calc_discount(count + 1)

    discounted = total_new * (1 - disc_curr)

    # 5. Собираем items под CartResponse
    now = datetime.utcnow()
    items: List[CartItemOut] = []
    for l in ordered:
        items.append(
            CartItemOut(
                id=0,                     # фиктивный
                item_type="LANDING",
                added_at=now,
                landing=LandingInCart.from_orm(l),
            )
        )

    return {
        "total_amount": round(discounted, 2),
        "total_old_amount": total_old,
        "total_new_amount": total_new,
        "current_discount": round(disc_curr * 100, 2),
        "next_discount": round(disc_next * 100, 2),
        "total_amount_with_balance_discount": 0,
        "updated_at": now,
        "items": items,
    }
