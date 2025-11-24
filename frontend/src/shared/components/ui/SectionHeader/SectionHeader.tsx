import s from "./SectionHeader.module.scss";
import { Trans } from "react-i18next";

const SectionHeader = ({ name }: { name: string }) => {
  return (
    <div className={s.title_wrapper}>
      <h3>
        <Trans i18nKey={name} />
      </h3>
    </div>
  );
};

export default SectionHeader;
