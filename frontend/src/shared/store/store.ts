import { configureStore } from "@reduxjs/toolkit";
import { userReducer } from "./slices/userSlice.ts";
import { adminReducer } from "./slices/adminSlice.ts";
import { mainReducer } from "./slices/mainSlice.ts";
import { cartReducer } from "./slices/cartSlice.ts";
import { paymentReducer } from "./slices/paymentSlice.ts";

export const store = configureStore({
  reducer: {
    user: userReducer,
    payment: paymentReducer,
    admin: adminReducer,
    main: mainReducer,
    cart: cartReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: false,
    }),
});

export type AppRootStateType = ReturnType<typeof store.getState>;
export type AppDispatchType = typeof store.dispatch;
