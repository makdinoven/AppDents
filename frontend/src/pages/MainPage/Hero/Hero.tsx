import s from "./Hero.module.scss";
import { t } from "i18next";
import Title from "../../../components/ui/Title/Title.tsx";
import { Trans } from "react-i18next";
import ArrowButton from "../../../components/ui/ArrowButton/ArrowButton.tsx";
import LineWrapper from "../../../components/ui/LineWrapper/LineWrapper.tsx";
// import UniversalSlider from "../../../components/CommonComponents/UniversalSlider/UniversalSlider.tsx";
import { CircleArrow } from "../../../assets/icons/index.ts";
import HeroBackgroundMobile from "/src/assets/hero-background-mobile.webp";
import HeroBackground from "/src/assets/hero-background.webp";

// const slides = [
//   <div>Слайд 1</div>,
//   <div>Слайд 2</div>,
//   <div>Слайд 3</div>,
//   <div>Слайд 4</div>,
//   <div>Слайд 5</div>,
//   <div>Слайд 6</div>,
// ];

const Hero = ({ onClickScroll }: { onClickScroll: () => void }) => {
  return (
    <>
      <section className={s.hero}>
        <div className={s.hero_content}>
          <Title>
            <Trans
              i18nKey="main.title"
              components={{
                1: <span className="highlight" />,
              }}
            />
          </Title>
          {/*<UniversalSlider*/}
          {/*  slides={slides}*/}
          {/*  effect="coverflow"*/}
          {/*  autoplay*/}
          {/*  pagination*/}
          {/*  delay={5000}*/}
          {/*/>*/}
          <div className={s.img_wrapper}>
            <picture>
              <source
                srcSet={HeroBackgroundMobile}
                media="(max-width: 576px)"
              />
              <img src={HeroBackground} alt="" />
            </picture>
            <div onClick={onClickScroll} className={s.glass_block}>
              <CircleArrow />
              <p>
                <Trans i18nKey="main.hero.description" />
              </p>
            </div>
          </div>
        </div>
        <div className={s.hero_bottom}>
          <p className={s.bottom_desc}>
            <Trans
              i18nKey="main.hero.widestRange"
              components={{
                1: <span className="highlight" />,
              }}
            />
          </p>
          <LineWrapper>
            <ArrowButton
              onClick={onClickScroll}
              text={t("main.hero.chooseCourse")}
            />
          </LineWrapper>
          <p className={s.bottom_secondary_desc}>
            <Trans
              i18nKey="main.hero.bestPrices"
              components={{
                1: <span className="highlight" />,
              }}
            />
          </p>
        </div>
      </section>
    </>
  );
};
export default Hero;
