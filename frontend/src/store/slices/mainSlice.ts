import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import {
  getBooks,
  getBooksRecommend,
  getCourses,
  getCoursesRecommend,
  getTags,
  globalSearch,
} from "../actions/mainActions.ts";
import { transformTags } from "../../common/helpers/helpers.ts";
import { LanguagesType } from "../../components/ui/LangLogo/LangLogo.tsx";

export type SearchResultKeysType = "landings" | "authors" | "book_landings";

type TagType = {
  id: number;
  name: string;
  value: string;
};

interface MainState {
  tags: TagType[];
  courses: any[];
  totalCourses: number;
  books: any[];
  totalBooks: number;
  loading: boolean;
  search: SearchType;
  error: string | null;
}

export type ResultBookData = {
  id: number;
  title: string;
  cover?: string;
  price: number;
};

export type ResultLandingData = {
  id: number;
  landing_name: string;
  new_price: number;
  old_price: number;
  preview_photo: string;
  page_name: string;
  authors: any[];
  course_ids: number[];
  language: string;
};

export type ResultAuthorData = {
  id: number;
  language: LanguagesType;
  name: string;
  photo: string;
  courses_count: number;
  books_count: number;
  description: string;
};

export type SearchResultsType = {
  landings: ResultLandingData[] | null;
  authors: ResultAuthorData[] | null;
  book_landings: ResultBookData[];
  counts: Record<SearchResultKeysType, number>;
} | null;

type SearchType = {
  q: string | null;
  loading: boolean;
  selectedLanguages: LanguagesType[] | null;
  selectedCategories: SearchResultKeysType[] | null;
  results: SearchResultsType;
};

const initialState: MainState = {
  tags: [],
  courses: [],
  totalCourses: 0,
  books: [],
  totalBooks: 0,
  loading: true,
  search: {
    q: null,
    loading: false,
    selectedLanguages: null,
    selectedCategories: null,
    results: null,
  },
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
    clearBooks: (state) => {
      state.books = [];
      state.totalBooks = 0;
    },
    clearSearch: (state) => {
      state.search = {
        q: null,
        loading: false,
        selectedLanguages: null,
        selectedCategories: null,
        results: null,
      };
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
      )
      .addCase(getBooks.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(
        getBooks.fulfilled,
        (state, action: PayloadAction<{ res: any }, string, { arg: any }>) => {
          state.loading = false;
          const { cards, total } = action.payload.res.data;
          state.books =
            state.books.length && action.meta.arg.skip !== 0
              ? [...state.books, ...cards]
              : cards;
          state.totalBooks = total;
        },
      )
      .addCase(getBooks.rejected, (state, action) => {
        state.loading = false;
        if (action.payload) state.error = action.payload;
      })
      .addCase(getBooksRecommend.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(
        getBooksRecommend.fulfilled,
        (state, action: PayloadAction<{ res: any }, string, { arg: any }>) => {
          state.loading = false;
          const { cards, total } = action.payload.res.data;
          state.books =
            state.books.length && action.meta.arg.skip !== 0
              ? [...state.books, ...cards]
              : cards;
          state.totalBooks = total;
        },
      )
      .addCase(globalSearch.pending, (state, action) => {
        state.search.loading = true;
        state.search.q = action.meta.arg.q;
        state.search.selectedLanguages = action.meta.arg.languages;
        state.search.selectedCategories = action.meta.arg.types;
      })
      .addCase(
        globalSearch.fulfilled,
        (state, action: PayloadAction<{ res: any }>) => {
          state.search.loading = false;
          state.search.results = {
            landings: action.payload.res.data.landings,
            book_landings: action.payload.res.data.book_landings,
            authors: action.payload.res.data.authors,
            counts: action.payload.res.data.counts,
          };
        },
      )
      .addCase(globalSearch.rejected, (state) => {
        state.search.loading = false;
        state.search.results = null;
      });
  },
});

export const { clearSearch, clearCourses, clearBooks } = mainSlice.actions;
export const mainReducer = mainSlice.reducer;
