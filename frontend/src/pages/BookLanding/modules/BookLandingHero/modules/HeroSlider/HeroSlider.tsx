import { FC, useState, JSX, useRef, useEffect, useMemo } from "react";

import "swiper/swiper-bundle.css";
import s from "./HeroSlider.module.scss";
import { CircleArrowSmall } from "../../../../../../assets/icons";

type HeroSliderProps = {
  gallery: any[];
};

const HeroSlider: FC<HeroSliderProps> = ({ gallery }) => {
  const [activeUrl, setActiveUrl] = useState(gallery[0].url);
  const [activeSlideIndex, setActiveSlideIndex] = useState(0);
  const galleryRef = useRef<HTMLUListElement>(null);
  const [resultGallery, setResultGallery] = useState<any[]>([]);
  const firstItemRef = useRef<HTMLLIElement>(null);
  const lastItemRef = useRef<HTMLLIElement>(null);
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

  gallery = useMemo(
    () => [
      ...gallery,
      {
        id: Date.now(),
        url: "https://cdn.dent-s.com/images/book_landings/2/preview/ba52045d84174f4881be140905e8fa61.webp",
        alt: "string",
        caption: "string",
        sort_index: 0,
      },
      {
        id: Date.now(),
        url: "https://dent-s.com/assets/img/preview_img/da86fd0501ad4ff0954209ec345b3d3e.jpg",
        alt: "string",
        caption: "string",
        sort_index: 0,
      },
      {
        id: Date.now(),
        url: "https://cdn.dent-s.com/images/book_landings/2/preview/ba52045d84174f4881be140905e8fa611.webp",
        alt: "string",
        caption: "string",
        sort_index: 0,
      },
    ],
    [gallery],
  );

  // const needsArrows = gallery.length > 4;

  useEffect(() => {
    const result =
      gallery.length > 0
        ? gallery.map((photo, index) => ({
            index,
            url: photo.url,
            alt: photo.alt,
          }))
        : [];

    while (result.length < 4) {
      result.push({
        index: result.length,
        url: undefined,
        alt: undefined,
      });
    }

    setResultGallery(result);
  }, [gallery]);

  const renderGallery = (): JSX.Element => {
    return (
      <ul className={s.gallery} ref={galleryRef}>
        {resultGallery.map((item: any, index) =>
          item.url ? (
            <li
              key={item.url}
              onClick={() => handleSlideChange(item.index)}
              className={activeSlideIndex === item.index ? s.active : ""}
              ref={
                index === 0
                  ? firstItemRef
                  : index === resultGallery.length - 1
                    ? lastItemRef
                    : null
              }
            >
              <img src={item.url} alt={item.alt} />
            </li>
          ) : (
            <li key={item.index}>
              <div className={s.photo_placeholder} />
            </li>
          ),
        )}
      </ul>
    );
  };

  const handleSlideChange = (index: number) => {
    if (index < 0) {
      index = 0;
    } else if (index > resultGallery.length - 1) {
      index = resultGallery.length - 1;
    }
    const { url } = resultGallery[index];
    setActiveUrl(url);
    setActiveSlideIndex(index);
  };

  const handleScroll = (direction: "up" | "down") => {
    if (galleryRef.current) {
      const isMobile = screenWidth < MOBILE;

      if (isMobile) {
        galleryRef.current.scrollBy({
          left: direction === "up" ? -132 : 132,
          behavior: "smooth",
        });
      } else
        galleryRef.current.scrollBy({
          top: direction === "up" ? -132 : 132,
          behavior: "smooth",
        });
    }
  };

  return (
    <div className={s.slider}>
      <CircleArrowSmall className={s.up} onClick={() => handleScroll("up")} />
      {renderGallery()}
      <CircleArrowSmall
        className={s.down}
        onClick={() => handleScroll("down")}
      />
      <img src={activeUrl} alt="preview" className={s.preview_photo} />
      <div className={s.slide_indicators}>
        {Array(gallery.length)
          .fill({ length: gallery.length })
          .map((_, index) => (
            <div
              key={index}
              className={`${s.dot} ${activeSlideIndex === index ? s.active : ""}`}
              onClick={() => handleSlideChange(index)}
            />
          ))}
      </div>
    </div>
  );
};

export default HeroSlider;
