import s from "./Cart.module.scss";
import s_footer from "./CartFooter/CartFooter.module.scss";
import { useNavigate } from "react-router-dom";
import { useEffect, useRef, useState } from "react";
import { Path } from "../../routes/routes.ts";
import { Trans } from "react-i18next";
import CartItem from "./CartItem/CartItem.tsx";
import { useDispatch, useSelector } from "react-redux";
import { AppDispatchType, AppRootStateType } from "../../store/store.ts";
import {
  getCart,
  getCartPreview,
  removeCartItem,
} from "../../store/actions/cartActions.ts";
import { CartIcon, CheckMark } from "../../assets/icons/index.ts";
import { mainApi } from "../../api/mainApi/mainApi.ts";
import CartFooter from "./CartFooter/CartFooter.tsx";
import { cartStorage } from "../../api/cartApi/cartStorage.ts";
import { syncCartFromStorage } from "../../store/slices/cartSlice.ts";
import {
  BASE_URL,
  REF_CODE_LS_KEY,
  REF_CODE_PARAM,
} from "../../common/helpers/commonConstants.ts";
import {
  CartItemBookType,
  CartItemCourseType,
  CartItemKind,
} from "../../api/cartApi/types.ts";
import { t } from "i18next";
import { Alert } from "../../components/ui/Alert/Alert.tsx";
import ModalOverlay from "../../components/Modals/ModalOverlay/ModalOverlay.tsx";
import ModalCloseButton from "../../components/ui/ModalCloseButton/ModalCloseButton.tsx";
import useOutsideClick from "../../common/hooks/useOutsideClick.ts";
import { clearUserCourses } from "../../store/slices/userSlice.ts";

const Cart = () => {
  const navigate = useNavigate();
  const closeModalRef = useRef<() => void>(null);
  const modalRef = useRef<HTMLDivElement | null>(null);
  const dispatch = useDispatch<AppDispatchType>();
  const { isLogged, email, language } = useSelector(
    (state: AppRootStateType) => state.user,
  );
  const [loading, setLoading] = useState(false);
  const balance = useSelector((state: AppRootStateType) => state.user.balance);
  const {
    items,
    quantity,
    loading: cartLoading,
    current_discount,
    next_discount,
    total_amount,
    total_amount_with_balance_discount,
    total_new_amount,
    total_old_amount,
  } = useSelector((state: AppRootStateType) => state.cart);
  const [isBalanceUsed, setIsBalanceUsed] = useState<boolean>(false);
  const isCartEmpty = quantity === 0;
  useOutsideClick(modalRef, () => {
    closeCart();
  });

  useEffect(() => {
    if (!isLogged && quantity > 0) {
      dispatch(getCartPreview());
    }
  }, [isLogged, quantity]);

  const handlePay = async (form: any) => {
    const rcCode = localStorage.getItem(REF_CODE_LS_KEY);
    const courseItems = items.filter(
      (item): item is { data: CartItemCourseType; item_type: "LANDING" } =>
        item.item_type === "LANDING",
    );
    const bookItems = items.filter(
      (item): item is { data: CartItemBookType; item_type: "BOOK" } =>
        item.item_type === "BOOK",
    );

    setLoading(true);
    const dataToSend = {
      landing_ids: courseItems.map((item) => item.data.id),
      book_landing_ids: bookItems.map((item) => item.data.id),
      course_ids: courseItems.map((item) => item.data.course_ids).flat(),
      book_ids: bookItems.map((item) => item.data.book_ids).flat(),
      region: language,
      price_cents: (total_amount * 100).toFixed(0),
      user_email: isLogged ? email : form.email,
      success_url: `${BASE_URL}${Path.successPayment}`,
      use_balance: isBalanceUsed,
      source: "CART",
      cancel_url:
        !isLogged && rcCode
          ? `${BASE_URL}/${Path.cart}?${REF_CODE_PARAM}=${rcCode}`
          : `${BASE_URL}/${Path.cart}`,
    };
    try {
      const res = await mainApi.buyCourse(dataToSend, isLogged);
      localStorage.removeItem(REF_CODE_LS_KEY);
      const checkoutUrl = res.data.checkout_url;
      const balanceLeft = res.data.balance_left;
      setLoading(false);

      if (checkoutUrl) {
        const newTab = window.open(checkoutUrl, "_blank");

        if (!newTab || newTab.closed || typeof newTab.closed === "undefined") {
          window.location.href = checkoutUrl;
        }
      }

      if (balanceLeft) {
        dispatch(clearUserCourses());
        Alert(
          t("successPaymentWithBalance", { balance: balanceLeft }),
          <CheckMark />,
        );
        navigate(Path.profile);
      }

      dispatch(getCart());
    } catch (error) {
      setLoading(false);
      console.log(error);
    }
  };

  const handleDeleteCartItem = async (id: number, type: CartItemKind) => {
    if (isLogged) {
      setLoading(true);
      await dispatch(removeCartItem({ id, type }));
      setLoading(false);
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
              cartPreviewLoading={!isLogged && cartLoading}
              loading={loading}
              quantity={quantity}
              total_new_amount={total_new_amount}
              total_amount_with_balance_discount={
                total_amount_with_balance_discount
              }
              total_amount={total_amount}
              balance={balance!}
              setIsBalanceUsed={setIsBalanceUsed}
              isBalanceUsed={isBalanceUsed}
              total_old_amount={total_old_amount}
              isLogged={isLogged}
              next_discount={next_discount}
              current_discount={current_discount}
              handlePay={(form: any) => handlePay(form)}
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
