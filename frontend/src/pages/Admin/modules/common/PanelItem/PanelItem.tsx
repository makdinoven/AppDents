import s from "./PanelItem.module.scss";
import { Link } from "react-router-dom";
import PrettyButton from "../../../../../components/ui/PrettyButton/PrettyButton.tsx";
import { t } from "i18next";
import ToggleCheckbox from "../../../../../components/ui/ToggleCheckbox/ToggleCheckbox.tsx";

interface PanelItemType {
  name: string;
  link: string;
  handleToggle?: (value: number) => void;
  showToggle?: boolean;
  isHidden?: boolean;
  landingPath?: string;
  id?: number;
}

const PanelItem = ({
  link,
  name,
  id,
  landingPath,
  handleToggle,
  isHidden,
  showToggle = false,
}: PanelItemType) => {
  const renderButtons = () => {
    return landingPath ? (
      <div className={s.buttons}>
        <Link to={link}>
          <PrettyButton text={t("admin.update")} />
        </Link>
        <Link to={landingPath}>
          <PrettyButton variant={"primary"} text={t("admin.view")} />
        </Link>
      </div>
    ) : (
      <Link to={link}>
        <PrettyButton text={t("admin.update")} />
      </Link>
    );
  };

  return (
    <div className={s.item}>
      <div>
        {id && (
          <span>
            {showToggle && (
              <ToggleCheckbox
                isChecked={!isHidden}
                onChange={() => handleToggle && handleToggle(id)}
              />
            )}
            {id}
          </span>
        )}{" "}
        {name}
      </div>
      {renderButtons()}
    </div>
  );
};

export default PanelItem;
