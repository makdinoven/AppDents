import { FiltersDataUI } from "../types";
import type { ListQueryParams } from "../../list/model/useListQueryParams";
import FiltersPanelFullscreen from "./FiltersPanelFullscreen";
import Search from "../../ui/Search/Search";
import s from "./FiltersPanel.module.scss";
import { useState } from "react";
import { t } from "i18next";
import { Chevron } from "../../../assets/icons";
import FilterChip from "../../ui/FilterChip/FilterChip.tsx";
import SortSelect from "../../SortSelect/SortSelect.tsx";

type Props = {
  filtersData: FiltersDataUI | null;
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
  searchPlaceholder,
  params,
  actions,
}: Props) => {
  const [open, setOpen] = useState(false);

  if (!filtersData) return null;

  return (
    <>
      <div className={s.filters_panel}>
        <Search id={"q"} placeholder={searchPlaceholder} />

        <div className={s.filter_controls}>
          {filtersData.sorts.length > 0 && (
            <SortSelect
              options={filtersData.sorts}
              params={params}
              actions={actions}
            />
          )}
          <FilterChip
            text={t("filters.allFilters")}
            iconRight={<Chevron />}
            onClick={() => setOpen(true)}
            className={s.filters_buttons}
          />
        </div>
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
