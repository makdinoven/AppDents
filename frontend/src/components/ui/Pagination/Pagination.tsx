import { useSearchParams } from "react-router-dom";
import s from "./Pagination.module.scss";
import { useEffect } from "react";

type PaginationProps = {
  page: number;
  setPage: (page: number) => void;
  totalPages: number;
};

const Pagination = ({ page, setPage, totalPages }: PaginationProps) => {
  const [searchParams, setSearchParams] = useSearchParams();

  useEffect(() => {
    const pageFromUrl = searchParams.get("page");
    if (pageFromUrl) {
      const pageNumber = parseInt(pageFromUrl, 10);
      if (!isNaN(pageNumber) && pageNumber >= 1 && pageNumber <= totalPages) {
        setPage(pageNumber);
      }
    }
  }, [searchParams, setPage, totalPages]);

  if (totalPages <= 1) return null;

  const changePage = (newPage: number) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setPage(newPage);
      setSearchParams({ page: newPage.toString() });
    }
  };

  const createButton = (pageNumber: number) => (
    <button
      key={pageNumber}
      onClick={() => changePage(pageNumber)}
      className={page === pageNumber ? s.activePage : ""}
    >
      {pageNumber}
    </button>
  );

  const createEllipsis = (key: string) => (
    <span key={key} className={s.ellipsis}>
      ...
    </span>
  );

  const startPage = Math.max(2, page - 1);
  const endPage = Math.min(totalPages - 1, page + 1);

  return (
    <div className={s.pagination_container}>
      {page > 1 && (
        <button onClick={() => changePage(page - 1)} className={s.navButton}>
          &lt;
        </button>
      )}

      {createButton(1)}

      {page > 3 && createEllipsis("start-ellipsis")}

      {Array.from({ length: endPage - startPage + 1 }, (_, idx) =>
        createButton(startPage + idx),
      )}

      {page < totalPages - 2 && createEllipsis("end-ellipsis")}

      {totalPages > 1 && createButton(totalPages)}

      {page < totalPages && (
        <button onClick={() => changePage(page + 1)} className={s.navButton}>
          &gt;
        </button>
      )}
    </div>
  );
};

export default Pagination;
