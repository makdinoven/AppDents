import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { getCourses, getMe, login } from "../actions/userActions.ts";
import i18n from "i18next";

interface UserState {
  email: string | null;
  role: string | null;
  loading: boolean;
  error: ErrorResponse | null;
  isLogged: boolean;
  language: string;
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
  email: null,
  role: null,
  loading: false,
  error: null,
  isLogged: false,
  language: "EN",
  courses: [],
};

const userSlice = createSlice({
  name: "user",
  initialState,
  reducers: {
    logout: (state) => {
      if (
        window.location.pathname.startsWith("/admin") ||
        window.location.pathname.startsWith("/profile")
      ) {
        window.location.href = "/";
      }
      state.email = null;
      state.role = null;
      state.loading = false;
      state.error = null;
      state.isLogged = false;
      localStorage.removeItem("access_token");
    },
    setLanguage: (state, action: PayloadAction<string>) => {
      const newLanguage = action.payload;
      state.language = newLanguage;
      localStorage.setItem("DENTS_LANGUAGE", newLanguage);
      i18n.changeLanguage(newLanguage);
    },
  },
  extraReducers: (builder) => {
    builder
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
            "access_token",
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
          state.email = action.payload.res.data.email;
          state.role = action.payload.res.data.role;
        },
      )
      .addCase(getMe.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as ErrorResponse;
        userSlice.caseReducers.logout(state);
      })
      .addCase(getCourses.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(
        getCourses.fulfilled,
        (state, action: PayloadAction<{ res: any }>) => {
          state.courses = action.payload.res.data;
          state.loading = false;
        },
      );
  },
});

export const { logout, setLanguage } = userSlice.actions;
export const userReducer = userSlice.reducer;
