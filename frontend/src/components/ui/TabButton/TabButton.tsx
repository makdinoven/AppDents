import s from "./TabButton.module.scss";

interface TabButtonProps {
  text: string;
  isActive?: boolean;
  onClick?: () => void;
}

const TabButton = ({ onClick, text, isActive }: TabButtonProps) => {
  return (
    <button
      onClick={onClick}
      className={`${s.btn} ${isActive ? s.active : ""}`}
    >
      {text}
    </button>
  );
};
export default TabButton;
