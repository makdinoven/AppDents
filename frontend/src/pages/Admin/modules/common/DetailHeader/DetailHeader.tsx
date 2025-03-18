import s from "./DetailHeader.module.scss";
import { Trans } from "react-i18next";
import BackButton from "../../../../../components/ui/BackButton/BackButton.tsx";

const DetailHeader = ({ title }: { title: string }) => {
  return (
    <div className={s.detail_header}>
      <BackButton />
      <h1>
        <Trans i18nKey={title} />
      </h1>
    </div>
  );
};

export default DetailHeader;
