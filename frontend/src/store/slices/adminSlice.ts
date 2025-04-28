import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import {
  createAuthor,
  createCourse,
  createLanding,
  createUser,
  getAuthors,
  getCourses,
  getLandings,
  getUsers,
} from "../actions/adminActions.ts";
import { CourseType } from "../../pages/Admin/types.ts";

interface AdminState {
  courses: CourseType[];
  landings: any;
  users: any;
  authors: any;
  loading: boolean;
  error: null;
}

const initialState: AdminState = {
  courses: [],
  landings: [],
  users: [],
  authors: [],
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
    builder
      .addCase(getAuthors.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(
        getAuthors.fulfilled,
        (state, action: PayloadAction<{ res: any }>) => {
          state.loading = false;
          state.authors = action.payload.res.data.items.sort(
            (a: { id: number }, b: { id: number }) => b.id - a.id,
          );
        },
      )
      .addCase(getAuthors.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as any;
      });

    builder
      .addCase(createAuthor.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(
        createAuthor.fulfilled,
        (state, action: PayloadAction<{ res: any }>) => {
          state.loading = false;
          if (action.payload) {
            state.authors = [action.payload.res.data, ...state.authors];
          }
        },
      )
      .addCase(createAuthor.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as any;
      });

    builder
      .addCase(getUsers.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(
        getUsers.fulfilled,
        (state, action: PayloadAction<{ res: any }>) => {
          state.loading = false;
          state.users = action.payload.res.data.sort(
            (a: { id: number }, b: { id: number }) => b.id - a.id,
          );
        },
      )
      .addCase(getUsers.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as any;
      });

    builder
      .addCase(createUser.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(
        createUser.fulfilled,
        (state, action: PayloadAction<{ res: any }>) => {
          state.loading = false;
          if (action.payload) {
            state.users = [action.payload.res.data, ...state.users];
          }
        },
      )
      .addCase(createUser.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as any;
      });
  },
});

export const adminReducer = adminSlice.reducer;
