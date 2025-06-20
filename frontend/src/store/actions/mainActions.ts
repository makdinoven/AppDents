import { createAppAsyncThunk } from "../createAppAsynkThunk.ts";
import { mainApi } from "../../api/mainApi/mainApi.ts";

export const getTags = createAppAsyncThunk(
  "main/getTags",
  async (_, { rejectWithValue }) => {
    try {
      const res = await mainApi.getTags();

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
  "main/getCourses",
  async (params: any, { rejectWithValue }) => {
    try {
      const res = await mainApi.getCourseCards(params);

      if (res.data.error) {
        return rejectWithValue(res.data.error);
      }

      return { res };
    } catch (e: any) {
      return rejectWithValue(e.response?.data || "Unknown error");
    }
  },
);

export const getCoursesRecommend = createAppAsyncThunk(
  "main/getCoursesRecommend",
  async (params: any, { rejectWithValue }) => {
    try {
      const res = await mainApi.getCourseCardsRecommend(params);

      if (res.data.error) {
        return rejectWithValue(res.data.error);
      }

      return { res };
    } catch (e: any) {
      return rejectWithValue(e.response?.data || "Unknown error");
    }
  },
);
