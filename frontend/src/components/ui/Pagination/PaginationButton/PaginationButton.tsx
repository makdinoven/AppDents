import s from "./PaginationButton.module.scss";
import Arrow from "../../../../assets/Icons/Arrow.tsx";

const PaginationButton = ({
  onClick,
  pageNumber,
  activePage,
  variant = "default",
}: {
  onClick: () => void;
  pageNumber: number;
  activePage: number;
  variant?: "next" | "prev" | "default";
}) => {
  switch (variant) {
    case "next":
      return (
        <button
          onClick={onClick}
          className={`${s.navButton} ${s.navButtonArrow} ${s.nextNavButton}`}
        >
          <Arrow />
        </button>
      );
    case "prev":
      return (
        <button
          onClick={onClick}
          className={`${s.navButton} ${s.navButtonArrow} ${s.prevNavButton}`}
        >
          <Arrow />
        </button>
      );
    case "default":
      return (
        <button
          onClick={onClick}
          className={`${s.navButton} ${activePage === pageNumber ? s.activePage : ""}`}
        >
          {pageNumber}
        </button>
      );
  }
};

export default PaginationButton;
