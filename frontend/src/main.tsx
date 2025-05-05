import { Suspense } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import "./styles/index.scss";
import App from "./App.tsx";
import { Provider } from "react-redux";
import { store } from "./store/store.ts";
import "./i18n/i18n.ts";
import { TriggerRefProvider } from "./common/context/TriggerRefContext.tsx";

createRoot(document.getElementById("root")!).render(
  <Provider store={store}>
    <BrowserRouter>
      <TriggerRefProvider>
        <Suspense fallback="loading">
          <App />
        </Suspense>
      </TriggerRefProvider>
    </BrowserRouter>
  </Provider>,
);
