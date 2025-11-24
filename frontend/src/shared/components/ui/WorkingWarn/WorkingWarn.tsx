import s from "./WokingWarn.module.scss";
import { Trans } from "react-i18next";

const WorkingWarn = () => {
  return (
    <div className={s.working_warn}>
      <h2>
        <Trans i18nKey={"workingWarn.title"} />
      </h2>
      <p>
        <Trans i18nKey={"workingWarn.first"} />
      </p>
      <p>
        <Trans i18nKey={"workingWarn.second"} />
      </p>
      <p>
        <Trans i18nKey={"workingWarn.third"} />
      </p>
      <p>
        <Trans i18nKey={"workingWarn.fourth"} />
      </p>
      <p>
        <Trans i18nKey={"workingWarn.last"} />
      </p>
    </div>
  );
};

export default WorkingWarn;
