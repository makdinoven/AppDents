import s from "./Hero.module.scss";
import { t } from "i18next";
import Title from "../../../components/ui/Title/Title.tsx";
import { Trans } from "react-i18next";
import ArrowButton from "../../../components/ui/ArrowButton/ArrowButton.tsx";
import LineWrapper from "../../../components/ui/LineWrapper/LineWrapper.tsx";
import MainSlider from "../../../components/CommonComponents/MainSlider/MainSlider.tsx";

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
          <MainSlider />
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
