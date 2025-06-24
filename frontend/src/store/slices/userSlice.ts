import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import {
  getCourses,
  getMe,
  login,
  logoutAsync,
  getMyReferrals,
  getMyTransactions,
} from "../actions/userActions.ts";
import i18n from "i18next";
import {
  LS_LANGUAGE_KEY,
  LS_TOKEN_KEY,
} from "../../common/helpers/commonConstants.ts";
import { TransactionType } from "../../common/types/commonTypes.ts";
import { AxiosResponse } from "axios";

const savedLanguage = localStorage.getItem(LS_LANGUAGE_KEY) || "EN";

export type Referral = {
  user_id: number;
  email: string;
  total_paid: number;
  total_cashback: number;
  created_at?: string;
};

type TransactionResponse = {
  id: number;
  amount: number;
  type: "REFERRAL_CASHBACK" | "INTERNAL_PURCHASE" | "ADMIN_ADJUST";
  meta:
    | {
        percent: 50;
        from_user: number;
        purchase_id: number;
      }
    | {
        reason: string;
        courses: number[];
      }
    | {
        reason: string;
      };
  created_at: string;
};

interface ErrorResponse {
  detail?: {
    error?: {
      translation_key?: string;
    };
  };
}

interface UserState {
  email: string | null;
  id: number | null;
  role: string | null;
  loading: boolean;
  error: ErrorResponse | null;
  isLogged: boolean;
  language: string;
  balance: number | null;
  courses: [];
  referrals: Referral[];
  transactions: TransactionType[];
  loadingStats: boolean;
}

interface ErrorResponse {
  detail?: {
    error?: {
      translation_key?: string;
    };
  };
}

const getCamelCaseString = (string: string): string => {
  return string.split("_").reduce((result, value, index) => {
    return index === 0
      ? result + value
      : result + value[0].toUpperCase() + value.slice(1);
  }, "");
};
const initialState: UserState = {
  id: null,
  email: null,
  role: null,
  loading: false,
  error: null,
  isLogged: false,
  balance: null,
  language: savedLanguage,
  courses: [],
  referrals: [],
  transactions: [],
  loadingStats: false,
};

const userSlice = createSlice({
  name: "user",
  initialState,
  reducers: {
    logout: (state) => {
      localStorage.removeItem(LS_TOKEN_KEY);
      state.email = null;
      state.role = null;
      state.loading = false;
      state.error = null;
      state.isLogged = false;
      state.balance = null;
      state.courses = [];
    },
    setLanguage: (state, action: PayloadAction<string>) => {
      const newLanguage = action.payload;
      state.language = newLanguage;
      localStorage.setItem(LS_LANGUAGE_KEY, newLanguage);
      i18n.changeLanguage(newLanguage);
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(logoutAsync.pending, (state) => {
        state.loading = true;
      })
      .addCase(logoutAsync.fulfilled, (state) => {
        state.email = null;
        state.role = null;
        state.loading = false;
        state.error = null;
        state.isLogged = false;
        state.balance = null;
      })
      .addCase(login.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(
        login.fulfilled,
        (state, action: PayloadAction<{ res: any }>) => {
          state.loading = false;
          state.isLogged = true;
          localStorage.setItem(
            LS_TOKEN_KEY,
            action.payload.res.data.access_token
          );
        }
      )
      .addCase(login.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as ErrorResponse;
      })

      .addCase(getMe.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(
        getMe.fulfilled,
        (state, action: PayloadAction<{ res: any }>) => {
          state.loading = false;
          state.isLogged = true;
          state.balance = action.payload.res.data.balance;
          state.email = action.payload.res.data.email;
          state.role = action.payload.res.data.role;
          state.id = action.payload.res.data.id;
        }
      )
      .addCase(getMe.rejected, (state, action) => {
        state.error = action.payload as ErrorResponse;
        userSlice.caseReducers.logout(state);
        state.loading = false;
      })
      .addCase(getCourses.pending, (state) => {
        state.error = null;
      })
      .addCase(
        getCourses.fulfilled,
        (state, action: PayloadAction<{ res: any }>) => {
          state.courses = action.payload.res.data;
        }
      )
      .addCase(
        getMyReferrals.fulfilled,
        (state, action: PayloadAction<{ res: AxiosResponse<Referral[]> }>) => {
          state.loadingStats = false;
          state.referrals = action.payload.res.data;
        }
      )
      .addCase(getMyReferrals.pending, (state) => {
        state.loadingStats = true;
        state.error = null;
      })
      .addCase(getMyReferrals.rejected, (state, action) => {
        state.error = action.payload as ErrorResponse;
        state.loadingStats = false;
      })
      .addCase(getMyTransactions.pending, (state) => {
        state.loadingStats = true;
        state.error = null;
      })
      .addCase(
        getMyTransactions.fulfilled,
        (
          state,
          action: PayloadAction<{
            res: AxiosResponse<TransactionResponse[]>;
          }>
        ) => {
          state.loadingStats = false;
          state.transactions = action.payload.res.data.map((transaction) => {
            const baseFields = {
              amount: transaction.amount,
              type: transaction.type,
              created_at: transaction.created_at,
            };

            switch (transaction.type) {
              case "REFERRAL_CASHBACK":
                return {
                  ...baseFields,
                  type: "referralCashback",
                  from_user:
                    "from_user" in transaction.meta
                      ? transaction.meta.from_user
                      : null,
                } as const;

              case "INTERNAL_PURCHASE":
                return {
                  ...baseFields,
                  type: "internalPurchase",
                  reason:
                    "reason" in transaction.meta
                      ? getCamelCaseString(transaction.meta.reason)
                      : null,
                  courses:
                    "courses" in transaction.meta
                      ? transaction.meta.courses
                      : [],
                } as const;

              case "ADMIN_ADJUST":
                return {
                  ...baseFields,
                  type: "adminAdjust",
                  reason:
                    "reason" in transaction.meta
                      ? transaction.meta.reason
                      : null,
                } as const;
            }
          });
        }
      )
      .addCase(getMyTransactions.rejected, (state, action) => {
        state.error = action.payload as ErrorResponse;
        state.loadingStats = false;
      });
  },
});

export const { logout, setLanguage } = userSlice.actions;
export const userReducer = userSlice.reducer;
