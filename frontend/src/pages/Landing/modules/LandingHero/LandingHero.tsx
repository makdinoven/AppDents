import { useState, useEffect } from "react";
import s from "./LandingHero.module.scss";
import Title from "../../../../components/ui/Title/Title.tsx";
import { Trans } from "react-i18next";
import initialPhoto from "../../../../assets/no-pictures.png";
import { CircleArrow } from "../../../../assets/icons/index.ts";

const LandingHero = ({
  data: { photo, landing_name, authors, renderBuyButton, isWebinar },
}: {
  data: any;
}) => {
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
    <section className={s.hero}>
      {!isMobile ? (
        <div className={s.hero_top}>
          <Title>
            <Trans i18nKey={isWebinar ? "onlineWebinar" : "onlineCourse"} />
          </Title>
          <div className={s.card_header}></div>
        </div>
      ) : null}

      <div className={s.hero_content_wrapper}>
        <div className={s.card}>
          {isMobile ? (
            <div className={s.folder}>
              <Title>
                <Trans i18nKey={isWebinar ? "onlineWebinar" : "onlineCourse"} />
              </Title>
            </div>
          ) : null}
          <div className={s.card_body}>
            <div className={s.photo}>
              {photo ? (
                <img src={photo} alt="Course image" />
              ) : (
                <div
                  style={{ backgroundImage: `url(${initialPhoto})` }}
                  className={s.no_photo}
                ></div>
              )}
            </div>
          </div>
          <div className={s.card_bottom}></div>
        </div>

        <div className={s.hero_content}>
          <h2>{landing_name}</h2>
          <div className={s.arrow}>
            <CircleArrow />
          </div>
          <p>{authors}</p>
          {renderBuyButton}
        </div>
      </div>
    </section>
  );
};

export default LandingHero;
