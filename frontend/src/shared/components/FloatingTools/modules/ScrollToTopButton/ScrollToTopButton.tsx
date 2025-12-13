import s from "./ScrollToTopButton.module.scss";
import { Arrow } from "../../../../assets/icons";

interface ScrollToTopButtonProps {
  isVisible: boolean;
  className: string;
}

const ScrollToTopButton = ({
  isVisible,
  className,
}: ScrollToTopButtonProps) => {
  const handleClick = () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <div
      onClick={handleClick}
      className={`${s.btn_wrapper} ${isVisible ? s.show : ""} ${className ? className : ""}`}
    >
      <button className={s.scroll_btn}>
        <Arrow />
      </button>
    </div>
  );
};

export default ScrollToTopButton;
