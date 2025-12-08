import s from "./FloatingTools.module.scss";
import { useScroll } from "../../common/hooks/useScroll.ts";
import ScrollToTopButton from "./modules/ScrollToTopButton/ScrollToTopButton.tsx";
import InteractionWidget from "./modules/InteractionWidget/InteractionWidget.tsx";

const FloatingTools = () => {
  const isScrolled = useScroll(1200);
  const isCompleted = false;
  return (
    <div className={s.floating_tools}>
      <div className={s.content}>
        <ScrollToTopButton isVisible={isScrolled} />
        <InteractionWidget isVisible={!isCompleted} isScrolled={isScrolled} />
      </div>
    </div>
  );
};
export default FloatingTools;
