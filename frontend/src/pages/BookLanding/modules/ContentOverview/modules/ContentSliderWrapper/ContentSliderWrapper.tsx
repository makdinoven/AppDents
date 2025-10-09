import React, { FC, useEffect, useRef, useState } from "react";
import UniversalSlider, {
  UniversalSliderProps,
  UniversalSliderRef,
} from "../../../../../../components/CommonComponents/UniversalSlider/UniversalSlider.tsx";
import s from "./ContentSliderWrapper.module.scss";
import { BackArrow } from "../../../../../../assets/icons";
import { ContentOverviewSlideRef } from "../ContentOverviewSlide/ContentOverviewSlide.tsx";
import { useScreenWidth } from "../../../../../../common/hooks/useScreenWidth.ts";

interface ContentSliderWrapperProps
  extends Omit<
    UniversalSliderProps,
    "navigation" | "navigationType" | "pagination" | "paginationType"
  > {
  slides: React.ReactNode[];
  slideRefs: React.RefObject<ContentOverviewSlideRef[]>;
  showLabels?: boolean;
  activeIndex: number;
  setActiveIndex: (index: number) => void;
}

const ContentSliderWrapper: FC<ContentSliderWrapperProps> = ({
  slides,
  slideRefs,
  showLabels = false,
  activeIndex,
  setActiveIndex,
  ...props
}) => {
  const screenWidth = useScreenWidth();
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
        allowTouchMove={screenWidth <= 768}
        loop={false}
      />
      {showLabels && isRefsReady && (
        <div className={s.custom_nav}>
          {prevSlide && activeIndex > 0 && (
            <button
              className={s.prev}
              onClick={() => sliderRef.current?.slidePrev()}
            >
              <BackArrow />
              <span className={s.label}>{prevSlide?.title}</span>
            </button>
          )}

          {nextSlide && activeIndex < slides.length - 1 && (
            <button
              className={s.next}
              onClick={() => sliderRef.current?.slideNext()}
            >
              <span className={s.label}>{nextSlide?.title}</span>
              <BackArrow className={s.iconRotated} /> {/* или rotate: 180deg */}
            </button>
          )}
        </div>
      )}
    </div>
  );
};

export default ContentSliderWrapper;
