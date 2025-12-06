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
import { ArrowX, Chevron, FilterIcon } from "../../../assets/icons";
import FilterChip from "../FilterChip/FilterChip.tsx";
import SortSelect from "../SortSelect/SortSelect.tsx";
import SelectedFilters from "../SelectedFilters/SelectedFilters.tsx";
import { Trans } from "react-i18next";

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

        {filtersData.sorts.length > 0 && (
          <SortSelect
            selectClassName={s.select}
            chipClassName={s.select}
            options={filtersData.sorts}
            params={params}
            actions={actions}
          />
        )}
        <FilterChip
          showBadge
          className={s.select}
          badgeCount={selectedFilters?.length}
          iconLeft={<FilterIcon />}
          text={t("filters.allFilters")}
          iconRight={<Chevron className={s.chevron_icon} />}
          onClick={() => setOpen(true)}
        />
      </div>

      {totalItems > 0 && (
        <div className={s.found_items_section}>
          <FilterChip
            className={`${s.reset_chip} ${selectedFilters && selectedFilters?.length > 0 ? "" : s.hidden}`}
            variant={"selectedFilter"}
            onClick={actions.resetAll}
            text={
              ""
              // t("filters.resetAll")
            }
            iconLeft={<ArrowX />}
          />
          <p>
            <Trans i18nKey={t("filters.itemsFound", { count: totalItems })} />
          </p>
        </div>
      )}

      <SelectedFilters
        selected={selectedFilters}
        reset={actions.resetSingle}
        loading={loading}
      />
    </div>
  );
};

export default FiltersPanel;
