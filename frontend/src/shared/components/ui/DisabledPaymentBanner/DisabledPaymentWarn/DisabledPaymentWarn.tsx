import s from "./DisabledPaymentWarn.module.scss";
import { Trans } from "react-i18next";
import { ErrorIcon } from "../../../../assets/icons";

const DisabledPaymentWarn = () => {
  return (
    <div className={s.warn}>
      <div className={s.warn_title_container}>
        <ErrorIcon />
        <p>
          <Trans i18nKey={"disabledPayment.title"} />
        </p>
      </div>
      <p>
        <Trans i18nKey={"disabledPayment.date"} />.{" "}
        <Trans i18nKey={"disabledPayment.boughtCourses"} />
      </p>
    </div>
  );
};

export default DisabledPaymentWarn;
