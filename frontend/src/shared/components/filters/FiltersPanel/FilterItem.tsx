import { Filter } from "../types";
import type { ListQueryParams } from "../../list/model/useListQueryParams";
import MultiSelectFilter from "./MultiSelectFilter";
import RangeFilter from "./RangeFilter";
import s from "./FiltersPanel.module.scss";

type Props = {
  filter: Filter;
  params: ListQueryParams;
  actions: {
    set: (next: Partial<ListQueryParams>) => void;
    reset: (key: string) => void;
  };
};

const FilterItem = ({ filter, params, actions }: Props) => {
  const reset = () => {
    if (filter.type === "range") {
      actions.reset(filter.from);
      actions.reset(filter.to);
    } else if (filter.type === "multiselect") {
      actions.reset(filter.name);
    }
  };

  return (
    <div className={s.filter_block}>
      <div className={s.filter_header_row}>
        <div className={s.filter_header}>{filter.label}</div>
        <button onClick={reset} className={s.reset_item_btn}>
          Reset
        </button>
      </div>

      {filter.type === "multiselect" && (
        <MultiSelectFilter filter={filter} params={params} actions={actions} />
      )}

      {filter.type === "range" && (
        <RangeFilter filter={filter} params={params} actions={actions} />
      )}
    </div>
  );
};

export default FilterItem;
