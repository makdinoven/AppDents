import s from "./Pages.module.scss";
import SectionHeader from "../../../../components/ui/SectionHeader/SectionHeader.tsx";
import { Trans } from "react-i18next";
import UniversalSlider from "../../../../components/CommonComponents/UniversalSlider/UniversalSlider.tsx";
import BookImg from "../../../../assets/BOOK_IMG.png";

const Pages = () => {
  // const screenWidth = useScreenWidth();

  const slides = [
    <div className={s.page}>
      <img src={BookImg} alt="" />
    </div>,
    <div className={s.page}>
      <img src={BookImg} alt="" />
    </div>,
    <div className={s.page}>
      <img src={BookImg} alt="" />
    </div>,
  ];

  return (
    <section className={s.pages}>
      <SectionHeader name={"bookLanding.pages.title"} />

      <div className={s.pages_container}>
        <div className={s.pages_header}>
          <h3>
            <Trans i18nKey={"bookLanding.pages.readFirstPages"} />
          </h3>
          <p>
            <Trans i18nKey={"bookLanding.pages.fullBook"} />
          </p>
        </div>
        <div className={s.pages_body}>
          <UniversalSlider
            paginationType={"dots"}
            pagination
            navigation
            navigationPosition={"center"}
            slides={slides}
            slidesPerView={3}
          />
        </div>
      </div>
    </section>
  );
};

export default Pages;
