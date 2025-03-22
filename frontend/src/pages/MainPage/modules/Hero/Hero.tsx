import s from "./Hero.module.scss";
import { t } from "i18next";
import Title from "../../../../components/ui/Title/Title.tsx";
import { Trans } from "react-i18next";
import CircleArrow from "../../../../common/Icons/CircleArrow.tsx";
import ArrowButton from "../../../../components/ui/ArrowButton/ArrowButton.tsx";
import Search from "../../../../components/ui/Search/Search.tsx";
import HeroBackgroundMobile from "/src/assets/hero-background-mobile.webp";
import HeroBackground from "/src/assets/hero-background.webp";
import LineWrapper from "../../../../components/ui/LineWrapper/LineWrapper.tsx";

const Hero = () => {
  const handleSearch = () => {};

  return (
    <>
      <section className={s.hero}>
        <div className={s.hero_top}>
          <Search
            value={""}
            placeholder={t("searchCourses")}
            onChange={handleSearch}
          />
        </div>
        <div className={s.hero_content}>
          <Title>
            <div className={s.title_first_line}>
              <Trans i18nKey="main.title.firstPart" />
              <span className={s.highlight}>
                <Trans i18nKey="main.title.secondPart" />
              </span>
            </div>
            <Trans i18nKey="main.title.lastPart" />
          </Title>
          <div className={s.img_wrapper}>
            <picture>
              <source
                srcSet={HeroBackgroundMobile}
                media="(max-width: 576px)"
              />
              <img src={HeroBackground} alt="" />
            </picture>
            <div className={s.glass_block}>
              <CircleArrow />
              <p>
                <Trans i18nKey="main.hero.description" />
              </p>
            </div>
          </div>
        </div>
        <div className={s.hero_bottom}>
          <p className={s.bottom_desc}>
            <Trans i18nKey="main.hero.widestRange.firstPart" />
            <span className="highlight">
              <Trans i18nKey="main.hero.widestRange.secondPart" />
            </span>
            <Trans i18nKey="main.hero.widestRange.lastPart" />
          </p>
          <LineWrapper>
            <ArrowButton text={t("main.hero.chooseCourse")} />
          </LineWrapper>
          <p className={s.bottom_secondary_desc}>
            <span className="highlight">
              <Trans i18nKey="main.hero.bestPrices.firstPart" />
            </span>
            <Trans i18nKey="main.hero.bestPrices.lastPart" />
          </p>
        </div>
      </section>
    </>
  );
};
export default Hero;
