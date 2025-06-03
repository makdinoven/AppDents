import s from "./AddToCartButton.module.scss";
import { CartIcon, CheckMarkIcon } from "../../../assets/logos/index";
import LoaderOverlay from "../LoaderOverlay/LoaderOverlay.tsx";
import { Trans } from "react-i18next";
import {
  addCartItem,
  removeCartItem,
} from "../../../store/actions/cartActions.ts";
import { cartStorage } from "../../../api/cartApi/cartStorage.ts";
import {
  selectIsInCart,
  syncCartFromStorage,
} from "../../../store/slices/cartSlice.ts";
import { useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { AppDispatchType, AppRootStateType } from "../../../store/store.ts";

const AddToCartButton = ({
  item,
  variant = "default",
  hasText,
  className,
}: {
  item: {
    landing: {
      id: number;
      landing_name: string;
      authors: any[];
      page_name: string;
      old_price: number;
      new_price: number;
      preview_photo: string;
      course_ids: number[];
    };
  };
  hasText?: boolean;
  className?: string;
  variant?: "default" | "primary";
}) => {
  const id = item?.landing?.id;
  const isInCart = useSelector(selectIsInCart(id));
  const [loading, setLoading] = useState(false);
  const dispatch = useDispatch<AppDispatchType>();
  const isLogged = useSelector(
    (state: AppRootStateType) => state.user.isLogged,
  );

  const toggleCardInCart = async () => {
    setLoading(true);
    if (!isInCart) {
      if (isLogged) {
        await dispatch(addCartItem(id));
      } else {
        cartStorage.addItem(item);
        dispatch(syncCartFromStorage());
      }
    } else {
      if (isLogged) {
        await dispatch(removeCartItem(id));
      } else {
        cartStorage.removeItem(id);
        dispatch(syncCartFromStorage());
      }
    }
    setLoading(false);
  };

  return (
    <button
      onClick={(e) => {
        e.preventDefault();
        e.stopPropagation();
        toggleCardInCart();
      }}
      className={`${className ? className : ""} ${s.btn} ${isInCart ? s.active : ""} ${s[variant]}`}
    >
      {loading && <LoaderOverlay inset={2} />}
      {!isInCart ? (
        <>
          {hasText && <Trans i18nKey="cart.addToCart" />}
          <CartIcon />
        </>
      ) : (
        <>
          <Trans i18nKey={"cart.inCart"} />
          <CheckMarkIcon />
        </>
      )}
    </button>
  );
};

export default AddToCartButton;
