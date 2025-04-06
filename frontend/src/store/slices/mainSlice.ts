import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { getTags } from "../actions/mainActions.ts";

interface MainState {
  tags: string[];
  loading: boolean;
  error: string | null;
}

const initialState: MainState = {
  tags: [],
  loading: true,
  error: null,
};

const mainSlice = createSlice({
  name: "main",
  initialState,
  reducers: {},

  extraReducers: (builder) => {
    builder
      .addCase(getTags.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(
        getTags.fulfilled,
        (state, action: PayloadAction<{ res: any }>) => {
          state.loading = false;
          state.tags = action.payload.res.data;
        },
      )
      .addCase(getTags.rejected, (state, action) => {
        state.loading = false;
        if (action.payload) state.error = action.payload;
      });
  },
});

export const mainReducer = mainSlice.reducer;
