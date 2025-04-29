import s from "./Pagination.module.scss";
import Arrow from "../../../assets/Icons/Arrow.tsx";
import PaginationButton from "./PaginationButton/PaginationButton.tsx";

type PaginationProps = {
  page: number;
  setPage: (page: number) => void;
  totalPages: number;
};

const Pagination = ({ page, setPage, totalPages }: PaginationProps) => {
  if (totalPages <= 1) return null;

  const changePage = (newPage: number) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setPage(newPage);
    }
  };

  const createEllipsis = (key: string) => (
    <span key={key} className={s.ellipsis}>
      ...
    </span>
  );

  const startPage = Math.max(2, page - 1);
  const endPage = Math.min(totalPages - 1, page + 1);

  return (
    <div className={s.pagination_container}>
      <div className={s.pagination}>
        {page > 1 && (
          <button
            onClick={() => changePage(page - 1)}
            className={`${s.navButton} ${s.prevNavButton}`}
          >
            <Arrow />
          </button>
        )}

        <PaginationButton
          onClick={() => changePage(1)}
          pageNumber={1}
          activePage={page}
        />

        {page > 3 && createEllipsis("start-ellipsis")}

        {Array.from({ length: endPage - startPage + 1 }, (_, idx) => (
          <PaginationButton
            key={startPage + idx}
            onClick={() => changePage(startPage + idx)}
            pageNumber={startPage + idx}
            activePage={page}
          />
        ))}

        {page < totalPages - 2 && createEllipsis("end-ellipsis")}

        {totalPages > 1 && (
          <PaginationButton
            onClick={() => changePage(totalPages)}
            pageNumber={totalPages}
            activePage={page}
          />
        )}

        {page < totalPages && (
          <button
            onClick={() => changePage(page + 1)}
            className={`${s.navButton} ${s.nextNavButton}`}
          >
            <Arrow />
          </button>
        )}
      </div>
    </div>
  );
};

export default Pagination;
