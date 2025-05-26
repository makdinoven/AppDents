import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { CartType } from "../../api/cartApi/types.ts";
import { cartStorage } from "../../api/cartApi/cartStorage.ts";
import {
  addCartItem,
  getCart,
  removeCartItem,
} from "../actions/cartActions.ts";
import { AppRootStateType } from "../store.ts";

const initialState: CartType = cartStorage.getCart() || {
  items: [],
  loading: false,
  quantity: 0,
};

const cartSlice = createSlice({
  name: "cart",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(getCart.pending, (state) => {
        state.loading = true;
      })
      .addCase(
        getCart.fulfilled,
        (state, action: PayloadAction<{ res: any }>) => {
          state.loading = false;
          state.items = action.payload.res.data.items; // TODO CHANGE TO REAL RES DATA CONF
          state.quantity = state.items.length;
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
          state.items = action.payload.res.data.items; // TODO CHANGE TO REAL RES DATA CONF
          state.quantity = state.items.length;
          cartStorage.setCart(state);
        },
      );
    builder
      .addCase(removeCartItem.pending, (state) => {
        state.loading = true;
      })
      .addCase(
        removeCartItem.fulfilled,
        (state, action: PayloadAction<{ res: any }>) => {
          state.loading = false;
          state.items = action.payload.res.data.items; // TODO CHANGE TO REAL RES DATA CONF
          state.quantity = state.items.length;
          cartStorage.setCart(state);
        },
      );
  },
});

export const selectIsInCart = (id: number) => (state: AppRootStateType) =>
  state.cart.items.some((item) => item.id === id);

export const cartReducer = cartSlice.reducer;
