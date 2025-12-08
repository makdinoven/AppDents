import s from "./FloatingTools.module.scss";
import { useScroll } from "../../common/hooks/useScroll.ts";
import ScrollToTopButton from "./modules/ScrollToTopButton/ScrollToTopButton.tsx";
import SurveyWidget from "./modules/SurveyWidget/SurveyWidget.tsx";

const FloatingTools = () => {
  const isScrolled = useScroll(1200);
  const isCompleted = false;
  return (
    <div className={s.floating_tools}>
      <div className={s.content}>
        <ScrollToTopButton isVisible={isScrolled} />
        <SurveyWidget isVisible={!isCompleted} isScrolled={isScrolled} />
      </div>
    </div>
  );
};
export default FloatingTools;
