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
  navigation?: boolean;
  effect?: "slide" | "fade" | "cube" | "coverflow" | "flip";
  paginationType?: "story" | "dots";
  paginationColor?: "white" | "primary";
  slidesPerView?: number | "auto";
  delay?: number;
  className?: string;
  isFullWidth?: boolean;
  navigationPosition?: "center" | "bottom";
  navigationClassname?: string;
};

const UniversalSlider: FC<UniversalSliderProps> = ({
  slides,
  autoplay = false,
  loop = true,
  pagination = true,
  navigation,
  paginationType = "story",
  slidesPerView = 1,
  effect = "slide",
  navigationPosition = "center",
  paginationColor = "primary",
  delay = 5000,
  className = "",
  isFullWidth = false,
  navigationClassname,
}) => {
  const prevRef = useRef(null);
  const nextRef = useRef(null);

  return (
    <div
      style={{
        width: isFullWidth ? `100vw` : "100%",
        left: isFullWidth ? `-20px` : "",
      }}
      className={s.slider}
    >
      <Swiper
        autoHeight={false}
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
                  return `<span class="${className} ${paginationType} ${paginationColor}">${innerSpan}</span>`;
                },
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
      {navigation && (
        <div
          className={[s.customNav, s[navigationPosition], navigationClassname]
            .filter(Boolean)
            .join(" ")}
        >
          <button ref={prevRef} className={s.prev}>
            <BackArrow strokeWidth={1} />
          </button>
          <button ref={nextRef} className={s.next}>
            <BackArrow strokeWidth={1} />
          </button>
        </div>
      )}
    </div>
  );
};

export default UniversalSlider;
