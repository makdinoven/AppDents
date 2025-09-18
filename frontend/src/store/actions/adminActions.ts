import { createAppAsyncThunk } from "../createAppAsynkThunk.ts";
import { adminApi } from "../../api/adminApi/adminApi.ts";
import { ParamsType } from "../../api/adminApi/types.ts";

export const getCourses = createAppAsyncThunk(
  "admin/getCourses",
  async (params: ParamsType, { rejectWithValue }) => {
    try {
      const res = await adminApi.getCoursesList(params);
      if (res.data.error) {
        return rejectWithValue(res.data.error);
      }

      return { res };
    } catch (e: any) {
      return rejectWithValue(e.response.data);
    }
  },
);

export const searchCourses = createAppAsyncThunk(
  "admin/searchCourses",
  async (params: ParamsType, { rejectWithValue }) => {
    try {
      const res = await adminApi.searchCourses(params);
      if (res.data.error) {
        return rejectWithValue(res.data.error);
      }

      return { res };
    } catch (e: any) {
      return rejectWithValue(e.response.data);
    }
  },
);

export const createCourse = createAppAsyncThunk(
  "admin/createCourse",
  async (data: any, { rejectWithValue }) => {
    try {
      const res = await adminApi.createCourse(data);
      if (res.data.error) {
        return rejectWithValue(res.data.error);
      }

      return { res };
    } catch (e: any) {
      return rejectWithValue(e.response.data);
    }
  },
);

export const getLandings = createAppAsyncThunk(
  "admin/getLandings",
  async (params: ParamsType, { rejectWithValue }) => {
    try {
      const res = await adminApi.getLandingsList(params);
      if (res.data.error) {
        return rejectWithValue(res.data.error);
      }

      return { res };
    } catch (e: any) {
      return rejectWithValue(e.response.data);
    }
  },
);

export const searchLandings = createAppAsyncThunk(
  "admin/searchLandings",
  async (params: ParamsType, { rejectWithValue }) => {
    try {
      const res = await adminApi.searchLandings(params);
      if (res.data.error) {
        return rejectWithValue(res.data.error);
      }

      return { res };
    } catch (e: any) {
      return rejectWithValue(e.response.data);
    }
  },
);

export const createLanding = createAppAsyncThunk(
  "admin/createLanding",
  async (data: any, { rejectWithValue }) => {
    try {
      const res = await adminApi.createLanding(data);
      if (res.data.error) {
        return rejectWithValue(res.data.error);
      }

      return { res };
    } catch (e: any) {
      return rejectWithValue(e.response.data);
    }
  },
);

export const getBooks = createAppAsyncThunk(
  "admin/getBooks",
  async (params: ParamsType, { rejectWithValue }) => {
    try {
      const res = await adminApi.getBooksList(params);
      if (res.data.error) {
        return rejectWithValue(res.data.error);
      }

      return { res };
    } catch (e: any) {
      return rejectWithValue(e.response.data);
    }
  },
);

export const searchBooks = createAppAsyncThunk(
  "admin/searchBooks",
  async (params: ParamsType, { rejectWithValue }) => {
    try {
      const res = await adminApi.searchBooks(params);
      if (res.data.error) {
        return rejectWithValue(res.data.error);
      }

      return { res };
    } catch (e: any) {
      return rejectWithValue(e.response.data);
    }
  },
);

export const createBook = createAppAsyncThunk(
  "admin/createBook",
  async (data: any, { rejectWithValue }) => {
    try {
      const res = await adminApi.createBook(data);
      if (res.data.error) {
        return rejectWithValue(res.data.error);
      }

      return { res };
    } catch (e: any) {
      return rejectWithValue(e.response.data);
    }
  },
);

export const getAuthors = createAppAsyncThunk(
  "admin/getAuthors",
  async (params: ParamsType, { rejectWithValue }) => {
    try {
      const res = await adminApi.getAuthorsList(params);
      if (res.data.error) {
        return rejectWithValue(res.data.error);
      }

      return { res };
    } catch (e: any) {
      return rejectWithValue(e.response.data);
    }
  },
);

export const searchAuthors = createAppAsyncThunk(
  "admin/searchAuthors",
  async (params: ParamsType, { rejectWithValue }) => {
    try {
      const res = await adminApi.searchAuthors(params);
      if (res.data.error) {
        return rejectWithValue(res.data.error);
      }

      return { res };
    } catch (e: any) {
      return rejectWithValue(e.response.data);
    }
  },
);

export const createAuthor = createAppAsyncThunk(
  "admin/createAuthor",
  async (data: any, { rejectWithValue }) => {
    try {
      const res = await adminApi.createAuthor(data);
      if (res.data.error) {
        return rejectWithValue(res.data.error);
      }

      return { res };
    } catch (e: any) {
      return rejectWithValue(e.response.data);
    }
  },
);

export const getUsers = createAppAsyncThunk(
  "admin/getUsers",
  async (params: ParamsType, { rejectWithValue }) => {
    try {
      const res = await adminApi.getUsersList(params);
      if (res.data.error) {
        return rejectWithValue(res.data.error);
      }

      return { res };
    } catch (e: any) {
      return rejectWithValue(e.response.data);
    }
  },
);

export const searchUsers = createAppAsyncThunk(
  "admin/searchUsers",
  async (params: ParamsType, { rejectWithValue }) => {
    try {
      const res = await adminApi.searchUsers(params);
      if (res.data.error) {
        return rejectWithValue(res.data.error);
      }

      return { res };
    } catch (e: any) {
      return rejectWithValue(e.response.data);
    }
  },
);

export const createUser = createAppAsyncThunk(
  "admin/createUser",
  async (data: any, { rejectWithValue }) => {
    try {
      const res = await adminApi.createUser(data);
      if (res.data.error) {
        return rejectWithValue(res.data.error);
      }

      return { res };
    } catch (e: any) {
      return rejectWithValue(e.response.data);
    }
  },
);
