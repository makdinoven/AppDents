import s from "./Header.module.scss";
import { Link, useLocation } from "react-router-dom";
import { useScroll } from "../../common/hooks/useScroll.ts";
import PromoHeaderContent from "./content/PromoHeaderContent.tsx";
import MainHeaderContent from "./content/MainHeaderContent.tsx";
import VideoHeaderContent from "./content/VideoHeaderContent.tsx";
import {
  isBookLanding,
  isPromotionLanding,
  isVideoLanding,
} from "../../common/helpers/helpers.ts";
import TimerBanner from "../ui/TimerBanner/TimerBanner.tsx";
import PromoBookHeaderContent from "./content/PromoBookHeaderContent.tsx";
import AppLogo from "@logo";
import { PATHS } from "../../../app/routes/routes.ts";

const Header = () => {
  const location = useLocation();
  const isScrolled = useScroll();
  const isPromotion = isPromotionLanding(location.pathname);
  const isVideo = isVideoLanding(location.pathname);
  const isBook = isBookLanding(location.pathname);

  const renderHeaderContent = () => {
    if (isVideo) return <VideoHeaderContent />;
    if (isPromotion && !isBook) return <PromoHeaderContent />;
    if (isBook && isPromotion) return <PromoBookHeaderContent />;
    return <MainHeaderContent />;
  };

  const showTimer = isPromotion && !isVideo;

  return (
    <>
      {showTimer && <TimerBanner />}
      <header className={`${s.header} ${isScrolled ? s.scrolled : ""}`}>
        <div className={`${s.content} ${isVideo ? s.video : ""}`}>
          <nav className={`${s.nav} ${isPromotion ? "" : s.main}`}>
            {!isVideo && (
              <Link
                className={`${s.logo} ${isPromotion ? s.logoPromo : ""}`}
                to={PATHS.MAIN}
              >
                <AppLogo />
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
