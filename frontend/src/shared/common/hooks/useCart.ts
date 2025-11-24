import { useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { AppDispatchType, AppRootStateType } from "../../store/store.ts";
import {
  addCartItem,
  removeCartItem,
} from "../../store/actions/cartActions.ts";
import {
  selectIsInCart,
  syncCartFromStorage,
} from "../../store/slices/cartSlice.ts";
import { cartStorage } from "../../api/cartApi/cartStorage.ts";
import {
  CartItemBookType,
  CartItemCourseType,
  CartItemKind,
} from "../../api/cartApi/types.ts";

export const useCart = (
  item: CartItemCourseType | CartItemBookType,
  type: CartItemKind,
) => {
  const id = item.id;
  const dispatch = useDispatch<AppDispatchType>();
  const isInCart = useSelector(selectIsInCart(id));
  const isLogged = useSelector(
    (state: AppRootStateType) => state.user.isLogged,
  );
  const [loading, setLoading] = useState(false);

  const toggleCartItem = async () => {
    setLoading(true);

    if (!isInCart) {
      if (isLogged) {
        await dispatch(addCartItem({ id, type }));
      } else {
        cartStorage.addItem({ item_type: type, data: item });
        dispatch(syncCartFromStorage());
      }
    } else {
      if (isLogged) {
        await dispatch(removeCartItem({ id, type }));
      } else {
        cartStorage.removeItem(type, id);
        dispatch(syncCartFromStorage());
      }
    }

    setLoading(false);
  };

  return {
    isInCart,
    cartItemLoading: loading,
    toggleCartItem,
  };
};
