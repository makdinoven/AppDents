import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import {
  getAuthors,
  getCourses,
  getLandings,
  getUsers,
  searchAuthors,
  searchCourses,
  searchLandings,
  searchUsers,
} from "../actions/adminActions.ts";

interface PaginationListType {
  list: any[];
  total: number | null;
  total_pages: number | null;
}

interface AdminState {
  courses: PaginationListType;
  landings: PaginationListType;
  users: PaginationListType;
  authors: PaginationListType;
  loading: boolean;
  error: null;
}

const initialPaginationListState: PaginationListType = {
  list: [],
  total: null,
  total_pages: null,
};

const initialState: AdminState = {
  courses: initialPaginationListState,
  landings: initialPaginationListState,
  users: initialPaginationListState,
  authors: initialPaginationListState,
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
          state.courses.list = action.payload.res.data.items;
          state.courses.total_pages = action.payload.res.data.total_pages;
          state.courses.total = action.payload.res.data.total;
        },
      )
      .addCase(getCourses.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as any;
      });
    builder
      .addCase(searchCourses.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(
        searchCourses.fulfilled,
        (state, action: PayloadAction<{ res: any }>) => {
          state.loading = false;
          state.courses.list = action.payload.res.data.items;
          state.courses.total_pages = action.payload.res.data.total_pages;
          state.courses.total = action.payload.res.data.total;
        },
      )
      .addCase(searchCourses.rejected, (state, action) => {
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
          state.landings.list = action.payload.res.data.items;
          state.landings.total_pages = action.payload.res.data.total_pages;
          state.landings.total = action.payload.res.data.total;
        },
      )
      .addCase(searchLandings.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as any;
      });
    builder
      .addCase(searchLandings.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(
        searchLandings.fulfilled,
        (state, action: PayloadAction<{ res: any }>) => {
          state.loading = false;
          state.landings.list = action.payload.res.data.items;
          state.landings.total_pages = action.payload.res.data.total_pages;
          state.landings.total = action.payload.res.data.total;
        },
      )
      .addCase(getLandings.rejected, (state, action) => {
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
          state.authors.list = action.payload.res.data.items;
          state.authors.total_pages = action.payload.res.data.total_pages;
          state.authors.total = action.payload.res.data.total;
        },
      )
      .addCase(searchAuthors.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as any;
      });

    builder
      .addCase(searchAuthors.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(
        searchAuthors.fulfilled,
        (state, action: PayloadAction<{ res: any }>) => {
          state.loading = false;
          state.authors.list = action.payload.res.data.items;
          state.authors.total_pages = action.payload.res.data.total_pages;
          state.authors.total = action.payload.res.data.total;
        },
      )
      .addCase(getAuthors.rejected, (state, action) => {
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
          state.users.list = action.payload.res.data.items;
          state.users.total_pages = action.payload.res.data.total_pages;
          state.users.total = action.payload.res.data.total;
        },
      )
      .addCase(getUsers.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as any;
      });

    builder
      .addCase(searchUsers.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(
        searchUsers.fulfilled,
        (state, action: PayloadAction<{ res: any }>) => {
          state.loading = false;
          state.users.list = action.payload.res.data.items;
          state.users.total_pages = action.payload.res.data.total_pages;
          state.users.total = action.payload.res.data.total;
        },
      )
      .addCase(searchUsers.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as any;
      });
  },
});

export const adminReducer = adminSlice.reducer;
