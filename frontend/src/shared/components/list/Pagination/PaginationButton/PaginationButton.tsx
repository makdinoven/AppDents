import s from "./PaginationButton.module.scss";
import { BackArrow } from "../../../../assets/icons";

const PaginationButton = ({
  disabled,
  onClick,
  pageNumber,
  activePage,
  variant = "default",
}: {
  disabled?: boolean;
  onClick: () => void;
  pageNumber: number;
  activePage: number;
  variant?: "next" | "prev" | "default";
}) => {
  const isActive = activePage === pageNumber;

  switch (variant) {
    case "next":
      return (
        <button
          onClick={onClick}
          className={`${s.navButton} ${s.navButtonArrow} ${s.nextNavButton} ${disabled ? s.disabled : ""}`}
        >
          <BackArrow />
        </button>
      );
    case "prev":
      return (
        <button
          onClick={onClick}
          className={`${s.navButton} ${s.navButtonArrow} ${s.prevNavButton} ${disabled ? s.disabled : ""}`}
        >
          <BackArrow />
        </button>
      );
    case "default":
      return (
        <button
          onClick={isActive ? undefined : onClick}
          className={`${s.navButton} ${isActive ? s.activePage : ""}`}
        >
          {pageNumber}
        </button>
      );
  }
};

export default PaginationButton;
