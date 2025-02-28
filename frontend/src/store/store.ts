import { configureStore } from "@reduxjs/toolkit";
import { userReducer } from "./slices/userSlice.ts";
import { adminReducer } from "./slices/adminSlice.ts";
import { mainReducer } from "./slices/mainSlice.ts";

export const store = configureStore({
  reducer: {
    user: userReducer,
    admin: adminReducer,
    main: mainReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: false,
    }),
});

// types
export type AppRootStateType = ReturnType<typeof store.getState>;
export type AppDispatchType = typeof store.dispatch;
