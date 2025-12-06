import s from "./SelectedFilters.module.scss";
import FilterChip from "../FilterChip/FilterChip.tsx";
import { ResetSingleActionType, SelectedUI } from "../model/types.ts";
import { ArrowX, Chevron } from "../../../assets/icons";
import { t } from "i18next";
import { useEffect, useState } from "react";
import { getFilterIcon } from "../model/getFilterIcon.tsx";
import { useSelectedFiltersLayout } from "./model/useSelectedFiltersLayout.ts";

type Props = {
  selected: SelectedUI[] | null;
  reset: ResetSingleActionType;
  loading?: boolean;
};

const SelectedFilters = ({ selected, reset, loading = false }: Props) => {
  const items = selected ?? [];
  const [pendingKey, setPendingKey] = useState<string | null>(null);

  const {
    row1,
    row2,
    containerRef,
    measureRef,
    canScrollLeft,
    canScrollRight,
    scrollLeft,
    scrollRight,
  } = useSelectedFiltersLayout(items);

  const getChipKey = (chip: SelectedUI) =>
    chip.kind === "multiselect"
      ? `${chip.paramName}-${chip.value}`
      : `range-${chip.paramName}`;

  const buildRangeText = (chip: Extract<SelectedUI, { kind: "range" }>) => {
    const { from, to } = chip;
    return `${from ? from : "min"} – ${to ? to : "max"}`;
  };

  const buildText = (chip: SelectedUI) =>
    chip.kind === "multiselect" ? t(chip.name) : buildRangeText(chip);

  const renderChip = (chip: SelectedUI) => {
    const key = getChipKey(chip);
    const isPending = loading && pendingKey === key;

    return (
      <FilterChip
        key={key}
        text={buildText(chip)}
        variant="selectedFilter"
        iconLeft={getFilterIcon(chip.paramName)}
        iconRight={<ArrowX />}
        loading={isPending}
        onClick={() => {
          if (loading) return;
          setPendingKey(key);

          if (chip.kind === "multiselect") {
            reset(chip.paramName, chip.value);
          } else {
            reset(chip.paramName);
          }
        }}
      />
    );
  };

  useEffect(() => {
    if (!loading) {
      setPendingKey(null);
    }
  }, [loading]);

  if (items.length === 0) return null;

  return (
    <>
      <div className={s.selected_filters_wrapper}>
        <button
          type="button"
          className={`${s.scroll_btn} ${s.scroll_btn_left} ${
            canScrollLeft ? "" : s.hidden
          }`}
          onClick={scrollLeft}
        >
          <Chevron className={s.scroll_icon_left} />
        </button>

        <div className={s.selected_filters_outer} ref={containerRef}>
          <div className={s.selected_filters_row}>{row1.map(renderChip)}</div>
          {row2.length > 0 && (
            <div className={s.selected_filters_row}>{row2.map(renderChip)}</div>
          )}
        </div>

        <button
          type="button"
          className={`${s.scroll_btn} ${s.scroll_btn_right} ${
            canScrollRight ? "" : s.hidden
          }`}
          onClick={scrollRight}
        >
          <Chevron className={s.scroll_icon_right} />
        </button>
      </div>

      <div
        className={s.selected_filters_measure}
        ref={measureRef}
        aria-hidden="true"
      >
        {items.map(renderChip)}
      </div>
    </>
  );
};

export default SelectedFilters;
