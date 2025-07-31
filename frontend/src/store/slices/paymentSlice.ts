import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { PAGE_SOURCES } from "../../common/helpers/commonConstants.ts";

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
    clearPaymentData(state) {
      state.data = null;
    },
  },
});

export const {
  setPaymentData,
  openPaymentModal,
  closePaymentModal,
  clearPaymentData,
} = paymentSlice.actions;
export const paymentReducer = paymentSlice.reducer;
