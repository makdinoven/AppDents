import { Suspense } from "react";
import { createRoot } from "react-dom/client";
import "./styles/index.scss";
import { Provider } from "react-redux";
import { store } from "../shared/store/store.ts";
import "../shared/i18n/i18n.ts";
import { TriggerRefProvider } from "../shared/common/context/TriggerRefContext.tsx";
import {
  AuthProvider,
  RouterProvider,
  ScrollToTopProvider,
} from "./routes/providers";
import { BrowserRouter } from "react-router-dom";

createRoot(document.getElementById("root")!).render(
  <Provider store={store}>
    <BrowserRouter>
      <AuthProvider>
        <ScrollToTopProvider>
          <TriggerRefProvider>
            <Suspense fallback="loading">
              <RouterProvider />
            </Suspense>
          </TriggerRefProvider>
        </ScrollToTopProvider>
      </AuthProvider>
    </BrowserRouter>
  </Provider>,
);
