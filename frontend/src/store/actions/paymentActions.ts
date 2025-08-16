import { createAppAsyncThunk } from "../createAppAsynkThunk.ts";
import { mainApi } from "../../api/mainApi/mainApi.ts";

export const getLandingDataForPayment = createAppAsyncThunk(
  "payment/getLandingData",
  async (slug: string, { rejectWithValue }) => {
    try {
      const res = await mainApi.getLanding(slug);

      if (res.data.error) {
        return rejectWithValue(res.data.error);
      }

      return { res };
    } catch (e: any) {
      return rejectWithValue(e.response?.data || "Unknown error");
    }
  },
);
