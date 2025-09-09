import React, { useEffect, useState } from "react";
import s from "./LandingHeroSkeleton.module.scss";
import { CircleArrow } from "../../../../assets/icons";

interface LandingHeroSkeletonProps {}

const LandingHeroSkeleton: React.FC<
  LandingHeroSkeletonProps
> = ({}: LandingHeroSkeletonProps) => {
  const MOBILE_BREAKPOINT = 576;

  const [isMobile, setIsMobile] = useState(
    window.innerWidth < MOBILE_BREAKPOINT
  );

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < MOBILE_BREAKPOINT);
    };

    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
    };
  }, [isMobile]);

  return (
    <>
      {!isMobile ? (
        <div className={s.hero_top}>
          <h1 className={s.title}></h1>
          <div className={s.card_header}></div>
        </div>
      ) : null}
      <div className={s.hero_content_wrapper}>
        <div className={s.card}>
          {isMobile ? (
            <div className={s.folder}>
              <h1 className={s.title}></h1>
            </div>
          ) : null}
          <div className={s.card_body}>
            <div className={s.photo}></div>
          </div>
          <div className={s.card_bottom}></div>
        </div>
        <div className={s.hero_content}>
          <h2 className={s.landing_name}></h2>
          <div className={s.arrow}>
            <CircleArrow />
          </div>
          <p></p>
          <div className={s.buy_button}></div>
        </div>
      </div>
    </>
  );
};

export default LandingHeroSkeleton;
