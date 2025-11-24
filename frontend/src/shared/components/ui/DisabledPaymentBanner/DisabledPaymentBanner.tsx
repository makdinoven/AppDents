import s from "./DisabledPaymentBanner.module.scss";
import { Trans } from "react-i18next";
import { ErrorIcon } from "../../../assets/icons";

const DisabledPaymentBanner = () => {
  return (
    <div id={"disabled-payment-banner"} className={s.banner_wrapper}>
      <div className={s.banner}>
        <div className={s.title_wrapper}>
          <ErrorIcon />
          <h4>
            <Trans i18nKey={"disabledPayment.title"} />
          </h4>
          <ErrorIcon />
        </div>

        <p>
          <Trans i18nKey={"disabledPayment.date"} />
        </p>
        <p className={s.line_text}>
          <Trans i18nKey={"disabledPayment.boughtCourses"} />
        </p>
        <p>
          <Trans i18nKey={"disabledPayment.sorry"} />
        </p>
      </div>
    </div>
  );
};

export default DisabledPaymentBanner;
