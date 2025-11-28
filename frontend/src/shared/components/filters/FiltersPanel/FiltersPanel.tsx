import { FiltersDataUI } from "../types";
import type { ListQueryParams } from "../../list/model/useListQueryParams";
import FiltersPanelFullscreen from "./FiltersPanelFullscreen";
import Search from "../../ui/Search/Search";
import s from "./FiltersPanel.module.scss";
import { useState } from "react";

type Props = {
  filtersData: FiltersDataUI | null;
  searchKey: string;
  searchPlaceholder: string;
  params: ListQueryParams;
  actions: {
    set: (next: Partial<ListQueryParams>) => void;
    reset: (key: string) => void;
    resetAll: () => void;
  };
};

const FiltersPanel = ({
  filtersData,
  searchKey,
  searchPlaceholder,
  params,
  actions,
}: Props) => {
  const [open, setOpen] = useState(false);

  if (!filtersData) return null;

  return (
    <>
      <div className={s.filters}>
        <Search id={searchKey} placeholder={searchPlaceholder} />

        {filtersData.sorts.length > 0 && (
          <select
            className={s.sort}
            value={params.sort ?? ""}
            onChange={(e) =>
              actions.set({ sort: e.target.value || undefined, page: 1 })
            }
          >
            <option value=""></option>
            {filtersData.sorts.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        )}

        <span className={s.filters_button} onClick={() => setOpen(true)}>
          filters
        </span>
      </div>

      <FiltersPanelFullscreen
        isOpen={open}
        onClose={() => setOpen(false)}
        filters={filtersData.filters}
        params={params}
        actions={actions}
      />
    </>
  );
};

export default FiltersPanel;
