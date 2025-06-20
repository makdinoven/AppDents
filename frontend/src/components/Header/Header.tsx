import s from "./Header.module.scss";
import { Link, useLocation } from "react-router-dom";
import { Path } from "../../routes/routes.ts";
import { DentsLogo } from "../../assets/logos/index";
import { useScroll } from "../../common/hooks/useScroll.ts";
import PromoHeaderContent from "./content/PromoHeaderContent.tsx";
import MainHeaderContent from "./content/MainHeaderContent.tsx";
import VideoHeaderContent from "./content/VideoHeaderContent.tsx";
import {
  isPromotionLanding,
  isVideoLanding,
} from "../../common/helpers/helpers.ts";
import TimerBanner from "../ui/TimerBanner/TimerBanner.tsx";

const Header = () => {
  const location = useLocation();
  const isScrolled = useScroll();
  const isPromotion = isPromotionLanding(location.pathname);
  const isVideo = isVideoLanding(location.pathname);

  const renderHeaderContent = () => {
    if (isVideo) return <VideoHeaderContent />;
    if (isPromotion) return <PromoHeaderContent />;
    return <MainHeaderContent />;
  };

  return (
    <>
      {isPromotion && !isVideo && <TimerBanner />}
      <header className={`${s.header} ${isScrolled ? s.scrolled : ""}`}>
        <div className={`${s.content} ${isVideo ? s.video : ""}`}>
          <nav className={s.nav}>
            {!isVideo && (
              <Link
                className={`${s.logo} ${isPromotion ? s.logoPromo : ""}`}
                to={Path.main}
              >
                <DentsLogo />
              </Link>
            )}

            {renderHeaderContent()}
          </nav>
        </div>
      </header>
    </>
  );
};

export default Header;
