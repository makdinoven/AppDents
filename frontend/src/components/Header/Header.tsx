import s from "./Header.module.scss";
import { Link } from "react-router-dom";
import { Path } from "../../routes/routes.ts";
import { DentsLogo } from "../../assets/logos/index";
import { useScroll } from "../../common/hooks/useScroll.ts";
import { isPromotionLanding } from "../../common/helpers/helpers.ts";
import PromoHeaderContent from "./content/PromoHeaderContent.tsx";
import MainHeaderContent from "./content/MainHeaderContent.tsx";

const Header = () => {
  const isScrolled = useScroll();
  const isPromotion = isPromotionLanding(location.pathname);

  return (
    <header className={`${s.header} ${isScrolled ? s.scrolled : ""}`}>
      <div className={s.content}>
        <nav className={s.nav}>
          <Link
            className={`${s.logo} ${isPromotion ? s.logoPromo : ""}`}
            to={Path.main}
          >
            <DentsLogo />
          </Link>
          {isPromotion ? <PromoHeaderContent /> : <MainHeaderContent />}
        </nav>
      </div>
    </header>
  );
};

export default Header;
