import { useCallback, useMemo, useRef } from "react";
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
  ignoredKeys?: string[];
  servicePrefix?: string;
}

const PAGE = "page";
const SIZE = "page-size";
const SORT = "sort";

const shallowEqualParams = (a: ListQueryParams | null, b: ListQueryParams) => {
  if (!a) return false;

  const aKeys = Object.keys(a);
  const bKeys = Object.keys(b);
  if (aKeys.length !== bKeys.length) return false;

  for (const key of aKeys) {
    const aVal = a[key];
    const bVal = b[key];

    if (Array.isArray(aVal) && Array.isArray(bVal)) {
      if (aVal.length !== bVal.length) return false;
      for (let i = 0; i < aVal.length; i++) {
        if (aVal[i] !== bVal[i]) return false;
      }
    } else if (aVal !== bVal) {
      return false;
    }
  }

  return true;
};

export function useListQueryParams(options?: Options) {
  const [search, setSearch] = useSearchParams();
  const location = useLocation();
  const prevParamsRef = useRef<ListQueryParams | null>(null);

  const defaultPage = options?.defaultPage ?? 1;
  const defaultPageSize = options?.defaultPageSize ?? 12;
  const defaultSort = options?.defaultSort ?? "popular_desc";
  const ignoredKeys = options?.ignoredKeys ?? [];
  const servicePrefix = options?.servicePrefix ?? "_";

  const params: ListQueryParams = useMemo(() => {
    const filtered = new URLSearchParams();

    search.forEach((value, key) => {
      if (ignoredKeys.includes(key)) return;
      if (servicePrefix && key.startsWith(servicePrefix)) return;

      filtered.append(key, value);
    });

    const page = Number(filtered.get(PAGE)) || defaultPage;
    const size = Number(filtered.get(SIZE)) || defaultPageSize;
    const sort = filtered.get(SORT) || defaultSort;

    const next: ListQueryParams = { page, size, sort };

    filtered.forEach((value, key) => {
      if (key === PAGE || key === SIZE || key === SORT) return;

      next[key] = value.includes(",") ? value.split(",") : value;
    });

    if (shallowEqualParams(prevParamsRef.current, next)) {
      return prevParamsRef.current as ListQueryParams;
    }

    prevParamsRef.current = next;
    return next;
  }, [
    search,
    defaultPage,
    defaultPageSize,
    defaultSort,
    ignoredKeys,
    servicePrefix,
  ]);

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

        if (!isPageKey && options?.resetToFirstPage) {
          newSearch.set(PAGE, "1");
        }
      });

      const oldSearchStr = search.toString();
      const newSearchStr = newSearch.toString();

      if (oldSearchStr === newSearchStr) {
        return;
      }

      const onlyPageChange =
        Object.keys(next).length === 1 && next.page !== undefined;

      setSearch(newSearch, {
        replace: !onlyPageChange,
      });
    },
    [search, setSearch, options?.resetToFirstPage],
  );

  const reset = useCallback(
    (key: string) => {
      const newSearch = new URLSearchParams(search);
      newSearch.delete(key);
      newSearch.set(PAGE, "1");

      setSearch(newSearch, {
        replace: true,
      });
    },
    [search, setSearch, location.state],
  );

  const resetSingle = useCallback(
    (key: string, value?: string) => {
      const newSearch = new URLSearchParams(search);

      if (value !== undefined) {
        const current = newSearch.get(key);
        if (!current) return;

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
      });
    },
    [search, setSearch, location.state],
  );

  const resetAll = useCallback(() => {
    const newSearch = new URLSearchParams();

    search.forEach((value, key) => {
      const isService = servicePrefix && key.startsWith(servicePrefix); // служебные key

      if (isService) {
        newSearch.set(key, value);
      }
    });
    newSearch.set(PAGE, String(defaultPage));
    newSearch.set(SIZE, String(defaultPageSize));
    newSearch.set(SORT, String(defaultSort));

    setSearch(newSearch, { replace: true });
  }, [
    search,
    setSearch,
    ignoredKeys,
    servicePrefix,
    defaultPage,
    defaultPageSize,
    defaultSort,
  ]);

  return {
    params,
    actions: { set, reset, resetAll, resetSingle },
  };
}
