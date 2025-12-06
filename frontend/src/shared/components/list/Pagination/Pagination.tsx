import s from "./Pagination.module.scss";
import PaginationButton from "./PaginationButton/PaginationButton.tsx";
import { PAGE_SIZES } from "../../../common/helpers/commonConstants.ts";
import { t } from "i18next";
import Select from "../../ui/Select/Select.tsx";
import FilterChip from "../../filters/FilterChip/FilterChip.tsx";

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
        <Select
          options={PAGE_SIZES}
          renderTrigger={(open) => (
            <FilterChip
              variant={"dropdown"}
              text={size.toString()}
              isActive={open}
              className={`${s.sort_button} ${open ? s.open : ""}`}
            />
          )}
          subtitle={t("pagination.pageSize")}
          radioButtonType="radio"
          onChange={(val) => onSizeChange(Number(val))}
          activeValue={size.toString()}
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
