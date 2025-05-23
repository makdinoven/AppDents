import s from "./ScrollToTopButton.module.scss";
import Arrow from "../../../assets/Icons/Arrow.tsx";
import { useScroll } from "../../../common/hooks/useScroll.ts";

const ScrollToTopButton = () => {
  const handleClick = () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const isScrolled = useScroll(1200);

  return (
    <button
      onClick={handleClick}
      className={`${s.scroll_btn} ${isScrolled ? s.show : ""}`}
    >
      <Arrow />
    </button>
  );
};

export default ScrollToTopButton;
