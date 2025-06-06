import { Outlet, useLocation } from "react-router-dom";
import Header from "../Header/Header.tsx";
import Footer from "../Footer/Footer.tsx";
import s from "./Layout.module.scss";
import MobileMenu from "../ui/MobileMenu/MobileMenu.tsx";
import ScrollToTopButton from "../ui/ScrollToTopButton/ScrollToTopButton.tsx";
import SearchModal from "../ui/SearchModal/SearchModal.tsx";
import { OPEN_SEARCH_KEY } from "../../common/helpers/commonConstants.ts";

const Layout = () => {
  const location = useLocation();
  const isAdminRoute = location.pathname.startsWith("/admin");

  return (
    <div className={s.main_wrapper}>
      <Header />
      <main className={s.content}>
        <Outlet />
      </main>
      {!isAdminRoute && <Footer />}
      <SearchModal openKey={OPEN_SEARCH_KEY} />
      <MobileMenu />
      <ScrollToTopButton />
    </div>
  );
};

export default Layout;
