import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { cartStorage, getInitialCart } from "../../api/cartApi/cartStorage.ts";
import {
  addCartItem,
  getCart,
  getCartPreview,
  removeCartItem,
} from "../actions/cartActions.ts";
import { CartApiResponse, CartType } from "../../api/cartApi/types.ts";
import { AppRootStateType } from "../store.ts";

const normalizeCartResponse = (data: CartApiResponse): CartType => {
  const items = data.items.map((item) => ({
    data: item.landing ?? item.book!,
    item_type: item.item_type,
  }));

  return {
    items,
    quantity: items.length,
    current_discount: data.current_discount,
    next_discount: data.next_discount,
    total_amount: data.total_amount,
    total_amount_with_balance_discount: data.total_amount_with_balance_discount,
    total_new_amount: data.total_new_amount,
    total_old_amount: data.total_old_amount,
  };
};

const initialState: CartType = cartStorage.getCart() ?? getInitialCart();

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
          const normalized = normalizeCartResponse(action.payload.res.data);
          Object.assign(state, normalized);
          cartStorage.setCart(normalized);
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
          const normalized = normalizeCartResponse(action.payload.res.data);
          Object.assign(state, normalized);
          cartStorage.setCart(normalized);
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
          const normalized = normalizeCartResponse(action.payload.res.data);
          Object.assign(state, normalized);
          cartStorage.setCart(normalized);
        },
      );
    builder
      .addCase(getCartPreview.pending, (state) => {
        state.loading = true;
      })
      .addCase(
        getCartPreview.fulfilled,
        (state, action: PayloadAction<{ res: { data: CartApiResponse } }>) => {
          state.loading = false;
          const normalized = normalizeCartResponse(action.payload.res.data);
          Object.assign(state, normalized);
          cartStorage.setCart(normalized);
        },
      );
  },
});

export const selectIsInCart = (id: number) => (state: AppRootStateType) =>
  state.cart?.items.some((item) => item.data.id === id);

export const { clearCart, syncCartFromStorage } = cartSlice.actions;

export const cartReducer = cartSlice.reducer;
