import s from "./Hero.module.scss";
import { t } from "i18next";
import Title from "../../../../components/CommonComponents/Title/Title.tsx";
import { Trans } from "react-i18next";
import CircleArrow from "../../../../common/Icons/CircleArrow.tsx";
import ArrowButton from "../../../../components/ui/ArrowButton/ArrowButton.tsx";
import { useRef, useState } from "react";
import ModalWrapper from "../../../../components/ModalWrapper/ModalWrapper.tsx";
import Search from "../../../../components/ui/Search/Search.tsx";

const Hero = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const triggerRef = useRef<HTMLButtonElement | null>(null);

  const handleSearch = () => {};

  return (
    <>
      <section className={s.hero}>
        <div className={s.hero_top}>
          <Search placeholder={t("searchCourses")} onChange={handleSearch} />
          {/*<UnstyledButton*/}
          {/*  ref={triggerRef}*/}
          {/*  onClick={() => setIsModalOpen(true)}*/}
          {/*  className={`${s.filter_btn} ${isModalOpen ? s.filter_btn_active : ""}`}*/}
          {/*>*/}
          {/*  <FilterIcon />*/}
          {/*</UnstyledButton>*/}
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
                srcSet="/src/assets/hero-background-mobile.webp"
                media="(max-width: 576px)"
              />
              <img src="/src/assets/hero-background.webp" alt="Image" />
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
            <span className={s.highlight}>
              <Trans i18nKey="main.hero.widestRange.secondPart" />
            </span>
            <Trans i18nKey="main.hero.widestRange.lastPart" />
          </p>
          <div className={s.btn_wrapper}>
            <ArrowButton text={t("main.hero.chooseCourse")} />
          </div>
          <p className={s.bottom_secondary_desc}>
            <span className={s.highlight}>
              <Trans i18nKey="main.hero.bestPrices.firstPart" />
            </span>
            <Trans i18nKey="main.hero.bestPrices.lastPart" />
          </p>
        </div>
      </section>
      <ModalWrapper
        cutoutPosition="top-right"
        triggerElement={triggerRef.current}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      >
        <h2>Модалка фильтров</h2>
      </ModalWrapper>
    </>
  );
};
export default Hero;
