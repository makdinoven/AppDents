import { Filter } from "../types.ts";
import type { ListQueryParams } from "../../list/model/useListQueryParams.ts";
import MultiSelectFilter from "./MultiselectFilter.tsx";
import RangeFilter from "./RangeFilter.tsx";
import s from "./FiltersPanel.module.scss";

type FilterItemProps = {
  filter: Filter;
  params: ListQueryParams;
  setParams: (next: Partial<ListQueryParams>) => void;
};

const FilterItem = ({ filter, params, setParams }: FilterItemProps) => {
  const resetSingle = () => {
    if (filter.type === "range") {
      setParams({
        filters: {
          ...params.filters,
          [filter.param_name_from]: undefined,
          [filter.param_name_to]: undefined,
        },
        page: 1,
      });
    }

    if (filter.type === "multiselect") {
      setParams({
        filters: {
          ...params.filters,
          [filter.param_name]: [],
        },
        page: 1,
      });
    }
  };

  return (
    <div className={s.filter_block}>
      <div className={s.filter_header_row}>
        <div className={s.filter_header}>{filter.label}</div>

        <button className={s.reset_item_btn} onClick={resetSingle}>
          Reset
        </button>
      </div>

      {filter.type === "multiselect" && (
        <MultiSelectFilter
          filter={filter}
          params={params}
          setParams={setParams}
        />
      )}

      {filter.type === "range" && (
        <RangeFilter filter={filter} params={params} setParams={setParams} />
      )}
    </div>
  );
};

export default FilterItem;
