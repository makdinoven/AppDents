import { createSlice, PayloadAction } from "@reduxjs/toolkit";

export interface PaymentDataType {
  isFree: boolean; // TODO УДАЛИТЬ
  isWebinar: boolean; // TODO УДАЛИТЬ
  fromAd: boolean;
  priceCents: number;
  newPrice: number;
  oldPrice: number;
  landingIds?: number[];
  slug: string;
  courseIds: number[];
  region: string;
  successUrl: string;
  cancelUrl: string;
  source: string;
  courses: {
    name: string;
    newPrice: number;
    oldPrice: number;
    lessonsCount: string;
  }[];
}

interface State {
  data: PaymentDataType | null;
  backgroundUrl: string | null;
}

const initialState: State = {
  data: null,
  backgroundUrl: null,
};

const paymentSlice = createSlice({
  name: "payment",
  initialState,
  reducers: {
    setPaymentData(
      state,
      action: PayloadAction<{ data: PaymentDataType; backgroundUrl?: string }>,
    ) {
      state.data = action.payload.data;
      if (action.payload.backgroundUrl) {
        state.backgroundUrl = action.payload.backgroundUrl;
      }
    },
    setBackgroundUrl(state, action: PayloadAction<{ url: string }>) {
      state.backgroundUrl = action.payload.url;
    },
    clearPaymentData(state) {
      state.data = null;
      state.backgroundUrl = null;
    },
  },
});

export const { setPaymentData, setBackgroundUrl, clearPaymentData } =
  paymentSlice.actions;
export const paymentReducer = paymentSlice.reducer;
