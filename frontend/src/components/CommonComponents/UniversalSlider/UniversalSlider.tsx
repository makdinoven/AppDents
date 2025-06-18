import { FC, ReactNode, useRef } from "react";
import { Swiper, SwiperSlide } from "swiper/react";
import { Autoplay, EffectFade, Navigation, Pagination } from "swiper/modules";
import "swiper/swiper-bundle.css";

import s from "./UniversalSlider.module.scss";
import BackArrow from "../../../assets/Icons/BackArrow.tsx";

type UniversalSliderProps = {
  slides: ReactNode[];
  autoplay?: boolean;
  loop?: boolean;
  pagination?: boolean;
  effect?: "slide" | "fade" | "cube" | "coverflow" | "flip";
  delay?: number;
  className?: string;
};

const UniversalSlider: FC<UniversalSliderProps> = ({
  slides,
  autoplay = false,
  loop = true,
  pagination = true,
  effect = "slide",
  delay = 5000,
  className = "",
}) => {
  const prevRef = useRef(null);
  const nextRef = useRef(null);

  return (
    <div className={s.slider}>
      <Swiper
        className={className}
        modules={[Autoplay, Pagination, Navigation, EffectFade]}
        loop={loop}
        navigation={{
          prevEl: prevRef.current,
          nextEl: nextRef.current,
        }}
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
                renderBullet: (_, className) =>
                  `<span class="${className}"><span class="progress"></span></span>`,
              }
            : false
        }
        autoplay={autoplay ? { delay, disableOnInteraction: false } : false}
        effect={effect}
      >
        {slides.map((slide, idx) => (
          <SwiperSlide className={s.slide} key={idx}>
            {slide}
          </SwiperSlide>
        ))}
      </Swiper>
      <div className={s.customNav}>
        <button ref={prevRef} className={s.prev}>
          <BackArrow />
        </button>
        <button ref={nextRef} className={s.next}>
          <BackArrow />
        </button>
      </div>
    </div>
  );
};

export default UniversalSlider;
