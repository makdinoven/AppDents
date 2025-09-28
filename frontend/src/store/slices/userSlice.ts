import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import {
  getCourses,
  getMe,
  login,
  logoutAsync,
} from "../actions/userActions.ts";
import i18n from "i18next";
import {
  LS_LANGUAGE_KEY,
  LS_TOKEN_KEY,
} from "../../common/helpers/commonConstants.ts";

const savedLanguage = localStorage.getItem(LS_LANGUAGE_KEY) || "EN";

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
  loadingCourses: boolean;
  error: ErrorResponse | null;
  isLogged: boolean;
  language: string;
  balance: number | null;
  courses: [];
}

interface ErrorResponse {
  detail?: {
    error?: {
      translation_key?: string;
    };
  };
}

const initialState: UserState = {
  id: null,
  email: null,
  role: null,
  loading: false,
  loadingCourses: false,
  error: null,
  isLogged: false,
  balance: null,
  language: savedLanguage,
  courses: [],
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
    clearUserCourses: (state) => {
      state.courses = [];
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
            action.payload.res.data.access_token,
          );
        },
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
        },
      )
      .addCase(getMe.rejected, (state, action) => {
        state.error = action.payload as ErrorResponse;
        userSlice.caseReducers.logout(state);
        state.loading = false;
      })
      .addCase(getCourses.pending, (state) => {
        state.error = null;
        state.loadingCourses = true;
      })
      .addCase(
        getCourses.fulfilled,
        (state, action: PayloadAction<{ res: any }>) => {
          state.courses = action.payload.res.data;
          state.loadingCourses = false;
        },
      )
      .addCase(getCourses.rejected, (state, action) => {
        state.error = action.payload as ErrorResponse;
        state.loadingCourses = false;
      });
  },
});

export const { logout, setLanguage, clearUserCourses } = userSlice.actions;
export const userReducer = userSlice.reducer;
