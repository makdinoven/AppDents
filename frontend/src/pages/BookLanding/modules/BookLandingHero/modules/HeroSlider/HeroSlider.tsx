import { FC, useState, JSX, useRef, useEffect } from "react";

import "swiper/swiper-bundle.css";
import s from "./HeroSlider.module.scss";
import { CircleArrowSmall } from "../../../../../../assets/icons";
import ModalOverlay from "../../../../../../components/Modals/ModalOverlay/ModalOverlay.tsx";

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
  const [showArrow, setShowArrow] = useState({
    up: false,
    down: true,
  });
  const [isFullScreen, setIsFullScreen] = useState(false);

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

  const needsArrows = gallery.length > 4;

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
      <ul
        className={`${s.gallery} ${isFullScreen && s.full_screen}`}
        ref={galleryRef}
      >
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

  const checkScrollPosition = () => {
    if (galleryRef.current && firstItemRef.current && lastItemRef.current) {
      const galleryRect = galleryRef.current.getBoundingClientRect();
      const firstItemRect = firstItemRef.current.getBoundingClientRect();
      const lastItemRect = lastItemRef.current.getBoundingClientRect();

      const isFirstItemAtTop =
        Math.abs(firstItemRect.top - galleryRect.top) < 5;

      const isLastItemAtBottom =
        Math.abs(lastItemRect.bottom - galleryRect.bottom) < 5;

      setShowArrow({
        up: !isFirstItemAtTop,
        down: !isLastItemAtBottom,
      });
    }
  };

  useEffect(() => {
    const gallery = galleryRef.current;
    if (gallery) {
      gallery.addEventListener("scroll", checkScrollPosition);
      checkScrollPosition();

      return () => gallery.removeEventListener("scroll", checkScrollPosition);
    }
  }, []);

  const handleScroll = (direction: "up" | "down") => {
    if (galleryRef.current) {
      const isMobile = screenWidth < MOBILE;

      if (isMobile) {
        galleryRef.current.scrollBy({
          left: direction === "up" ? -132 : 132,
          behavior: "smooth",
        });
      } else {
        galleryRef.current.scrollBy({
          top: direction === "up" ? -132 : 132,
          behavior: "smooth",
        });
      }

      setTimeout(checkScrollPosition, 300);
    }
  };

  const handleOpenFullScreen = () => {
    setIsFullScreen((prev) => !prev);
  };

  const slider = (
    <div className={`${s.slider} ${isFullScreen && s.full_screen}`}>
      {needsArrows && showArrow.up && (
        <CircleArrowSmall className={s.up} onClick={() => handleScroll("up")} />
      )}
      {renderGallery()}
      {needsArrows && showArrow.down && (
        <CircleArrowSmall
          className={s.down}
          onClick={() => handleScroll("down")}
        />
      )}
      <img
        src={activeUrl}
        alt="preview"
        className={`${s.preview_photo} ${isFullScreen && s.full_screen}`}
        onClick={handleOpenFullScreen}
      />
      <div className={`${s.slide_indicators} ${isFullScreen && s.full_screen}`}>
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

  return isFullScreen ? (
    <ModalOverlay
      isVisibleCondition={isFullScreen}
      modalPosition="top"
      customHandleClose={handleOpenFullScreen}
    >
      <div className={s.modal}>{slider}</div>
    </ModalOverlay>
  ) : (
    <>{slider}</>
  );
};

export default HeroSlider;
