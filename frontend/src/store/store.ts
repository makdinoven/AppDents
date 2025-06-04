import { configureStore } from "@reduxjs/toolkit";
import { userReducer } from "./slices/userSlice.ts";
import { adminReducer } from "./slices/adminSlice.ts";
import { mainReducer } from "./slices/mainSlice.ts";
import { landingReducer } from "./slices/landingSlice.ts";
import { cartReducer } from "./slices/cartSlice.ts";

export const store = configureStore({
  reducer: {
    user: userReducer,
    admin: adminReducer,
    main: mainReducer,
    landing: landingReducer,
    cart: cartReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: false,
    }),
});

export type AppRootStateType = ReturnType<typeof store.getState>;
export type AppDispatchType = typeof store.dispatch;
