import s from "./Pagination.module.scss";
import PaginationButton from "./PaginationButton/PaginationButton.tsx";
import { PAGE_SIZES } from "../../../common/helpers/commonConstants.ts";
import { t } from "i18next";
import MultiSelect from "../../ui/MultiSelect/MultiSelect.tsx";

export type PaginationType = {
  page: number;
  size: number;
  total: number;
  total_pages: number;
};

type PaginationProps = {
  pagination: PaginationType;
  onPageChange: (p: number) => void;
  onSizeChange: (sz: number) => void;
};

const Pagination = ({
  pagination,
  onPageChange,
  onSizeChange,
}: PaginationProps) => {
  const { page, total_pages: totalPages, size, total } = pagination;

  const createEllipsis = (key: string) => (
    <span key={key} className={s.ellipsis}>
      ...
    </span>
  );

  const startPage = Math.max(2, page - 1);
  const endPage = Math.min(totalPages - 1, page + 1);

  const handleChangePage = (p: number) => {
    onPageChange(p);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <div className={s.pagination_container}>
      <div className={s.size_container}>
        <MultiSelect
          isSearchable={false}
          placeholder={""}
          isMultiple={false}
          valueKey={"value" as const}
          labelKey={"name" as const}
          options={PAGE_SIZES}
          id={"page"}
          selectedValue={size.toString()}
          onChange={(e) => onSizeChange(Number(e.value as string))}
        />
      </div>

      <div className={s.pagination}>
        <PaginationButton
          disabled={page === 1}
          onClick={() => handleChangePage(page - 1)}
          pageNumber={totalPages}
          activePage={page}
          variant={"prev"}
        />
        <div className={s.pagination_buttons}>
          <PaginationButton
            onClick={() => handleChangePage(1)}
            pageNumber={1}
            activePage={page}
          />
          {page > 3 && createEllipsis("start-ellipsis")}
          {Array.from({ length: endPage - startPage + 1 }, (_, idx) => (
            <PaginationButton
              key={startPage + idx}
              onClick={() => handleChangePage(startPage + idx)}
              pageNumber={startPage + idx}
              activePage={page}
            />
          ))}
          {page < totalPages - 2 && createEllipsis("end-ellipsis")}
          {totalPages > 1 && (
            <PaginationButton
              onClick={() => handleChangePage(totalPages)}
              pageNumber={totalPages}
              activePage={page}
            />
          )}
        </div>
        <PaginationButton
          disabled={page === totalPages}
          onClick={() => handleChangePage(page + 1)}
          pageNumber={totalPages}
          activePage={page}
          variant={"next"}
        />
      </div>

      <span className={s.showing}>
        {total !== 0 &&
          `${(page - 1) * size + 1}-${Math.min(page * size, total)} ${t("of")} ${total}`}
      </span>
    </div>
  );
};

export default Pagination;
