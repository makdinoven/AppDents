import s from "./PaginationButton.module.scss";
import BackArrow from "../../../../assets/Icons/BackArrow.tsx";

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
          <BackArrow />
        </button>
      );
    case "prev":
      return (
        <button
          onClick={onClick}
          className={`${s.navButton} ${s.navButtonArrow} ${s.prevNavButton}`}
        >
          <BackArrow />
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
