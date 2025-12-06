import {
  FilterActionsType,
  FiltersDataUI,
  SelectedUI,
} from "../model/types.ts";
import type { ListQueryParams } from "../../list/model/useListQueryParams";
import FiltersPanelFullscreen from "../FiltersPanelFullscreen/FiltersPanelFullscreen.tsx";
import Search from "../../ui/Search/Search";
import s from "./FiltersPanel.module.scss";
import { useState } from "react";
import { t } from "i18next";
import { Chevron, FilterIcon } from "../../../assets/icons";
import FilterChip from "../FilterChip/FilterChip.tsx";
import SortSelect from "../SortSelect/SortSelect.tsx";
import SelectedFilters from "../SelectedFilters/SelectedFilters.tsx";

type Props = {
  loading?: boolean;
  filtersData: FiltersDataUI | null;
  searchPlaceholder: string;
  params: ListQueryParams;
  totalItems: number;
  selectedFilters: SelectedUI[] | null;
  actions: FilterActionsType;
};

const FiltersPanel = ({
  filtersData,
  loading,
  searchPlaceholder,
  params,
  totalItems,
  selectedFilters,
  actions,
}: Props) => {
  const [open, setOpen] = useState(false);

  if (!filtersData) return null;

  return (
    <div className={s.filters_panel_container}>
      <div className={s.filters_panel}>
        <Search
          valueFromUrl={params.q ?? ""}
          onChangeValue={(val) => actions.set({ q: val })}
          useDebounceOnChange
          id={"q"}
          placeholder={searchPlaceholder}
        />

        <FiltersPanelFullscreen
          loading={loading}
          totalItems={totalItems}
          isOpen={open}
          onClose={() => setOpen(false)}
          filters={filtersData.filters}
          params={params}
          actions={actions}
        />

        <div className={s.filter_controls}>
          {filtersData.sorts.length > 0 && (
            <SortSelect
              selectClassName={s.select}
              options={filtersData.sorts}
              params={params}
              actions={actions}
            />
          )}
          <FilterChip
            showBadge
            badgeCount={selectedFilters?.length}
            iconLeft={<FilterIcon />}
            text={t("filters.allFilters")}
            iconRight={<Chevron className={s.chevron_icon} />}
            onClick={() => setOpen(true)}
          />
        </div>
      </div>

      {/*{totalItems > 0 && (*/}
      {/*  <Trans i18nKey={t("filters.itemsFound", { count: totalItems })} />*/}
      {/*)}*/}

      <SelectedFilters
        selected={selectedFilters}
        reset={actions.resetSingle}
        loading={loading}
      />
    </div>
  );
};

export default FiltersPanel;
