import { UIMultiselectFilter } from "../types";
import type { ListQueryParams } from "../../list/model/useListQueryParams";
import s from "./FiltersPanel.module.scss";

type Props = {
  filter: UIMultiselectFilter;
  params: ListQueryParams;
  actions: {
    set: (next: Partial<ListQueryParams>) => void;
  };
};

const MultiSelectFilter = ({ filter, params, actions }: Props) => {
  const raw = params[filter.name];
  const selected = Array.isArray(raw) ? raw : raw ? String(raw).split(",") : [];

  const toggle = (value: string) => {
    const next = selected.includes(value)
      ? selected.filter((v) => v !== value)
      : [...selected, value];

    actions.set({
      [filter.name]: next.length ? next : undefined,
    });
  };

  return (
    <div className={s.filter_options}>
      {filter.options.map((opt) => (
        <label key={opt.value} className={s.filter_option}>
          <input
            type="checkbox"
            checked={selected.includes(opt.value)}
            onChange={() => toggle(opt.value)}
          />
          <span className={s.option_name}>{opt.label}</span>
          {opt.count !== undefined && (
            <span className={s.option_count}>({opt.count})</span>
          )}
        </label>
      ))}
    </div>
  );
};

export default MultiSelectFilter;
