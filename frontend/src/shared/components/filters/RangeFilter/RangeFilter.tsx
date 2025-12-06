import { UIRangeFilter } from "../model/types.ts";
import type { ListQueryParams } from "../../list/model/useListQueryParams.ts";
import s from "./RangeFilter.module.scss";
import { useEffect, useState } from "react";
import useDebounce from "../../../common/hooks/useDebounce.ts";

type Props = {
  filter: UIRangeFilter;
  params: ListQueryParams;
  actions: {
    set: (next: Partial<ListQueryParams>) => void;
  };
};

const RangeFilter = ({ filter, params, actions }: Props) => {
  const fromParam = params[filter.from];
  const toParam = params[filter.to];
  const [from, setFrom] = useState(
    fromParam !== undefined && fromParam !== null ? String(fromParam) : "",
  );
  const [to, setTo] = useState(
    toParam !== undefined && toParam !== null ? String(toParam) : "",
  );
  const debouncedFrom = useDebounce(from, 400);
  const debouncedTo = useDebounce(to, 400);

  useEffect(() => {
    setFrom(
      fromParam !== undefined && fromParam !== null ? String(fromParam) : "",
    );
  }, [fromParam]);

  useEffect(() => {
    setTo(toParam !== undefined && toParam !== null ? String(toParam) : "");
  }, [toParam]);

  useEffect(() => {
    const trimmed = debouncedFrom.trim();

    if (!trimmed) {
      actions.set({ [filter.from]: undefined });
      return;
    }

    const num = Number(trimmed);
    if (Number.isNaN(num)) {
      actions.set({ [filter.from]: undefined });
      return;
    }

    if (num < filter.min || num > filter.max) {
      return;
    }
    if (to && num > Number(to)) return;

    actions.set({ [filter.from]: num });
  }, [debouncedFrom]);

  useEffect(() => {
    const trimmed = debouncedTo.trim();

    if (!trimmed) {
      actions.set({ [filter.to]: undefined });
      return;
    }

    const num = Number(trimmed);

    if (Number.isNaN(num)) {
      actions.set({ [filter.to]: undefined });
      return;
    }

    if (num < filter.min || num > filter.max) {
      return;
    }

    if (from && num < Number(from)) return;

    actions.set({ [filter.to]: num });
  }, [debouncedTo]);

  return (
    <div className={s.range_container}>
      <div className={s.range_inputs}>
        <input
          type="number"
          id={`filter-from-${filter.from}`}
          min={filter.min}
          max={filter.max}
          placeholder={String(filter.min)}
          value={from}
          onChange={(e) => setFrom(e.target.value)}
        />

        <span className={s.range_separator}></span>

        <input
          type="number"
          id={`filter-to-${filter.to}`}
          min={filter.min}
          max={filter.max}
          placeholder={String(filter.max)}
          value={to}
          onChange={(e) => setTo(e.target.value)}
        />
      </div>

      {/*{filter.min && filter.max && (*/}
      {/*  <div className={s.min_max_container}>*/}
      {/*    <span className={s.min_max_val}>min: {filter.min}</span>*/}
      {/*    <span className={s.min_max_val}>max: {filter.max}</span>*/}
      {/*  </div>*/}
      {/*)}*/}
    </div>
  );
};

export default RangeFilter;
