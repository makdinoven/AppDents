import { AppRoutes } from "./routes/AppRoutes.tsx";
import { useLocation } from "react-router-dom";
import { useEffect } from "react";
import {
  initFacebookPixel,
  trackPageView,
} from "./common/helpers/facebookPixel.ts";
import { AppDispatchType } from "./store/store.ts";
import { useDispatch, useSelector } from "react-redux";
import { setLanguage } from "./store/slices/userSlice.ts";
import ScrollToTop from "./common/helpers/ScrollToTop.tsx";
import { getMe } from "./store/actions/userActions.ts";

function App() {
  const location = useLocation();
  const dispatch = useDispatch<AppDispatchType>();
  const language = useSelector((state: any) => state.user.language);

  useEffect(() => {
    initFacebookPixel();
  }, []);

  useEffect(() => {
    trackPageView();
  }, [location.pathname]);

  useEffect(() => {
    dispatch(getMe());
    const storedLanguage = localStorage.getItem("DENTS_LANGUAGE") || language;
    dispatch(setLanguage(storedLanguage));
  }, []);

  return (
    <>
      <ScrollToTop />
      <AppRoutes />
    </>
  );
}

export default App;
