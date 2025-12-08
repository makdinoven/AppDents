import s from "./ScrollToTopButton.module.scss";
import { Arrow } from "../../../../assets/icons";

const ScrollToTopButton = ({ isVisible }: { isVisible: boolean }) => {
  const handleClick = () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <div
      onClick={handleClick}
      className={`${s.btn_wrapper} ${isVisible ? s.show : ""}`}
    >
      <button className={s.scroll_btn}>
        <Arrow />
      </button>
    </div>
  );
};

export default ScrollToTopButton;
