import { createAppAsyncThunk } from "../createAppAsynkThunk.ts";
import { adminApi } from "../../api/adminApi/adminApi.ts";

export const getCourses = createAppAsyncThunk(
  "admin/getCourses",
  async (_, { rejectWithValue }) => {
    try {
      const res = await adminApi.getCoursesList();
      if (res.data.error) {
        return rejectWithValue(res.data.error);
      }

      return { res };
    } catch (e: any) {
      return rejectWithValue(e.response.data);
    }
  },
);

export const createCourse = createAppAsyncThunk(
  "admin/createCourse",
  async (_, { rejectWithValue }) => {
    try {
      const res = await adminApi.createCourse();
      if (res.data.error) {
        return rejectWithValue(res.data.error);
      }

      return { res };
    } catch (e: any) {
      return rejectWithValue(e.response.data);
    }
  },
);
