import { AppRoutes } from "./routes/AppRoutes.tsx";
import { useLocation } from "react-router-dom";
import { useEffect } from "react";
import {
  initFacebookPixel,
  initLanguagePixel,
  trackPageView,
} from "./common/helpers/facebookPixel.ts";
import { AppDispatchType } from "./store/store.ts";
import { useDispatch, useSelector } from "react-redux";
import { setLanguage } from "./store/slices/userSlice.ts";
import { getMe } from "./store/actions/userActions.ts";
import ScrollToTop from "./common/helpers/ScrollToTop.tsx";
import { getCart } from "./store/actions/cartActions.ts";
import {
  LS_LANGUAGE_KEY,
  REF_CODE_LS_KEY,
  REF_CODE_PARAM,
} from "./common/helpers/commonConstants.ts";

function App() {
  const location = useLocation();
  const dispatch = useDispatch<AppDispatchType>();
  const language = useSelector((state: any) => state.user.language);
  const isLogged = useSelector((state: any) => state.user.isLogged);

  useEffect(() => {
    initLanguagePixel(language);
    trackPageView();
  }, [location.pathname, language]);

  useEffect(() => {
    dispatch(getMe());
  }, []);

  useEffect(() => {
    initFacebookPixel();
    // dispatch(getMe());
    const storedLanguage = localStorage.getItem(LS_LANGUAGE_KEY) || language;
    dispatch(setLanguage(storedLanguage));
  }, []);

  useEffect(() => {
    if (isLogged) {
      dispatch(getCart());
    } else {
      const searchParams = new URLSearchParams(location.search);
      const rcCode = searchParams.get(REF_CODE_PARAM);

      if (rcCode) {
        localStorage.setItem(REF_CODE_LS_KEY, rcCode);
      }
    }
  }, [isLogged]);

  return (
    <div lang={language.toLowerCase()}>
      <ScrollToTop />
      <AppRoutes />
    </div>
  );
}

export default App;
