import { userApi } from "../../api/userApi/userApi.ts";
import { createAppAsyncThunk } from "../createAppAsynkThunk.ts";
import { LoginType } from "../../api/userApi/types.ts";

export const login = createAppAsyncThunk(
  "user/login",
  async (data: LoginType, { rejectWithValue }) => {
    try {
      const res = await userApi.login(data);
      if (res.data.error) {
        return rejectWithValue(res.data.error);
      }

      return { res };
    } catch (e: any) {
      return rejectWithValue(e.response.data);
    }
  },
);

export const getMe = createAppAsyncThunk(
  "user/getMe",
  async (_, { rejectWithValue }) => {
    try {
      const res = await userApi.getMe();

      if (res.data.error) {
        return rejectWithValue(res.data.error);
      }

      return { res };
    } catch (e: any) {
      return rejectWithValue(e.response?.data || "Unknown error");
    }
  },
);
