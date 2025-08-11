import { adminApi } from "../../../api/adminApi/adminApi";
import UniversalSlider from "../../ui/UniversalSlider/UniversalSlider";
import Slide from "./Slide/Slide";
import { useEffect, useState } from "react";
import { useSelector } from "react-redux";
import { AppRootStateType } from "../../../store/store";
import LoaderOverlay from "../../ui/LoaderOverlay/LoaderOverlay";
import Loader from "../../ui/Loader/Loader";

const MainSlider: React.FC = () => {
  const [screenWidth, setScreenWidth] = useState(window.innerWidth);
  const language = useSelector(
    (state: AppRootStateType) => state.user.language
  );
  const [loading, setLoading] = useState(false);
  const [slides, setSlides] = useState<any[]>([]);
  const TABLET_BREAKPOINT = 768;

  useEffect(() => {
    loadSlides(language);
  }, [language]);

  const loadSlides = async (language: string) => {
    try {
      setLoading(true);

      if (language) {
        const res = await adminApi.getSlides(language);

        const slidesList = res.data.slides
          .filter((slide: any) => slide.type !== "FREE")
          .map((slide: any) => <Slide key={slide.id} slideInfo={slide} />);

        setSlides(slidesList);
      }
    } catch (error) {
      console.log("Slides loading error:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const handleScreenResize = () => {
      setScreenWidth(window.innerWidth);
    };

    window.addEventListener("resize", handleScreenResize);

    handleScreenResize();

    return () => {
      window.removeEventListener("resize", handleScreenResize);
    };
  }, [screenWidth]);

  return (
    <>
      {loading && (
        <>
          <LoaderOverlay />
        </>
      )}
      {slides.length > 0 ? (
        <UniversalSlider
          autoplay
          slides={slides.filter(Boolean)}
          navigation
          navigationPosition="top-right"
          zoneNavigation={screenWidth < TABLET_BREAKPOINT}
          paginationPosition="top"
          theme="hero"
        />
      ) : (
        <Loader />
      )}
    </>
  );
};

export default MainSlider;
