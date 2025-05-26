import { createAppAsyncThunk } from "../createAppAsynkThunk.ts";
import { cartApi } from "../../api/cartApi/cartApi.ts";

export const getCart = createAppAsyncThunk(
  "cart/get",
  async (data: any, { rejectWithValue }) => {
    try {
      const res = await cartApi.getCart(data);
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
  async (data: any, { rejectWithValue }) => {
    try {
      const res = await cartApi.addCartItem(data);
      if (res.data.error) {
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
  async (data: any, { rejectWithValue }) => {
    try {
      const res = await cartApi.removeCartItem(data);
      if (res.data.error) {
        return rejectWithValue(res.data.error);
      }

      return { res };
    } catch (e: any) {
      return rejectWithValue(e.response.data);
    }
  },
);
