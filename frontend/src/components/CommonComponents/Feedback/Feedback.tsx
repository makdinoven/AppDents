import s from "./Feedback.module.scss";
import { FeedbackLogo } from "../../../assets/logos/index";
import { Trans } from "react-i18next";

export const Feedback = () => {
  return (
    <div className={s.tooltip_wrapper}>
      <div className={s.feedback_tooltip}>
        <Trans i18nKey="feedbackTooltip" />
      </div>
      <div className={s.feedback_icon}>
        <FeedbackLogo />
      </div>
    </div>
  );
};

export default Feedback;
