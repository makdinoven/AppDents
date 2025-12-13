import s from "./FloatingTools.module.scss";
import { useScroll } from "../../common/hooks/useScroll.ts";
import ScrollToTopButton from "./modules/ScrollToTopButton/ScrollToTopButton.tsx";
import SurveyWidget from "./modules/SurveyWidget/SurveyWidget.tsx";
import { useState } from "react";

const FloatingTools = () => {
  const isScrolled = useScroll(1200);
  const [showSurvey, setShowSurvey] = useState(false);

  return (
    <div className={s.floating_tools}>
      <div className={s.content}>
        <ScrollToTopButton
          isVisible={isScrolled}
          className={showSurvey ? s.translate : ""}
        />
        <SurveyWidget
          isScrolled={isScrolled}
          callback={(survey) => setShowSurvey(survey)}
        />
      </div>
    </div>
  );
};
export default FloatingTools;
