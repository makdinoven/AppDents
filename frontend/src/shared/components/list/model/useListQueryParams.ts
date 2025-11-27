import { useCallback, useMemo } from "react";
import { useSearchParams } from "react-router-dom";

export interface ListQueryParams {
  page: number;
  pageSize: number;
  filters: Record<string, any>;
}

interface UseListQueryParamsOptions {
  defaultPage?: number;
  defaultPageSize?: number;
}

export function useListQueryParams(options?: UseListQueryParamsOptions) {
  const [search, setSearch] = useSearchParams();

  const pageKey = "page";
  const sizeKey = "page-size";

  const defaultPage = options?.defaultPage ?? 1;
  const defaultPageSize = options?.defaultPageSize ?? 12;

  const params: ListQueryParams = useMemo(() => {
    const page = Number(search.get(pageKey)) || defaultPage;
    const pageSize = Number(search.get(sizeKey)) || defaultPageSize;

    const filters: Record<string, any> = {};

    search.forEach((value, key) => {
      if (key === pageKey || key === sizeKey) return;

      if (value.includes(",")) {
        filters[key] = value.split(",");
      } else {
        filters[key] = value;
      }
    });

    return { page, pageSize, filters };
  }, [search, defaultPage, defaultPageSize]);

  const updateParams = useCallback(
    (next: Partial<ListQueryParams>) => {
      const newSearch = new URLSearchParams(search);

      if (next.page !== undefined) {
        newSearch.set(pageKey, String(next.page));
      }

      if (next.pageSize !== undefined) {
        newSearch.set(sizeKey, String(next.pageSize));
      }

      if (next.filters) {
        Object.entries(next.filters).forEach(([key, value]) => {
          const isEmptyArray = Array.isArray(value) && value.length === 0;
          const isEmptyScalar =
            value === undefined || value === null || value === "";

          if (isEmptyArray || isEmptyScalar) {
            newSearch.delete(key);
            return;
          }

          if (Array.isArray(value)) {
            newSearch.set(key, value.join(","));
          } else {
            newSearch.set(key, String(value));
          }
        });
      }

      setSearch(newSearch);
    },
    [search, setSearch],
  );

  const resetParams = useCallback(() => {
    const cleared = new URLSearchParams();
    cleared.set(pageKey, String(defaultPage));
    cleared.set(sizeKey, String(defaultPageSize));
    setSearch(cleared, { replace: true });
  }, [setSearch, defaultPage, defaultPageSize]);

  return {
    params,
    setParams: updateParams,
    resetParams,
  };
}
