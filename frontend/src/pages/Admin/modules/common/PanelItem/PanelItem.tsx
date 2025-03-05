import s from "./PanelItem.module.scss";
import { Link } from "react-router-dom";
import PrettyButton from "../../../../../components/ui/PrettyButton/PrettyButton.tsx";
import { t } from "i18next";

interface PanelItemType {
  name: string;
  link: string;
  id?: number;
}

const PanelItem = ({ link, name, id }: PanelItemType) => {
  return (
    <div className={s.item}>
      <div>
        {id && <span>{id}</span>} {name}
      </div>
      <Link to={link}>
        <PrettyButton text={t("update")} />
      </Link>
    </div>
  );
};

export default PanelItem;
