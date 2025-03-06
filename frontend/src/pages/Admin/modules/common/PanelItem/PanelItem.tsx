import s from "./PanelItem.module.scss";
import { Link } from "react-router-dom";
import PrettyButton from "../../../../../components/ui/PrettyButton/PrettyButton.tsx";
import { t } from "i18next";

interface PanelItemType {
  name: string;
  link: string;
  landingPath?: string;
  id?: number;
}

const PanelItem = ({ link, name, id, landingPath }: PanelItemType) => {
  const renderButtons = () => {
    return landingPath ? (
      <div className={s.buttons}>
        <Link to={link}>
          <PrettyButton text={t("update")} />
        </Link>
        <Link to={landingPath}>
          <PrettyButton variant={"primary"} text={t("view")} />
        </Link>
      </div>
    ) : (
      <Link to={link}>
        <PrettyButton text={t("update")} />
      </Link>
    );
  };

  return (
    <div className={s.item}>
      <div>
        {id && <span>{id}</span>} {name}
      </div>
      {renderButtons()}
    </div>
  );
};

export default PanelItem;
