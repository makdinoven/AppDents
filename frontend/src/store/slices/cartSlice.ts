import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { cartStorage, getInitialCart } from "../../api/cartApi/cartStorage.ts";
import {
  addCartItem,
  getCart,
  removeCartItem,
} from "../actions/cartActions.ts";
import { CartApiResponse, CartTypeExtended } from "../../api/cartApi/types.ts";
import { AppRootStateType } from "../store.ts";

const initialState: CartTypeExtended =
  cartStorage.getCart() ?? getInitialCart();

const cartSlice = createSlice({
  name: "cart",
  initialState,
  reducers: {
    clearCart: (state) => {
      state.items = [];
      state.quantity = 0;
      state.current_discount = 0;
      state.next_discount = 0;
      state.total_amount = 0;
      state.total_amount_with_balance_discount = 0;
      state.total_new_amount = 0;
      state.total_old_amount = 0;
      cartStorage.setCart(state);
    },
    syncCartFromStorage: (state) => {
      const storedCart = cartStorage.getCart();
      if (storedCart) {
        Object.assign(state, storedCart);
      }
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(getCart.pending, (state) => {
        state.loading = true;
      })
      .addCase(
        getCart.fulfilled,
        (state, action: PayloadAction<{ res: { data: CartApiResponse } }>) => {
          state.loading = false;
          Object.assign(state, {
            ...action.payload.res.data,
            quantity: action.payload.res.data.items.length,
          });
          cartStorage.setCart(state);
        },
      );
    builder
      .addCase(addCartItem.pending, (state) => {
        state.loading = true;
      })
      .addCase(
        addCartItem.fulfilled,
        (state, action: PayloadAction<{ res: any }>) => {
          state.loading = false;
          Object.assign(state, {
            ...action.payload.res.data,
            quantity: action.payload.res.data.items.length,
          });
          cartStorage.setCart(state);
        },
      );
    builder
      .addCase(removeCartItem.pending, (state) => {
        state.loading = true;
      })
      .addCase(
        removeCartItem.fulfilled,
        (state, action: PayloadAction<{ res: { data: CartApiResponse } }>) => {
          state.loading = false;
          Object.assign(state, {
            ...action.payload.res.data,
            quantity: action.payload.res.data.items.length,
          });
          cartStorage.setCart(state);
        },
      );
  },
});

export const selectIsInCart = (id: number) => (state: AppRootStateType) =>
  state.cart.items.some((item) => item.landing.id === id);

export const { clearCart, syncCartFromStorage } = cartSlice.actions;

export const cartReducer = cartSlice.reducer;
