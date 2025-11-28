import { UIRangeFilter } from "../types";
import type { ListQueryParams } from "../../list/model/useListQueryParams";
import s from "./FiltersPanel.module.scss";

type Props = {
  filter: UIRangeFilter;
  params: ListQueryParams;
  actions: {
    set: (next: Partial<ListQueryParams>) => void;
  };
};

const RangeFilter = ({ filter, params, actions }: Props) => {
  const from = params[filter.from] ?? filter.min;
  const to = params[filter.to] ?? filter.max;

  const update = (key: string, v: string) =>
    actions.set({ [key]: v || undefined });

  return (
    <div className={s.range_inputs}>
      <input
        type="number"
        min={filter.min}
        max={filter.max}
        value={from}
        onChange={(e) => update(filter.from, e.target.value)}
      />

      <span className={s.range_separator}>–</span>

      <input
        type="number"
        min={filter.min}
        max={filter.max}
        value={to}
        onChange={(e) => update(filter.to, e.target.value)}
      />

      {filter.unit && <span className={s.unit}>{filter.unit}</span>}
    </div>
  );
};

export default RangeFilter;
