import s from "./Pages.module.scss";
import SectionHeader from "../../../../components/ui/SectionHeader/SectionHeader.tsx";
import { Trans } from "react-i18next";
import UniversalSlider from "../../../../components/CommonComponents/UniversalSlider/UniversalSlider.tsx";
import BookImg from "../../../../assets/BOOK_IMG.png";
import { useScreenWidth } from "../../../../common/hooks/useScreenWidth.ts";
import LineWrapper from "../../../../components/ui/LineWrapper/LineWrapper.tsx";

const Pages = ({ data }: { data: any }) => {
  const screenWidth = useScreenWidth();

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

  const renderTitleAndDesc = () => {
    return (
      <>
        <h3 className={s.pages_title}>
          <Trans i18nKey={"bookLanding.pages.readFirstPages"} />
        </h3>
        <p className={s.pages_desc}>
          <Trans i18nKey={"bookLanding.pages.fullBook"} />
        </p>
      </>
    );
  };

  return (
    <section id={"book-pages"} className={s.pages}>
      <SectionHeader name={"bookLanding.pages.title"} />

      <div className={s.pages_container}>
        <div className={s.pages_header}>
          {screenWidth > 768 && renderTitleAndDesc()}
        </div>
        <div className={s.pages_body}>
          {screenWidth <= 768 && renderTitleAndDesc()}
          <UniversalSlider
            paginationType={"dots"}
            paginationColor={"white"}
            pagination
            navigation
            navigationClassname={s.page_nav}
            navigationPosition={"center"}
            slides={slides}
          />
        </div>
      </div>
      <p className={s.program_p}>
        <Trans
          i18nKey="landing.youCanBuyEntireCourse"
          values={{ new_price: data.new_price, old_price: data.old_price }}
          components={{
            1: <span className="highlight" />,
            2: <span className="highlight" />,
          }}
        />
      </p>
      <LineWrapper>{data.renderBuyButton}</LineWrapper>
    </section>
  );
};

export default Pages;
