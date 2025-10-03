import React, { FC, useState, useRef, useEffect } from "react";
import UniversalSlider, {
  UniversalSliderProps,
  UniversalSliderRef,
} from "../../../../../../components/CommonComponents/UniversalSlider/UniversalSlider.tsx";
import s from "./ContentSliderWrapper.module.scss";
import { BackArrow } from "../../../../../../assets/icons";
import { ContentOverviewSlideRef } from "../ContentOverviewSlide/ContentOverviewSlide.tsx";

interface ContentSliderWrapperProps
  extends Omit<
    UniversalSliderProps,
    "navigation" | "navigationType" | "pagination" | "paginationType"
  > {
  slides: React.ReactNode[];
  slideRefs: React.RefObject<ContentOverviewSlideRef[]>;
  showLabels?: boolean;
}

const ContentSliderWrapper: FC<ContentSliderWrapperProps> = ({
  slides,
  slideRefs,
  showLabels = false,
  ...props
}) => {
  const [activeIndex, setActiveIndex] = useState(0);
  const [isRefsReady, setIsRefsReady] = useState(false);
  const sliderRef = useRef<UniversalSliderRef>(null);

  const prevIndex = activeIndex > 0 ? activeIndex - 1 : 0;
  const nextIndex =
    activeIndex < slides.length - 1 ? activeIndex + 1 : slides.length - 1;

  const prevSlide = slideRefs.current[prevIndex];
  const nextSlide = slideRefs.current[nextIndex];

  useEffect(() => {
    if (slideRefs.current && slideRefs.current.length > 0) {
      setIsRefsReady(true);
    }
  }, [slideRefs]);

  return (
    <div className={s.content_slider_wrapper}>
      <UniversalSlider
        {...props}
        slides={slides}
        navigation={false}
        onSlideChange={setActiveIndex}
        pagination={false}
        ref={sliderRef}
      />
      {showLabels && isRefsReady && (
        <div className={s.custom_nav}>
          {prevSlide && (
            <button
              className={`${s.prev} ${activeIndex > 0 && s.hidden}`}
              onClick={() => sliderRef.current?.slidePrev()}
            >
              <span className={s.label}>{prevSlide?.title}</span>
              <BackArrow />
            </button>
          )}
          {nextSlide && (
            <button
              className={`${s.next} ${activeIndex < slides.length - 1 && s.hidden}`}
              onClick={() => sliderRef.current?.slideNext()}
            >
              <span className={s.label}>{nextSlide?.title}</span>
              <BackArrow />
            </button>
          )}
        </div>
      )}
    </div>
  );
};

export default ContentSliderWrapper;
