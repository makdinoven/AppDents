import { useCallback, useMemo } from "react";
import { useSearchParams } from "react-router-dom";

export interface ListQueryParams {
  page: number;
  size: number;
  [key: string]: any;
}

interface Options {
  defaultPage?: number;
  defaultPageSize?: number;
  defaultSort?: string;
}

export function useListQueryParams(options?: Options) {
  const [search, setSearch] = useSearchParams();

  const PAGE = "page";
  const SIZE = "page-size";
  const SORT = "sort";

  const defaultPage = options?.defaultPage ?? 1;
  const defaultPageSize = options?.defaultPageSize ?? 12;
  const defaultSort = options?.defaultSort ?? "popular_desc";

  // ----------------------------------
  // PARSE URL
  // ----------------------------------
  const params: ListQueryParams = useMemo(() => {
    const page = Number(search.get(PAGE)) || defaultPage;
    const size = Number(search.get(SIZE)) || defaultPageSize;
    const sort = Number(search.get(SORT)) || defaultSort;

    const parsed: ListQueryParams = { page, size, sort };

    search.forEach((value, key) => {
      if (key === PAGE || key === SIZE || key === SORT) return;

      parsed[key] = value.includes(",") ? value.split(",") : value;
    });

    return parsed;
  }, [search, defaultPage, defaultPageSize, defaultSort]);

  // ----------------------------------
  // ACTIONS
  // ----------------------------------

  const set = useCallback(
    (next: Partial<ListQueryParams>) => {
      const newSearch = new URLSearchParams(search);

      Object.entries(next).forEach(([key, value]) => {
        const isPageKey = key === "page" || key === "size";

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

        // any filter → reset page
        if (!isPageKey) newSearch.set(PAGE, "1");
      });

      const onlyPageChange =
        Object.keys(next).length === 1 && next.page !== undefined;

      setSearch(newSearch, {
        replace: !onlyPageChange, // page = push, filters = replace
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

  const resetAll = useCallback(() => {
    const newSearch = new URLSearchParams();
    newSearch.set(PAGE, String(defaultPage));
    newSearch.set(SIZE, String(defaultPageSize));
    newSearch.set(SORT, String(defaultSort));

    setSearch(newSearch, { replace: true });
  }, [setSearch, defaultPage, defaultPageSize, defaultSort]);

  return {
    params,
    actions: { set, reset, resetAll },
  };
}
