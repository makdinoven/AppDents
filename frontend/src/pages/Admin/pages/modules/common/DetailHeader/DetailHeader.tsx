import s from "./DetailHeader.module.scss";
import { Trans } from "react-i18next";
import BackButton from "../../../../../../shared/components/ui/BackButton/BackButton.tsx";

const DetailHeader = ({
  title,
  link,
  showBackButton,
}: {
  title: string;
  link?: string;
  showBackButton?: boolean;
}) => {
  return (
    <div className={s.detail_header}>
      {showBackButton && <BackButton link={link} />}

      <h1>
        <Trans i18nKey={title} />
      </h1>
    </div>
  );
};

export default DetailHeader;
