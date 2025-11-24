import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { PAGE_SOURCES } from "../../common/helpers/commonConstants.ts";
import { CartItemKind, CartItemType } from "../../api/cartApi/types.ts";
import { LanguagesType } from "../../components/ui/LangLogo/LangLogo.tsx";
import { getLandingDataForPayment } from "../actions/paymentActions.ts";
import { PaymentDataModeType } from "../../common/hooks/usePaymentPageHandler.ts";

export interface PaymentApiPayload {
  course_ids: number[];
  book_ids: number[];
  book_landing_ids: number[];
  landing_ids: number[];
  price_cents: number;
  region: LanguagesType;
  user_email: string;
  success_url: string;
  cancel_url: string;
  fbp?: string;
  fbc?: string;
  use_balance: boolean;
  transfer_cart: boolean;
  cart_landing_ids: number[];
  cart_book_landing_ids: number[];
  ref_code?: string;
  source: (typeof PAGE_SOURCES)[keyof typeof PAGE_SOURCES];
  from_ad: boolean;
}

export interface PaymentHookDataPayload {
  new_price?: number;
  old_price?: number;
  course_ids: number[];
  book_ids: number[];
  book_landing_ids: number[];
  landing_ids: number[];
  price_cents: number;
  source?: (typeof PAGE_SOURCES)[keyof typeof PAGE_SOURCES];
  from_ad: boolean;
  region?: LanguagesType;
}

export interface PaymentRenderData {
  new_price: number;
  old_price: number;
  items: CartItemType[];
}

interface State {
  render: PaymentRenderData | null;
  data: PaymentHookDataPayload | null;
}

const initialState: State = {
  data: null,
  render: null,
};

const paymentSlice = createSlice({
  name: "payment",
  initialState,
  reducers: {
    setPaymentData(state, action: PayloadAction<State>) {
      state.data = action.payload.data;
      state.render = action.payload.render;
    },
  },

  extraReducers: (builder) => {
    builder.addCase(
      getLandingDataForPayment.fulfilled,
      (
        state,
        action: PayloadAction<{ res: any; mode: PaymentDataModeType }>,
      ) => {
        switch (action.payload.mode) {
          case "COURSES": {
            const {
              course_ids,
              id,
              new_price,
              old_price,
              language,
              authors,
              landing_name,
              page_name,
              lessons_count,
              preview_photo,
            } = action.payload.res.data;

            state.data = {
              course_ids,
              landing_ids: [id],
              book_ids: [],
              book_landing_ids: [],
              price_cents: new_price * 100,
              new_price,
              old_price,
              from_ad: false,
              region: language as LanguagesType,
            };

            state.render = {
              new_price: new_price,
              old_price: old_price,
              items: [
                {
                  item_type: "LANDING" as CartItemKind,
                  data: {
                    id: course_ids[0],
                    authors: authors,
                    landing_name,
                    page_name,
                    new_price,
                    old_price,
                    course_ids,
                    lessons_count,
                    preview_photo,
                  },
                },
              ],
            };
            break;
          }
          case "BOOKS": {
            const {
              book_ids,
              id,
              new_price,
              old_price,
              language,
              authors,
              landing_name,
              page_name,
              preview_photo,
            } = action.payload.res.data;

            state.data = {
              book_ids,
              landing_ids: [],
              course_ids: [],
              book_landing_ids: [id],
              price_cents: new_price * 100,
              new_price,
              old_price,
              from_ad: false,
              region: language as LanguagesType,
            };

            state.render = {
              new_price: new_price,
              old_price: old_price,
              items: [
                {
                  item_type: "BOOK" as CartItemKind,
                  data: {
                    id: id,
                    authors: authors,
                    landing_name,
                    page_name,
                    new_price,
                    old_price,
                    book_ids,
                    preview_photo,
                  },
                },
              ],
            };
            break;
          }
          case "BOTH": {
            break;
          }
        }
      },
    );
  },
});

export const { setPaymentData } = paymentSlice.actions;
export const paymentReducer = paymentSlice.reducer;
