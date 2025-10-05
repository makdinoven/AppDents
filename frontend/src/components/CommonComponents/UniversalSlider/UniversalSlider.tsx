import { forwardRef, ReactNode, useImperativeHandle, useRef } from "react";
import { Swiper, SwiperSlide } from "swiper/react";
import { Autoplay, EffectFade, Navigation, Pagination } from "swiper/modules";
import "swiper/swiper-bundle.css";

import s from "./UniversalSlider.module.scss";
import { BackArrow } from "../../../assets/icons";

export type UniversalSliderProps = {
  slides: ReactNode[];
  autoplay?: boolean;
  loop?: boolean;
  pagination?: boolean;
  navigation?: boolean;
  allowTouchMove?: boolean;
  effect?: "slide" | "fade" | "cube" | "coverflow" | "flip";
  paginationType?: "story" | "dots";
  slidesPerView?: number | "auto";
  delay?: number;
  className?: string;
  isFullWidth?: boolean;
  navigationPosition?: "center" | "bottom";
  onSlideChange?: (activeIndex: number) => void;
};

export interface UniversalSliderRef {
  slidePrev: () => void;
  slideNext: () => void;
}

const UniversalSlider = forwardRef<UniversalSliderRef, UniversalSliderProps>(
  (
    {
      slides,
      allowTouchMove,
      autoplay = false,
      loop = true,
      pagination = true,
      navigation,
      paginationType = "story",
      slidesPerView = 1,
      effect = "slide",
      navigationPosition = "center",
      delay = 5000,
      className = "",
      isFullWidth = false,
      onSlideChange,
    },
    ref,
  ) => {
    const prevRef = useRef(null);
    const nextRef = useRef(null);
    const swiperRef = useRef<any>(null);

    useImperativeHandle(ref, () => ({
      slidePrev: () => swiperRef.current?.slidePrev(),
      slideNext: () => swiperRef.current?.slideNext(),
    }));

    return (
      <div
        style={{
          width: isFullWidth ? `100vw` : "100%",
          left: isFullWidth ? `-10px` : "",
        }}
        className={s.slider}
      >
        <Swiper
          autoHeight={false}
          allowTouchMove={allowTouchMove}
          className={className}
          modules={[Autoplay, Pagination, Navigation, EffectFade]}
          loop={loop}
          navigation={{
            prevEl: prevRef.current,
            nextEl: nextRef.current,
          }}
          slidesPerView={slidesPerView}
          centeredSlides
          onBeforeInit={(swiper) => {
            if (
              swiper.params.navigation &&
              typeof swiper.params.navigation !== "boolean"
            ) {
              swiper.params.navigation.prevEl = prevRef.current;
              swiper.params.navigation.nextEl = nextRef.current;
            }
          }}
          pagination={
            pagination
              ? {
                  clickable: true,
                  renderBullet: (_, className) => {
                    const isStory = paginationType === "story";
                    const innerSpan = isStory
                      ? `<span class="${autoplay ? "progress" : "filled"}"></span>`
                      : "";
                    return `<span class="${className} ${paginationType}">${innerSpan}</span>`;
                  },
                }
              : false
          }
          autoplay={autoplay ? { delay, disableOnInteraction: false } : false}
          effect={effect}
          onSlideChange={(swiper) => onSlideChange?.(swiper.realIndex)}
          onSwiper={(swiper) => (swiperRef.current = swiper)}
        >
          {slides.map((slide, idx) => (
            <SwiperSlide className={s.slide} key={idx}>
              {slide}
            </SwiperSlide>
          ))}
        </Swiper>
        {navigation && (
          <div className={`${s.customNav} ${s[navigationPosition]}`}>
            <button ref={prevRef} className={s.prev}>
              <BackArrow />
            </button>
            <button ref={nextRef} className={s.next}>
              <BackArrow />
            </button>
          </div>
        )}
      </div>
    );
  },
);

export default UniversalSlider;
