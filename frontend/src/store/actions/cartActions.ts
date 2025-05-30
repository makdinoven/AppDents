import { createAppAsyncThunk } from "../createAppAsynkThunk.ts";
import { cartApi } from "../../api/cartApi/cartApi.ts";

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
  async (id: number, { rejectWithValue }) => {
    try {
      const res = await cartApi.addCartItem(id);
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
  async (id: number, { rejectWithValue }) => {
    try {
      const res = await cartApi.removeCartItem(id);
      if (res.data.error) {
        return rejectWithValue(res.data.error);
      }

      return { res };
    } catch (e: any) {
      return rejectWithValue(e.response.data);
    }
  },
);
