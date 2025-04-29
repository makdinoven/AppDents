import s from "./PaginationButton.module.scss";

const PaginationButton = ({
  onClick,
  pageNumber,
  activePage,
}: {
  onClick: () => void;
  pageNumber: number;
  activePage: number;
}) => {
  return (
    <button
      onClick={onClick}
      className={activePage === pageNumber ? s.activePage : ""}
    >
      {pageNumber}
    </button>
  );
};

export default PaginationButton;
