import React, { useEffect, useRef, useState } from "react";
import s from "./ContentOverview.module.scss";
import ContentOverviewSlide, {
  ContentOverviewSlideRef,
} from "./modules/ContentOverviewSlide/ContentOverviewSlide.tsx";
import SectionHeader from "../../../../components/ui/SectionHeader/SectionHeader.tsx";
import { useTranslation } from "react-i18next";
import ContentSliderWrapper from "./modules/ContentSliderWrapper/ContentSliderWrapper.tsx";

interface ContentOverviewProps {
  books: any[];
  portalParentId: string;
}

const ContentOverview: React.FC<ContentOverviewProps> = ({
  books,
  portalParentId,
}: ContentOverviewProps) => {
  const { t } = useTranslation();
  const [screenWidth, setScreenWidth] = useState(window.innerWidth);
  const slideRefs = useRef<ContentOverviewSlideRef[]>([]);

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
    <ContentOverviewSlide
      key={index}
      book={book}
      parentId={portalParentId}
      ref={(slide) => {
        if (slide) slideRefs.current[index] = slide;
      }}
    />
  ));

  const showLabels = slides.length > 1;

  return (
    <div className={s.content_overview}>
      <SectionHeader name={t("bookLanding.contentOverview")} />
      <ContentSliderWrapper
        slides={slides}
        slideRefs={slideRefs}
        className={s.slider}
        showLabels={showLabels}
      />
    </div>
  );
};

export default ContentOverview;
