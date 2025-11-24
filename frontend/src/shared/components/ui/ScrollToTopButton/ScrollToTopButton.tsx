import s from "./ScrollToTopButton.module.scss";
import { Arrow } from "../../../assets/icons";

import { useScroll } from "../../../common/hooks/useScroll.ts";

const ScrollToTopButton = () => {
  const handleClick = () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const isScrolled = useScroll(1200);

  return (
    <div
      onClick={handleClick}
      className={`${s.btn_wrapper} ${isScrolled ? s.show : ""}`}
    >
      <button className={s.scroll_btn}>
        <Arrow />
      </button>
    </div>
  );
};

export default ScrollToTopButton;
