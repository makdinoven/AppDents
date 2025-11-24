import { createAppAsyncThunk } from "../createAppAsynkThunk.ts";
import { mainApi } from "../../api/mainApi/mainApi.ts";
import { PaymentDataModeType } from "../../common/hooks/usePaymentPageHandler.ts";

export const getLandingDataForPayment = createAppAsyncThunk(
  "payment/getCourseLandingData",
  async (
    { slug, mode }: { slug: string; mode: PaymentDataModeType },
    { rejectWithValue },
  ) => {
    try {
      let res;

      switch (mode) {
        case "COURSES":
          res = await mainApi.getLanding(slug);
          break;
        case "BOOKS":
          res = await mainApi.getBookLanding(slug);
          break;
        case "BOTH": {
          const [bookRes, landingRes] = await Promise.all([
            mainApi.getBookLanding(slug),
            mainApi.getLanding(slug),
          ]);
          res = { book: bookRes, landing: landingRes };
          break;
        }
      }

      if (res.data.error) {
        return rejectWithValue(res.data.error);
      }

      return { res, mode };
    } catch (e: any) {
      return rejectWithValue(e.response?.data || "Unknown error");
    }
  },
);
