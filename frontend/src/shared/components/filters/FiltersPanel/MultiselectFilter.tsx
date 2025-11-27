import { MultiselectFilter, MultiselectOption } from "../types.ts";
import s from "./FiltersPanel.module.scss";
import type { ListQueryParams } from "../../list/model/useListQueryParams.ts";

type MultiSelectFilterProps = {
  filter: MultiselectFilter;
  params: ListQueryParams;
  setParams: (next: Partial<ListQueryParams>) => void;
};

const MultiSelectFilter = ({
  filter,
  params,
  setParams,
}: MultiSelectFilterProps) => {
  const raw = params.filters[filter.param_name];

  const selectedValues: string[] = Array.isArray(raw)
    ? raw.map(String)
    : raw
      ? String(raw).split(",")
      : [];

  const toggleOption = (option: MultiselectOption) => {
    const valueStr = String(option.id ?? option.value ?? "");

    const isSelected = selectedValues.includes(valueStr);
    const nextValues = isSelected
      ? selectedValues.filter((v) => v !== valueStr)
      : [...selectedValues, valueStr];

    setParams({
      filters: {
        ...params.filters,
        [filter.param_name]: nextValues,
      },
      page: 1,
    });
  };

  return (
    <div className={s.filter_block}>
      <div className={s.filter_header}>{filter.label}</div>

      <div className={s.filter_options}>
        {filter.options.map((option) => {
          const valueStr = String(option.id ?? option.value ?? "");
          const checked = selectedValues.includes(valueStr);

          return (
            <label key={valueStr} className={s.filter_option}>
              <input
                type="checkbox"
                checked={checked}
                onChange={() => toggleOption(option)}
              />
              <span className={s.option_name}>{option.name}</span>
              {typeof option.count === "number" && (
                <span className={s.option_count}>({option.count})</span>
              )}
            </label>
          );
        })}
      </div>
    </div>
  );
};

export default MultiSelectFilter;
