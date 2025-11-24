import s from "./Cart.module.scss";
import s_footer from "./CartFooter/CartFooter.module.scss";
import { useEffect, useRef } from "react";
import { Trans } from "react-i18next";
import CartItem from "./CartItem/CartItem.tsx";
import { useDispatch, useSelector } from "react-redux";
import { AppDispatchType, AppRootStateType } from "../../shared/store/store.ts";
import {
  getCartPreview,
  removeCartItem,
} from "../../shared/store/actions/cartActions.ts";
import { CartIcon } from "../../shared/assets/icons/index.ts";
import CartFooter from "./CartFooter/CartFooter.tsx";
import { cartStorage } from "../../shared/api/cartApi/cartStorage.ts";
import { syncCartFromStorage } from "../../shared/store/slices/cartSlice.ts";
import {
  CartItemBookType,
  CartItemCourseType,
  CartItemKind,
} from "../../shared/api/cartApi/types.ts";
import ModalOverlay from "../../shared/components/Modals/ModalOverlay/ModalOverlay.tsx";
import ModalCloseButton from "../../shared/components/ui/ModalCloseButton/ModalCloseButton.tsx";
import useOutsideClick from "../../shared/common/hooks/useOutsideClick.ts";
import { usePayment } from "../../shared/common/hooks/usePayment.tsx";

const Cart = () => {
  const closeModalRef = useRef<() => void>(null);
  const modalRef = useRef<HTMLDivElement | null>(null);
  const dispatch = useDispatch<AppDispatchType>();
  const { isLogged } = useSelector((state: AppRootStateType) => state.user);
  const { items, quantity, total_amount } = useSelector(
    (state: AppRootStateType) => state.cart,
  );
  const isCartEmpty = quantity === 0;
  useOutsideClick(modalRef, () => {
    closeCart();
  });

  useEffect(() => {
    if (!isLogged && quantity > 0) {
      dispatch(getCartPreview());
    }
  }, [isLogged, quantity]);

  const courseItems = items.filter(
    (item): item is { data: CartItemCourseType; item_type: "LANDING" } =>
      item.item_type === "LANDING",
  );
  const bookItems = items.filter(
    (item): item is { data: CartItemBookType; item_type: "BOOK" } =>
      item.item_type === "BOOK",
  );

  const paymentData = {
    landing_ids: courseItems.map((item) => item.data.id),
    book_landing_ids: bookItems.map((item) => item.data.id),
    course_ids: courseItems.map((item) => item.data.course_ids).flat(),
    book_ids: bookItems.map((item) => item.data.book_ids).flat(),
    price_cents: Number((total_amount * 100).toFixed(0)),
    source: "CART" as const,
    from_ad: false,
  };

  const {
    loading: cartPaymentLoading,
    isBalanceUsed,
    balance,
    toggleBalance,
    handlePayment,
    language,
  } = usePayment({
    paymentData,
    isFree: false,
    isOffer: false,
  });

  const handleDeleteCartItem = async (id: number, type: CartItemKind) => {
    if (isLogged) {
      // setLoading(true);
      await dispatch(removeCartItem({ id, type }));
      // setLoading(false);
    } else {
      cartStorage.removeItem(type, id);
      dispatch(syncCartFromStorage());
    }
  };

  const closeCart = () => {
    closeModalRef.current?.();
  };

  return (
    <ModalOverlay
      isVisibleCondition={true}
      isUsedAsPage
      modalPosition="right"
      onInitClose={(fn) => (closeModalRef.current = fn)}
    >
      <div ref={modalRef} className={`${s.cart} ${isCartEmpty ? s.empty : ""}`}>
        <div className={s.cart_header}>
          <ModalCloseButton className={s.close_button} onClick={closeCart} />
          {!isCartEmpty && (
            <h2 className={s.cart_title}>
              <Trans i18nKey="cart.title" />
            </h2>
          )}
          <div className={s.cart_icon_wrapper}>
            <CartIcon className={s.cart_icon} />
            {quantity > 0 && <span className={s.circle}>{quantity}</span>}
          </div>
        </div>

        {!isCartEmpty ? (
          <>
            <ul className={s.cart_items}>
              {items.map((item) => (
                <CartItem
                  key={item.data.id}
                  language={language}
                  item={item.data}
                  type={item.item_type}
                  onDelete={handleDeleteCartItem}
                />
              ))}
            </ul>
            <CartFooter
              paymentLoading={cartPaymentLoading}
              quantity={quantity}
              balance={balance!}
              setIsBalanceUsed={toggleBalance}
              isBalanceUsed={isBalanceUsed}
              isLogged={isLogged}
              handlePay={handlePayment}
            />
          </>
        ) : (
          <>
            <div className={s.empty_container}>
              <h2>
                <Trans i18nKey={"cart.empty.title"} />
              </h2>
              <p>
                <Trans i18nKey={"cart.empty.haventAdded"} />
              </p>
            </div>
            <button
              className={`${s_footer.btn} ${s_footer.pay_btn}`}
              onClick={closeCart}
            >
              <Trans i18nKey={"cart.returnToShop"} />
            </button>
          </>
        )}
      </div>
    </ModalOverlay>
  );
};

export default Cart;
