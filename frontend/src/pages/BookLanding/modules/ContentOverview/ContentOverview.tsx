import React, { useEffect, useState } from "react";
import s from "./ContentOverview.module.scss";
import UniversalSlider from "../../../../components/CommonComponents/UniversalSlider/UniversalSlider.tsx";
import ContentOverviewSlide from "./modules/ContentOverviewSlide/ContentOverviewSlide.tsx";
import SectionHeader from "../../../../components/ui/SectionHeader/SectionHeader.tsx";
import { useTranslation } from "react-i18next";

interface ContentOverviewProps {
  books: any[];
}

const ContentOverview: React.FC<ContentOverviewProps> = ({
  books,
}: ContentOverviewProps) => {
  const [screenWidth, setScreenWidth] = useState(window.innerWidth);
  const MIDDLE = 1024;

  useEffect(() => {
    const handleResize = () => {
      setScreenWidth(window.innerWidth);
    };

    handleResize();

    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
    };
  }, [screenWidth]);

  const slides = books.map((book: any, index) => (
    <ContentOverviewSlide book={book} index={index} />
  ));

  const { t } = useTranslation();
  return (
    <div className={s.content_overview}>
      <SectionHeader name={t("bookLanding.contentOverview")} />
      <UniversalSlider
        slides={slides}
        className={s.slider}
        navigation
        navigationPosition="center"
        pagination={screenWidth < MIDDLE}
        paginationType="dots"
      />
    </div>
  );
};

export default ContentOverview;
