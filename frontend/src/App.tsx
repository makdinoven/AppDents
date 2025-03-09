import { AppRoutes } from "./routes/AppRoutes.tsx";
import { useEffect } from "react";
import { AppDispatchType } from "./store/store.ts";
import { useDispatch } from "react-redux";
import { getMe } from "./store/actions/userActions.ts";
import ScrollToTop from "./common/helpers/ScrollToTop.tsx";

function App() {
  const dispatch = useDispatch<AppDispatchType>();

  useEffect(() => {
    dispatch(getMe());
  }, [dispatch]);

  return (
    <>
      <ScrollToTop />
      <AppRoutes />
    </>
  );
}

export default App;
