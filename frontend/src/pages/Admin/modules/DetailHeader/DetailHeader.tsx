import s from "./DetailHeader.module.scss";
import { Trans } from "react-i18next";
import PrettyButton from "../../../../components/ui/PrettyButton/PrettyButton.tsx";
import { useNavigate } from "react-router-dom";

const DetailHeader = ({ title }: { title: string }) => {
  const navigate = useNavigate();

  return (
    <div className={s.detail_header}>
      <PrettyButton text={"back"} onClick={() => navigate(-1)} />
      <h1>
        <Trans i18nKey={title} />
      </h1>
    </div>
  );
};

export default DetailHeader;
