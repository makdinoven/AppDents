import React, { useState, useEffect } from "react";
import s from "./LandingHero.module.scss";
import Title from "../../../../components/ui/Title/Title.tsx";
import { Trans } from "react-i18next";
import { CircleArrow, TagIcon } from "../../../../assets/icons/index.ts";
import LandingHeroSkeleton from "../../../../components/ui/Skeletons/LandingHeroSkeleton/LandingHeroSkeleton.tsx";
import { NoPictures } from "../../../../assets";
import { t } from "i18next";

interface LandingHeroProps {
  data: any;
  loading: boolean;
}

const LandingHero: React.FC<LandingHeroProps> = ({
  data,
  loading,
}: LandingHeroProps) => {
  const {
    photo,
    landing_name,
    authors,
    renderBuyButton,
    isWebinar,
    tags,
    sales,
  } = data;

  const MOBILE_BREAKPOINT = 576;

  const [isMobile, setIsMobile] = useState(
    window.innerWidth < MOBILE_BREAKPOINT,
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
      {loading ? (
        <LandingHeroSkeleton />
      ) : (
        <>
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
                    <Trans
                      i18nKey={isWebinar ? "onlineWebinar" : "onlineCourse"}
                    />
                  </Title>
                </div>
              ) : null}
              <div className={s.card_body}>
                <div className={s.photo}>
                  {photo ? (
                    <img src={photo} alt="Course image" />
                  ) : (
                    <NoPictures />
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
              <p className={s.authors}>{authors}</p>
              {tags?.length > 0 && (
                <div>
                  <TagIcon />
                  {tags
                    ?.map((tag: any) => {
                      return t(tag.name);
                    })
                    .join(", ")}
                </div>
              )}
              {sales && sales > 100 && (
                <p className={s.sales}>
                  <Trans
                    i18nKey={"landing.sales"}
                    values={{
                      sales: sales,
                    }}
                    components={[<span className={s.highlight} />]}
                  />
                </p>
              )}
              {renderBuyButton}
            </div>
          </div>
        </>
      )}
    </section>
  );
};

export default LandingHero;
