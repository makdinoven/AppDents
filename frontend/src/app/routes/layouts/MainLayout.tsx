import { Outlet } from "react-router-dom";
import Header from "../../../shared/components/Header/Header.tsx";
import Footer from "../../../shared/components/Footer/Footer.tsx";
import s from "./Layout.module.scss";
import MobileMenu from "../../../shared/components/ui/MobileMenu/MobileMenu.tsx";
import ScrollToTopButton from "../../../shared/components/ui/ScrollToTopButton/ScrollToTopButton.tsx";
import PaymentPage from "../../../pages/PaymentPage/PaymentPage.tsx";

const MainLayout = () => {
  return (
    <div className={s.main_wrapper}>
      <Header />
      <main className={s.content}>
        <Outlet />
      </main>
      <PaymentPage />
      <Footer />
      <ScrollToTopButton />
      <MobileMenu />
    </div>
  );
};

export default MainLayout;
