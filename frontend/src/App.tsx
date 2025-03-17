import { AppRoutes } from "./routes/AppRoutes.tsx";
import ScrollToTop from "./common/helpers/ScrollToTop.tsx";

function App() {
  return (
    <>
      <ScrollToTop />
      <AppRoutes />
    </>
  );
}

export default App;
