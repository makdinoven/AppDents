import { FC, useState, JSX, useRef, useEffect } from "react";

import "swiper/swiper-bundle.css";
import s from "./HeroSlider.module.scss";
import {
  ArrowX,
  BackArrow,
  CircleArrowSmall,
} from "../../../../../assets/icons";
import ModalOverlay from "../../../../../components/Modals/ModalOverlay/ModalOverlay.tsx";
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
  const TABLET = 768;
  const [showArrow, setShowArrow] = useState({
    up: false,
    down: true,
    left: false,
    right: true,
  });
  const [isFullScreen, setIsFullScreen] = useState(false);
  const closeFullscreenRef = useRef<() => void>(null);

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

    setResultGallery(result);
  }, [gallery]);

  const renderGallery = (): JSX.Element => {
    return (
      <ul
        className={`${s.gallery} ${isFullScreen && s.full_screen}`}
        ref={galleryRef}
      >
        {resultGallery.map((item: any, index) => (
          <li
            key={item.url + index}
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
        ))}
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
    if (galleryRef.current) {
      const el = galleryRef.current;

      const isAtLeft = el.scrollLeft <= 5;
      const isAtRight = el.scrollWidth - el.clientWidth - el.scrollLeft <= 5;

      const isAtTop = el.scrollTop <= 5;
      const isAtBottom = el.scrollHeight - el.clientHeight - el.scrollTop <= 5;

      setShowArrow({
        up: !isAtTop,
        down: !isAtBottom,
        left: !isAtLeft,
        right: !isAtRight,
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

  const handleScroll = (direction: "prev" | "next") => {
    if (galleryRef.current) {
      const isMobile = screenWidth < MOBILE;
      const isTablet = screenWidth < TABLET;

      if (isMobile || (isTablet && isFullScreen)) {
        galleryRef.current.scrollBy({
          left: direction === "prev" ? -132 : 132,
          behavior: "smooth",
        });
      } else if (isFullScreen) {
        galleryRef.current.scrollBy({
          top: direction === "prev" ? -200 : 200,
          behavior: "smooth",
        });
      } else {
        galleryRef.current.scrollBy({
          top: direction === "prev" ? -132 : 132,
          behavior: "smooth",
        });
      }

      setTimeout(checkScrollPosition, 300);
    }
  };

  const handleFullScreen = (state: boolean) => {
    if (!state) {
      closeFullscreenRef.current?.();
    } else {
      setIsFullScreen(true);
    }
  };

  const goToPrev = () => {
    setActiveSlideIndex((prev) => {
      const newIndex = prev === 0 ? prev : prev - 1;
      const { url } = resultGallery[newIndex];
      setActiveUrl(url);
      return newIndex;
    });
  };
  const goToNext = () => {
    setActiveSlideIndex((prev) => {
      const newIndex = prev === gallery.length - 1 ? prev : prev + 1;
      const { url } = resultGallery[newIndex];
      setActiveUrl(url);
      return newIndex;
    });
  };

  const renderArrows = (
    type: "back" | "circle",
    content: JSX.Element | (() => JSX.Element),
  ) => {
    const renderedContent = typeof content === "function" ? content() : content;
    return type === "circle" ? (
      <>
        {(showArrow.up || showArrow.left) && (
          <CircleArrowSmall
            className={`${s.arrow_up} ${isFullScreen && s.full_screen}`}
            onClick={() => handleScroll("prev")}
          />
        )}
        {renderedContent}
        {(showArrow.down || showArrow.right) && (
          <CircleArrowSmall
            className={`${s.arrow_down} ${isFullScreen && s.full_screen}`}
            onClick={() => handleScroll("next")}
          />
        )}
      </>
    ) : (
      <>
        <button
          className={`${s.arrow_prev} ${activeSlideIndex === 0 && s.disabled}`}
          onClick={goToPrev}
        >
          <BackArrow />
        </button>
        {renderedContent}
        <button
          className={`${s.arrow_next} ${activeSlideIndex === gallery.length - 1 && s.disabled}`}
          onClick={goToNext}
        >
          <BackArrow />
        </button>
      </>
    );
  };

  const preview = (
    <div
      className={`${s.preview_photo} ${isFullScreen && s.full_screen}`}
      onClick={() => handleFullScreen(true)}
    >
      <img src={activeUrl} alt="preview" />
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

  const slider = (
    <div className={`${s.slider} ${isFullScreen && s.full_screen}`}>
      {needsArrows ? renderArrows("circle", renderGallery) : renderGallery()}
      <div className={`${s.preview_section} ${isFullScreen && s.full_screen}`}>
        {isFullScreen ? renderArrows("back", preview) : preview}
      </div>
      {isFullScreen && (
        <button className={s.close} onClick={() => handleFullScreen(false)}>
          <ArrowX />
        </button>
      )}
    </div>
  );

  return (
    <>
      <ModalOverlay
        isVisibleCondition={isFullScreen}
        modalPosition="top"
        customHandleClose={() => setIsFullScreen(false)}
        onInitClose={(fn) => (closeFullscreenRef.current = fn)}
      >
        <div className={s.modal}>{slider}</div>
      </ModalOverlay>
      {slider}
    </>
  );
};

export default HeroSlider;
