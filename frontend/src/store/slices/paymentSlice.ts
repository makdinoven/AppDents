import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { PAGE_SOURCES } from "../../common/helpers/commonConstants.ts";
import { getLandingDataForPayment } from "../actions/paymentActions.ts";

export interface PaymentDataType {
  isFree?: boolean; // TODO УДАЛИТЬ
  isWebinar?: boolean; // TODO УДАЛИТЬ
  isOffer?: boolean; // TODO УДАЛИТЬ
  region?: string;
  landingIds?: number[];
  slug?: string;
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
  isPaymentModalOpen: boolean;
}

const initialState: State = {
  data: null,
  isPaymentModalOpen: false,
};

const paymentSlice = createSlice({
  name: "payment",
  initialState,
  reducers: {
    setPaymentData(state, action: PayloadAction<PaymentDataType>) {
      state.data = action.payload;
    },
    openPaymentModal(state) {
      state.isPaymentModalOpen = true;
    },
    closePaymentModal(state) {
      state.isPaymentModalOpen = false;
    },
    setIsFree(state, action: PayloadAction<boolean>) {
      if (state.data) state.data.isFree = action.payload;
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
          page_name,
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
          slug: page_name,
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

export const {
  setPaymentData,
  openPaymentModal,
  closePaymentModal,
  setIsFree,
} = paymentSlice.actions;
export const paymentReducer = paymentSlice.reducer;
