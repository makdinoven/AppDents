import { Outlet, useLocation } from "react-router-dom";
import Header from "../Header/Header.tsx";
import Footer from "../Footer/Footer.tsx";
import s from "./Layout.module.scss";

const Layout = () => {
  const location = useLocation();
  const isAdminRoute = location.pathname.startsWith("/admin");

  return (
    <div className={s.main_wrapper}>
      <Header />
      <div className={s.content}>
        <Outlet />
      </div>
      {!isAdminRoute && <Footer />}
    </div>
  );
};

export default Layout;
