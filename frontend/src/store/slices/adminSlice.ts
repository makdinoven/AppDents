import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import {
  createCourse,
  createLanding,
  getCourses,
  getLandings,
} from "../actions/adminActions.ts";
import { CourseType } from "../../pages/Admin/types.ts";

interface AdminState {
  courses: CourseType[];
  landings: any;
  users: [];
  loading: boolean;
  error: null;
}

const initialState: AdminState = {
  courses: [],
  landings: [],
  users: [],
  loading: false,
  error: null,
};

const adminSlice = createSlice({
  name: "admin",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(getCourses.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(
        getCourses.fulfilled,
        (state, action: PayloadAction<{ res: any }>) => {
          state.loading = false;
          state.courses = action.payload.res.data.sort(
            (a: { id: number }, b: { id: number }) => b.id - a.id,
          );
        },
      )
      .addCase(getCourses.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as any;
      });

    builder
      .addCase(createCourse.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(
        createCourse.fulfilled,
        (state, action: PayloadAction<{ res: any }>) => {
          state.loading = false;
          if (action.payload) {
            state.courses = [action.payload.res.data, ...state.courses];
          }
        },
      )
      .addCase(createCourse.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as any;
      });
    builder
      .addCase(getLandings.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(
        getLandings.fulfilled,
        (state, action: PayloadAction<{ res: any }>) => {
          state.loading = false;
          state.landings = action.payload.res.data.sort(
            (a: { id: number }, b: { id: number }) => b.id - a.id,
          );
        },
      )
      .addCase(getLandings.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as any;
      });

    builder
      .addCase(createLanding.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(
        createLanding.fulfilled,
        (state, action: PayloadAction<{ res: any }>) => {
          state.loading = false;
          if (action.payload) {
            state.landings = [action.payload.res.data, ...state.landings];
          }
        },
      )
      .addCase(createLanding.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as any;
      });
  },
});

export const adminReducer = adminSlice.reducer;
