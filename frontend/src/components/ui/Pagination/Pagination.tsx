import { useSearchParams } from "react-router-dom";
import s from "./Pagination.module.scss";
import PaginationButton from "./PaginationButton/PaginationButton.tsx";

type PaginationProps = {
  totalPages: number;
};

const Pagination = ({ totalPages }: PaginationProps) => {
  const [searchParams, setSearchParams] = useSearchParams();
  const page = parseInt(searchParams.get("page") || "1", 10);

  if (totalPages <= 1) return null;

  const changePage = (newPage: number) => {
    if (newPage >= 1 && newPage <= totalPages) {
      const newParams = new URLSearchParams(searchParams);
      newParams.set("page", newPage.toString());
      setSearchParams(newParams);
      window.scrollTo({ top: 0 });
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
          <PaginationButton
            onClick={() => changePage(page - 1)}
            pageNumber={totalPages}
            activePage={page}
            variant={"prev"}
          />
        )}
        <div className={s.pagination_buttons}>
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
        </div>
        {page < totalPages && (
          <PaginationButton
            onClick={() => changePage(page + 1)}
            pageNumber={totalPages}
            activePage={page}
            variant={"next"}
          />
        )}
      </div>
    </div>
  );
};

export default Pagination;
