import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import {
  getCourses,
  getCoursesRecommend,
  getTags,
} from "../actions/mainActions.ts";
import { transformTags } from "../../common/helpers/helpers.ts";

type TagType = {
  id: number;
  name: string;
  value: string;
};

interface MainState {
  tags: TagType[];
  courses: any[];
  totalCourses: number;
  loading: boolean;
  error: string | null;
}

const initialState: MainState = {
  tags: [],
  courses: [],
  totalCourses: 0,
  loading: true,
  error: null,
};

const mainSlice = createSlice({
  name: "main",
  initialState,
  reducers: {
    clearCourses: (state) => {
      state.courses = [];
      state.totalCourses = 0;
    },
  },

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
          state.tags = transformTags(action.payload.res.data);
        },
      )
      .addCase(getTags.rejected, (state, action) => {
        state.loading = false;
        if (action.payload) state.error = action.payload;
      })
      .addCase(getCourses.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(
        getCourses.fulfilled,
        (state, action: PayloadAction<{ res: any }, string, { arg: any }>) => {
          state.loading = false;
          const { cards, total } = action.payload.res.data;
          state.courses =
            state.courses.length && action.meta.arg.skip !== 0
              ? [...state.courses, ...cards]
              : cards;
          state.totalCourses = total;
        },
      )
      .addCase(getCourses.rejected, (state, action) => {
        state.loading = false;
        if (action.payload) state.error = action.payload;
      })
      .addCase(getCoursesRecommend.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(
        getCoursesRecommend.fulfilled,
        (state, action: PayloadAction<{ res: any }, string, { arg: any }>) => {
          state.loading = false;
          const { cards, total } = action.payload.res.data;
          state.courses =
            state.courses.length && action.meta.arg.skip !== 0
              ? [...state.courses, ...cards]
              : cards;
          state.totalCourses = total;
        },
      );
  },
});

export const { clearCourses } = mainSlice.actions;
export const mainReducer = mainSlice.reducer;
