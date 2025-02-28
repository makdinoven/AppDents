import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { getMe, login } from "../actions/userActions.ts";

interface UserState {
  email: string | null;
  role: string | null;
  loading: boolean;
  error: ErrorResponse | null;
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
};

const userSlice = createSlice({
  name: "user",
  initialState,
  reducers: {
    logout: (state) => {
      state.email = null;
      state.role = null;
      state.loading = false;
      state.error = null;
      localStorage.removeItem("access_token");
      if (
        window.location.pathname.startsWith("/admin") ||
        window.location.pathname.startsWith("/profile")
      ) {
        window.location.href = "/login";
      }
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
          state.email = action.payload.res.data.email;
          state.role = action.payload.res.data.role;
        },
      )
      .addCase(getMe.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as ErrorResponse;
        userSlice.caseReducers.logout(state);
      });
  },
});

export const { logout } = userSlice.actions;
export const userReducer = userSlice.reducer;
