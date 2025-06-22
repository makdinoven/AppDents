import { userApi } from "../../api/userApi/userApi.ts";
import { createAppAsyncThunk } from "../createAppAsynkThunk.ts";
import { LoginType } from "../../api/userApi/types.ts";
import { LS_TOKEN_KEY } from "../../common/helpers/commonConstants.ts";

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

export const getCourses = createAppAsyncThunk(
  "user/getCourses",
  async (_, { rejectWithValue }) => {
    try {
      const res = await userApi.getCourses();

      if (res.data.error) {
        return rejectWithValue(res.data.error);
      }

      return { res };
    } catch (e: any) {
      return rejectWithValue(e.response?.data || "Unknown error");
    }
  },
);

export const logoutAsync = createAppAsyncThunk(
  "user/logoutAsync",
  async (_) => {
    localStorage.removeItem(LS_TOKEN_KEY);
    return;
  },
);


export const getMyReferrals = createAppAsyncThunk(
  "wallet/getMyReferrals",
  async (_, { rejectWithValue }) => {
    try {
      const res = await userApi.getMyReferrals();
      if (res.data.error) {
        return rejectWithValue(res.data.error);
      }

      return { res };
    } catch (e: any) {
      return rejectWithValue(e.response.data);
    }
  }
);

export const getMyTransactions = createAppAsyncThunk(
  "wallet/getMyTransactions",
  async (_, { rejectWithValue }) => {
    try {
      const res = await userApi.getMyTransactions();

      if (res.data.error) {
        return rejectWithValue(res.data.error);
      }

      return { res };
    } catch (e: any) {
      return rejectWithValue(e.response.data);
    }
  }
);
