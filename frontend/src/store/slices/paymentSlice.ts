import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { PAGE_SOURCES } from "../../common/helpers/commonConstants.ts";
import { getLandingDataForPayment } from "../actions/paymentActions.ts";

export interface PaymentDataType {
  region?: string;
  landingIds?: number[];
  fromAd: boolean;
  priceCents: number;
  newPrice: number;
  oldPrice: number;
  courseIds: number[];
  source?: (typeof PAGE_SOURCES)[keyof typeof PAGE_SOURCES];
  courses: {
    name: string;
    newPrice: number;
    oldPrice: number;
    lessonsCount: string;
    img: string;
  }[];
}

interface State {
  data: PaymentDataType | null;
}

const initialState: State = {
  data: null,
};

const paymentSlice = createSlice({
  name: "payment",
  initialState,
  reducers: {
    setPaymentData(state, action: PayloadAction<PaymentDataType>) {
      state.data = action.payload;
    },
  },

  extraReducers: (builder) => {
    builder.addCase(
      getLandingDataForPayment.fulfilled,
      (state, action: PayloadAction<{ res: any }>) => {
        const {
          id,
          course_ids,
          new_price,
          old_price,
          language,
          landing_name,
          lessons_count,
          preview_photo,
        } = action.payload.res.data;

        state.data = {
          landingIds: [id],
          courseIds: course_ids,
          priceCents: new_price * 100,
          newPrice: new_price,
          oldPrice: old_price,
          region: language,
          fromAd: false,
          courses: [
            {
              name: landing_name,
              newPrice: new_price,
              oldPrice: old_price,
              lessonsCount: lessons_count,
              img: preview_photo,
            },
          ],
        };
      },
    );
  },
});

export const { setPaymentData } = paymentSlice.actions;
export const paymentReducer = paymentSlice.reducer;
