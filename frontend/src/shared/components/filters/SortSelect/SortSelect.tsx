import Select from "../../ui/Select/Select.tsx";
import { Sort } from "../../../assets/icons";
import FilterChip from "../FilterChip/FilterChip.tsx";
import { t } from "i18next";
import type { ListQueryParams } from "../../list/model/useListQueryParams.ts";

interface SelectComponentProps<T> {
  options: T[];
  params: ListQueryParams;
  selectClassName?: string;
  actions: {
    set: (next: Partial<ListQueryParams>) => void;
    reset: (key: string) => void;
    resetAll: () => void;
  };
}

const SortSelect = <T extends { [key: string]: any }>({
  options,
  params,
  selectClassName,
  actions,
}: SelectComponentProps<T>) => {
  const active = params.sort;

  const sortedOptions = [...options].sort((a, b) => {
    if (a.value === active) return -1;
    if (b.value === active) return 1;
    return 0;
  });

  return (
    <Select
      className={selectClassName}
      options={sortedOptions}
      renderTrigger={(open) => (
        <FilterChip
          variant={"dropdown"}
          text={t(`sort.keys.${params.sort}`)}
          iconLeft={<Sort />}
          isActive={open}
        />
      )}
      subtitle={t("sort.toShowFirst")}
      radioButtonType="radio"
      onChange={(sort) => actions.set({ sort })}
      activeValue={params.sort}
    />
  );
};
export default SortSelect;
