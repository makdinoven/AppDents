import s from "./FiltersPanel.module.scss";
import Search from "../../ui/Search/Search.tsx";
import { useState } from "react";
import type { ListQueryParams } from "../../list/model/useListQueryParams.ts";
import FiltersPanelFullscreen from "./FiltersPanelFullscreen.tsx";
import { FiltersData } from "../types.ts";

type FiltersPanelProps = {
  filtersData: FiltersData | null;
  searchKey: string;
  searchPlaceholder: string;
  params: ListQueryParams;
  setParams: (next: Partial<ListQueryParams>) => void;
};

const FiltersPanel = ({
  filtersData,
  searchKey,
  searchPlaceholder,
  params,
  setParams,
}: FiltersPanelProps) => {
  const [isFullScreen, setIsFullScreen] = useState(false);

  console.log(filtersData);

  if (!filtersData) return null;

  const { available_sorts, filters } = filtersData;

  const handleSortChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value || undefined;

    setParams({
      filters: {
        ...params.filters,
        sort: value,
      },
      page: 1,
    });
  };

  return (
    <>
      <div className={s.filters}>
        <Search id={searchKey} placeholder={searchPlaceholder} />

        {available_sorts?.length > 0 && (
          <select
            className={s.sort}
            value={params.filters.sort ?? ""}
            onChange={handleSortChange}
          >
            <option value="">{/* пустое значение = без сортировки */}</option>
            {available_sorts.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        )}

        <span
          className={s.filters_button}
          onClick={() => setIsFullScreen(true)}
        >
          filters
        </span>
      </div>

      <FiltersPanelFullscreen
        isFullScreen={isFullScreen}
        setIsFullScreen={setIsFullScreen}
        setParams={setParams}
        params={params}
        filters={filters}
      />
    </>
  );
};

export default FiltersPanel;
