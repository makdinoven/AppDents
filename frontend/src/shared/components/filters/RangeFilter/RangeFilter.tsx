import { UIRangeFilter } from "../model/types.ts";
import type { ListQueryParams } from "../../list/model/useListQueryParams.ts";
import s from "./RangeFilter.module.scss";
import { useEffect, useState } from "react";
import useDebounce from "../../../common/hooks/useDebounce.ts";
import RangeFilterItem from "./RangeFilterItem/RangeFilterItem.tsx";

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

  const updateNumber = (
    value: string,
    setter: (v: string) => void,
    mode: "inc" | "dec",
    min: number,
    max: number,
  ) => {
    if (mode === "dec") {
      if (value === "" || value === null) return;

      const current = Number(value);

      if (current <= min) {
        setter(""); // сброс
      } else {
        setter(String(current - 1));
      }

      return;
    }

    // INC
    const current = Number(value) || min;
    const next = Math.min(current + 1, max);
    setter(String(next));
  };

  const incFrom = () =>
    updateNumber(from, setFrom, "inc", filter.min, filter.max);

  const decFrom = () =>
    updateNumber(from, setFrom, "dec", filter.min, filter.max);

  const incTo = () => updateNumber(to, setTo, "inc", filter.min, filter.max);

  const decTo = () => updateNumber(to, setTo, "dec", filter.min, filter.max);

  return (
    <div className={s.range_container}>
      <div className={s.range_items}>
        <RangeFilterItem
          id={`filter-from-${filter.from}`}
          min={filter.min.toString()}
          max={filter.max.toString()}
          placeholder={filter.min.toString()}
          value={from}
          disabledMinus={!from}
          disabledPlus={!!from && Number(from) >= filter.max}
          actions={{
            change: (v) => setFrom(v),
            inc: incFrom,
            dec: decFrom,
          }}
        />

        <span className={s.range_separator}></span>

        <RangeFilterItem
          id={`filter-to-${filter.to}`}
          min={filter.min.toString()}
          max={filter.max.toString()}
          placeholder={filter.max.toString()}
          value={to}
          disabledMinus={!to}
          disabledPlus={!!to && Number(to) >= filter.max}
          actions={{
            change: (v) => setTo(v),
            inc: incTo,
            dec: decTo,
          }}
        />
      </div>
      {typeof filter.min !== "undefined" &&
        typeof filter.max !== "undefined" && (
          <div className={s.min_max_container}>
            <span>min: {filter.min}</span>
            <span>max: {filter.max}</span>
          </div>
        )}
    </div>
  );
};

export default RangeFilter;
