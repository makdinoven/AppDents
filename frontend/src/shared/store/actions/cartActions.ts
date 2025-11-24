import { createAppAsyncThunk } from "../createAppAsynkThunk.ts";
import { cartApi } from "../../api/cartApi/cartApi.ts";
import { CartItemKind } from "../../api/cartApi/types.ts";
import { cartStorage } from "../../api/cartApi/cartStorage.ts";

export const getCart = createAppAsyncThunk(
  "cart/get",
  async (_, { rejectWithValue }) => {
    try {
      const res = await cartApi.getCart();
      if (res.data.error) {
        return rejectWithValue(res.data.error);
      }

      return { res };
    } catch (e: any) {
      return rejectWithValue(e.response.data);
    }
  },
);

export const addCartItem = createAppAsyncThunk(
  "cart/addItem",
  async (data: { id: number; type: CartItemKind }, { rejectWithValue }) => {
    try {
      let res;
      if (data.type === "BOOK") {
        res = await cartApi.addCartItemBook(data.id);
      } else {
        res = await cartApi.addCartItemCourse(data.id);
      }

      if (res?.data.error) {
        return rejectWithValue(res.data.error);
      }

      return { res };
    } catch (e: any) {
      return rejectWithValue(e.response.data);
    }
  },
);

export const removeCartItem = createAppAsyncThunk(
  "cart/removeItem",
  async (data: { id: number; type: CartItemKind }, { rejectWithValue }) => {
    try {
      let res;
      if (data.type === "BOOK") {
        res = await cartApi.removeCartItemBook(data.id);
      } else {
        res = await cartApi.removeCartItemCourse(data.id);
      }

      if (res.data.error) {
        return rejectWithValue(res.data.error);
      }

      return { res };
    } catch (e: any) {
      return rejectWithValue(e.response.data);
    }
  },
);

export const getCartPreview = createAppAsyncThunk(
  "cart/getCartPreview",
  async (_, { rejectWithValue }) => {
    try {
      const cartLandingIds = cartStorage.getLandingIds();
      const res = await cartApi.previewCart(cartLandingIds!);
      if (res.data.error) {
        return rejectWithValue(res.data.error);
      }

      return { res };
    } catch (e: any) {
      return rejectWithValue(e.response.data);
    }
  },
);
