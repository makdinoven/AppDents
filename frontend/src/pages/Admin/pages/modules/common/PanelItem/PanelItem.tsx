import s from "./PanelItem.module.scss";
import { Link } from "react-router-dom";
import PrettyButton from "../../../../../../components/ui/PrettyButton/PrettyButton.tsx";
import ToggleCheckbox from "../../../../../../components/ui/ToggleCheckbox/ToggleCheckbox.tsx";

interface PanelItemType {
  name: string;
  link: string;
  handleToggle?: (value: number) => void;
  showToggle?: boolean;
  isHidden?: boolean;
  landingPath?: string;
  promoLandingPath?: string;
  id?: number;
}

const PanelItem = ({
  link,
  name,
  id,
  landingPath,
  promoLandingPath,
  handleToggle,
  isHidden,
  showToggle = false,
}: PanelItemType) => {
  const renderButtons = () => {
    return landingPath ? (
      <div className={s.buttons}>
        <Link to={link}>
          <PrettyButton text={"admin.update"} />
        </Link>
        <Link to={landingPath}>
          <PrettyButton variant={"primary"} text={"admin.view"} />
        </Link>
        {promoLandingPath && (
          <a href={promoLandingPath} target="_blank" rel="noopener noreferrer">
            <PrettyButton variant="default" text={"admin.promo"} />
          </a>
        )}
      </div>
    ) : (
      <Link to={link}>
        <PrettyButton text={"admin.update"} />
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
