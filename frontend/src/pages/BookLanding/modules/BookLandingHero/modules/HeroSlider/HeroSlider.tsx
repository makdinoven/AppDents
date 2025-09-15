import { FC, ReactNode, useRef, useState, useEffect } from "react";
import { Swiper, SwiperSlide } from "swiper/react";
import { Navigation, Pagination, Thumbs } from "swiper/modules";
import "swiper/swiper-bundle.css";
import s from "./HeroSlider.module.scss";

type HeroSliderProps = {
  slides: ReactNode[];
  className?: string;
};

const HeroSlider: FC<HeroSliderProps> = ({ slides, className = "" }) => {
  const prevRef = useRef(null);
  const nextRef = useRef(null);
  const [thumbsSwiper, setThumbsSwiper] = useState<any>(null);
  const [screenWidth, setScreenWidth] = useState(window.innerWidth);
  const MOBILE = 576;

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

  return (
    <div className={s.slider}>
      <Swiper
        onSwiper={setThumbsSwiper}
        modules={[Thumbs]}
        watchSlidesProgress
        slidesPerView={4}
        direction={screenWidth > MOBILE ? "vertical" : "horizontal"}
        className={s.thumbs}
      >
        {slides?.map((slide, idx) => (
          <SwiperSlide key={idx} className={s.thumb}>
            {slide}
          </SwiperSlide>
        ))}
      </Swiper>{" "}
      <Swiper
        autoHeight={false}
        className={className}
        modules={[Pagination, Navigation, Thumbs]}
        navigation={{
          prevEl: prevRef.current,
          nextEl: nextRef.current,
        }}
        slidesPerView={1}
        centeredSlides
        direction="vertical"
        onBeforeInit={(swiper) => {
          if (
            swiper.params.navigation &&
            typeof swiper.params.navigation !== "boolean"
          ) {
            swiper.params.navigation.prevEl = prevRef.current;
            swiper.params.navigation.nextEl = nextRef.current;
          }
        }}
        pagination={{
          clickable: true,
          renderBullet: (_, className) => {
            return `<span class="${className}"></span>`;
          },
        }}
        autoplay={false}
        effect="slider"
        speed={0}
        thumbs={{ swiper: thumbsSwiper }}
      >
        {slides?.map((slide, idx) => (
          <SwiperSlide className={s.slide} key={idx}>
            {slide}
          </SwiperSlide>
        ))}
      </Swiper>
    </div>
  );
};

export default HeroSlider;
