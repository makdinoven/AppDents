import s from "./Feedback.module.scss";
import { Trans } from "react-i18next";
import { FeedbackIcon } from "../../assets/icons";

export const Feedback = () => {
  return (
    <div className={s.tooltip_wrapper}>
      <div className={s.feedback_tooltip}>
        <Trans i18nKey="feedbackTooltip" />
      </div>
      <div className={s.feedback_icon}>
        <FeedbackIcon />
      </div>
    </div>
  );
};

export default Feedback;
