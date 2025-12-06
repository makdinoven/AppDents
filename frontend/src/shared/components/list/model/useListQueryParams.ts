import { useCallback, useMemo } from "react";
import { useLocation, useSearchParams } from "react-router-dom";

export interface ListQueryParams {
  page: number;
  size: number;
  [key: string]: any;
}

interface Options {
  resetToFirstPage?: boolean;
  defaultPage?: number;
  defaultPageSize?: number;
  defaultSort?: string;
}

export function useListQueryParams(options?: Options) {
  const [search, setSearch] = useSearchParams();
  const location = useLocation();

  const PAGE = "page";
  const SIZE = "page-size";
  const SORT = "sort";

  const defaultPage = options?.defaultPage ?? 1;
  const defaultPageSize = options?.defaultPageSize ?? 12;
  const defaultSort = options?.defaultSort ?? "popular_desc";

  const params: ListQueryParams = useMemo(() => {
    const page = Number(search.get(PAGE)) || defaultPage;
    const size = Number(search.get(SIZE)) || defaultPageSize;
    const sort = search.get(SORT) || defaultSort;

    const parsed: ListQueryParams = { page, size, sort };

    search.forEach((value, key) => {
      if (key === PAGE || key === SIZE || key === SORT) return;

      parsed[key] = value.includes(",") ? value.split(",") : value;
    });

    return parsed;
  }, [search, defaultPage, defaultPageSize, defaultSort]);

  const set = useCallback(
    (next: Partial<ListQueryParams>) => {
      const newSearch = new URLSearchParams(search);

      Object.entries(next).forEach(([key, value]) => {
        const isPageKey = key === "page";

        const emptyArray = Array.isArray(value) && value.length === 0;
        const emptyValue =
          value === undefined || value === null || value === "";

        if (emptyArray || emptyValue) {
          newSearch.delete(key);
        } else if (Array.isArray(value)) {
          newSearch.set(key, value.join(","));
        } else {
          newSearch.set(key, String(value));
        }
        if (!isPageKey && options?.resetToFirstPage) newSearch.set(PAGE, "1");
      });

      const onlyPageChange =
        Object.keys(next).length === 1 && next.page !== undefined;

      setSearch(newSearch, {
        replace: !onlyPageChange,
        ...(location.state?.backgroundLocation
          ? { state: { backgroundLocation: location.state.backgroundLocation } }
          : {}),
      });
    },
    [search, setSearch],
  );

  const reset = useCallback(
    (key: string) => {
      const newSearch = new URLSearchParams(search);
      newSearch.delete(key);
      newSearch.set(PAGE, "1");

      setSearch(newSearch, { replace: true });
    },
    [search, setSearch],
  );

  const resetSingle = useCallback(
    (key: string, value?: string) => {
      const newSearch = new URLSearchParams(search);
      if (value !== undefined) {
        const current = newSearch.get(key);

        if (!current) {
          return;
        }

        const arr = current.split(",").filter(Boolean);
        const nextArr = arr.filter((v) => v !== value);

        if (nextArr.length === 0) {
          newSearch.delete(key);
        } else {
          newSearch.set(key, nextArr.join(","));
        }
      } else {
        const rangeMap: Record<string, { from: string; to: string }> = {
          year: { from: "year_from", to: "year_to" },
          price: { from: "price_from", to: "price_to" },
          pages: { from: "pages_from", to: "pages_to" },
        };

        const range = rangeMap[key];

        if (range) {
          newSearch.delete(range.from);
          newSearch.delete(range.to);
        } else {
          newSearch.delete(key);
        }
      }

      newSearch.set(PAGE, "1");

      setSearch(newSearch, {
        replace: true,
        ...(location.state?.backgroundLocation
          ? { state: { backgroundLocation: location.state.backgroundLocation } }
          : {}),
      });
    },
    [search, setSearch, location.state, options?.resetToFirstPage],
  );

  const resetAll = useCallback(() => {
    const newSearch = new URLSearchParams();
    newSearch.set(PAGE, String(defaultPage));
    newSearch.set(SIZE, String(defaultPageSize));
    newSearch.set(SORT, String(defaultSort));

    setSearch(newSearch, { replace: true });
  }, [setSearch, defaultPage, defaultPageSize, defaultSort]);

  return {
    params,
    actions: { set, reset, resetAll, resetSingle },
  };
}
