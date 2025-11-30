import s from "./SortSelect.module.scss";
import Select from "./modules/Select/Select.tsx";
import { Chevron, Sort } from "../../assets/icons";
import FilterChip from "../ui/FilterChip/FilterChip.tsx";
import { useEffect, useState } from "react";
import { t } from "i18next";
import type { ListQueryParams } from "../list/model/useListQueryParams.ts";

interface SelectComponentProps<T> {
  options: T[];
  params: ListQueryParams;
  actions: {
    set: (next: Partial<ListQueryParams>) => void;
    reset: (key: string) => void;
    resetAll: () => void;
  };
}

const SortSelect = <T extends { [key: string]: any }>({
  options,
  params,
  actions,
}: SelectComponentProps<T>) => {
  const [activeValue, setActiveValue] = useState<string | undefined>(
    params.sort,
  );
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    setActiveValue(params.sort);
  }, [params.sort]);

  const handleSortChange = (newSortValue: string) => {
    const sort = newSortValue || undefined;

    actions.set({ sort });

    setActiveValue(sort);
  };

  return (
    <Select
      options={options}
      trigger={
        <FilterChip
          text={t(`sort.keys.${activeValue}`)}
          iconLeft={<Sort />}
          iconRight={<Chevron />}
          className={`${s.sort_button} ${isOpen ? s.open : ""}`}
        />
      }
      subtitle={t("sort.toShowFirst")}
      radioButtonType="radio"
      onChange={handleSortChange}
      isOpen={isOpen}
      setIsOpen={setIsOpen}
      activeValue={activeValue}
    />
  );
};
export default SortSelect;
