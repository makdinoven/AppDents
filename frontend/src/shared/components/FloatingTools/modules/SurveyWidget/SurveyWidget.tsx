import s from "./SurveyWidget.module.scss";
import { Interaction } from "../../../../assets/icons";
import { Trans } from "react-i18next";
import { useSearchParams } from "react-router-dom";

interface InteractionWidgetProps {
  isVisible: boolean;
  isScrolled: boolean;
}

const SurveyWidget = ({ isVisible, isScrolled }: InteractionWidgetProps) => {
  const [searchParams, setSearchParams] = useSearchParams();

  console.log(searchParams);

  const handleOpenSurvey = () => {
    const openSurvey = new URLSearchParams(searchParams);
    openSurvey.set("open-survey", "");
    setSearchParams(openSurvey);
  };

  return (
    isVisible && (
      <div className={`${s.survey_widget} ${isScrolled ? s.shift : ""}`}>
        <div className={s.btn_wrapper} onClick={() => handleOpenSurvey()}>
          <button className={s.survey_btn}>
            <Interaction />
          </button>
        </div>
        <div className={s.survey_text}>
          <span>
            <Trans i18nKey="survey.crowdFunding.title" />
          </span>
        </div>
      </div>
    )
  );
};
export default SurveyWidget;
