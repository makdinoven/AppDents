import s from "./ModalCloseButton.module.scss";
import { ModalClose } from "../../../assets/icons";

const ModalCloseButton = ({
  className,
  onClick,
}: {
  className: string;
  onClick: any;
}) => {
  return (
    <button
      onClick={onClick}
      className={`${className ? className : ""} ${s.close_button}`}
    >
      <ModalClose />
    </button>
  );
};

export default ModalCloseButton;
