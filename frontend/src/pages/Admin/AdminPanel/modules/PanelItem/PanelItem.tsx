import s from "./PanelItem.module.scss";
import { Link } from "react-router-dom";
import PrettyButton from "../../../../../components/ui/PrettyButton/PrettyButton.tsx";
import { t } from "i18next";

interface PanelItemType {
  name: string;
  link: string;
}

const PanelItem = ({ link, name }: PanelItemType) => {
  return (
    <div className={s.item}>
      {name}
      <Link to={link}>
        <PrettyButton text={t("update")} />
      </Link>
    </div>
  );
};

export default PanelItem;
