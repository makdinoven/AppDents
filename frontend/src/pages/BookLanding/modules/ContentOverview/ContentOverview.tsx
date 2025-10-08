import React, { useRef, useState } from "react";
import s from "./ContentOverview.module.scss";
import ContentOverviewSlide, {
  ContentOverviewSlideRef,
} from "./modules/ContentOverviewSlide/ContentOverviewSlide.tsx";
import SectionHeader from "../../../../components/ui/SectionHeader/SectionHeader.tsx";
import ContentSliderWrapper from "./modules/ContentSliderWrapper/ContentSliderWrapper.tsx";
import { t } from "i18next";

interface ContentOverviewProps {
  books: any[];
  portalParentId: string;
}

const ContentOverview: React.FC<ContentOverviewProps> = ({
  books,
  portalParentId,
}: ContentOverviewProps) => {
  const [activeIndex, setActiveIndex] = useState(0);
  const slideRefs = useRef<ContentOverviewSlideRef[]>([]);

  const slides = books.map((book: any, index) => (
    <ContentOverviewSlide
      key={index}
      book={book}
      parentId={portalParentId}
      ref={(slide) => {
        if (slide) slideRefs.current[index] = slide;
      }}
      isActive={activeIndex === index}
      isSingle={!(books.length > 1)}
    />
  ));

  const showLabels = slides.length > 1;

  return (
    <div className={s.content_overview}>
      <SectionHeader name={t("bookLanding.contentOverview")} />
      <ContentSliderWrapper
        activeIndex={activeIndex}
        setActiveIndex={setActiveIndex}
        slides={slides}
        slideRefs={slideRefs}
        className={s.slider}
        showLabels={showLabels}
      />
    </div>
  );
};

export default ContentOverview;
