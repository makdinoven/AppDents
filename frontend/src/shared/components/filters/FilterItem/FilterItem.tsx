import { Filter } from "../model/types.ts";
import type { ListQueryParams } from "../../list/model/useListQueryParams.ts";
import MultiSelectFilter from "../MultiSelectFilter/MultiSelectFilter.tsx";
import RangeFilter from "../RangeFilter/RangeFilter.tsx";
import s from "./FilterItem.module.scss";
import ResetBtn from "../ResetBtn/ResetBtn.tsx";
import { Trans } from "react-i18next";
import { getFilterIcon } from "../model/getFilterIcon.tsx";

type Props = {
  filter: Filter;
  params: ListQueryParams;
  actions: {
    set: (next: Partial<ListQueryParams>) => void;
    reset: (key: string) => void;
  };
};

const FilterItem = ({ filter, params, actions }: Props) => {
  const reset = () => {
    if (filter.type === "range") {
      actions.set({
        [filter.from]: undefined,
        [filter.to]: undefined,
      });
    } else if (filter.type === "multiselect") {
      actions.reset(filter.name);
    }
  };

  return (
    <div className={s.filter_block}>
      <div className={s.filter_header_row}>
        <p>
          <span className={s.label_icon}>
            {getFilterIcon(filter.type === "range" ? filter.to : filter.name)}
          </span>
          <Trans i18nKey={filter.label} />
        </p>
        <ResetBtn onClick={reset} text={"reset"} />
      </div>

      {filter.type === "multiselect" && (
        <MultiSelectFilter filter={filter} params={params} actions={actions} />
      )}

      {filter.type === "range" && (
        <RangeFilter filter={filter} params={params} actions={actions} />
      )}
    </div>
  );
};

export default FilterItem;
