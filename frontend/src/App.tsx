import { AppRoutes } from "./routes/AppRoutes.tsx";
import ScrollToTop from "./common/helpers/ScrollToTop.tsx";
import { useLocation } from "react-router-dom";
import { useEffect } from "react";
import {
  initFacebookPixel,
  trackPageView,
} from "./common/helpers/facebookPixel.ts";

function App() {
  const location = useLocation();

  useEffect(() => {
    initFacebookPixel();
  }, []);

  useEffect(() => {
    trackPageView();
  }, [location.pathname]);

  return (
    <>
      <ScrollToTop />
      <AppRoutes />
    </>
  );
}

export default App;
