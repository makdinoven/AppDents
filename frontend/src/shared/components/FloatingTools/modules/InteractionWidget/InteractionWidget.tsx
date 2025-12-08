import s from "./InteractionWidget.module.scss";
import { Interaction } from "../../../../assets/icons";

interface InteractionWidgetProps {
  isVisible: boolean;
  isScrolled: boolean;
}

const InteractionWidget = ({
  isVisible,
  isScrolled,
}: InteractionWidgetProps) => {
  const handleOpenInteractionForm = () => {};
  return (
    isVisible && (
      <div
        className={`${s.btn_wrapper} ${isScrolled ? s.shift : ""}`}
        onClick={() => handleOpenInteractionForm()}
      >
        <button className={s.interaction_btn}>
          <Interaction />
        </button>
      </div>
    )
  );
};
export default InteractionWidget;
