import type { ListQueryParams } from "../../list/model/useListQueryParams.ts";
import s from "./FiltersPanel.module.scss";
import type { RangeFilter as RangeFilterType } from "../types.ts";

type RangeFilterProps = {
  filter: RangeFilterType;
  params: ListQueryParams;
  setParams: (next: Partial<ListQueryParams>) => void;
};

const RangeFilter = ({ filter, params, setParams }: RangeFilterProps) => {
  const fromKey = filter.param_name_from;
  const toKey = filter.param_name_to;

  const fromValue =
    params.filters[fromKey] !== undefined
      ? params.filters[fromKey]
      : filter.min;
  const toValue =
    params.filters[toKey] !== undefined ? params.filters[toKey] : filter.max;

  const handleChange = (key: string, value: string) => {
    setParams({
      filters: {
        ...params.filters,
        [key]: value || undefined,
      },
      page: 1,
    });
  };

  return (
    <div className={s.filter_block}>
      <div className={s.filter_header}>{filter.label}</div>

      <div className={s.range_inputs}>
        <input
          type="number"
          min={filter.min}
          max={filter.max}
          value={fromValue}
          onChange={(e) => handleChange(fromKey, e.target.value)}
        />
        <span className={s.range_separator}>–</span>
        <input
          type="number"
          min={filter.min}
          max={filter.max}
          value={toValue}
          onChange={(e) => handleChange(toKey, e.target.value)}
        />
        {filter.unit && <span className={s.unit}>{filter.unit}</span>}
      </div>
    </div>
  );
};

export default RangeFilter;
