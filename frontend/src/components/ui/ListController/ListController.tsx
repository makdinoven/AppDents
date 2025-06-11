import s from "./ListController.module.scss";
import Pagination from "../Pagination/Pagination.tsx";
import { useSearchParams } from "react-router-dom";
import useDebounce from "../../../common/hooks/useDebounce.ts";
import { useEffect, useRef } from "react";
import { ParamsType } from "../../../api/adminApi/types.ts";
import FiltersPanel from "../FiltersPanel/FiltersPanel.tsx";
import Search from "../Search/Search.tsx";
import { Trans } from "react-i18next";
import {
  FILTER_PARAM_KEYS,
  FilterKeys,
  LS_LANGUAGE_KEY,
} from "../../../common/helpers/commonConstants.ts";

type ListControllerProps = {
  type: string;
  loadData: (params: ParamsType) => void;
  total: number;
  totalPages: number;
  size: number;
  language?: string;
  children: React.ReactNode;
  filters?: FilterKeys[];
};

const ListController = ({
  type,
  loadData,
  children,
  language,
  size,
  total,
  totalPages,
  filters = [],
}: ListControllerProps) => {
  const SEARCH_KEY = `${type}_search`;
  const [searchParams, setSearchParams] = useSearchParams();

  const pageFromUrl = parseInt(searchParams.get("page") || "1", 10);
  const searchValue = searchParams.get(SEARCH_KEY) || undefined;
  const debouncedSearchValue = useDebounce(searchValue, 300);

  const getCurrentFilters = (): Record<FilterKeys, string | undefined> => {
    const obj: Record<FilterKeys, string | undefined> = {} as any;
    filters.forEach((key) => {
      const paramName = FILTER_PARAM_KEYS[key];
      obj[key] = searchParams.get(paramName) || undefined;
    });
    return obj;
  };

  const initialAppLang = language
    ? localStorage.getItem(LS_LANGUAGE_KEY)
    : undefined;

  const currentFilters = getCurrentFilters();

  const prevFilters = useRef<{
    search?: string;
    appLanguage?: string;
    byKey: Record<FilterKeys, string | undefined>;
  }>({
    search: debouncedSearchValue,
    appLanguage: initialAppLang || undefined,
    byKey: getCurrentFilters(),
  });

  const loadDataWithParams = () => {
    const filtersObj = currentFilters;

    loadData({
      page: pageFromUrl,
      language: filtersObj.language || language,
      q: debouncedSearchValue ?? undefined,
      size: filtersObj.size ? Number(filtersObj.size) : size,
      sort: filtersObj.sort,
      tags: filtersObj.tags,
    });
  };

  useEffect(() => {
    const prev = prevFilters.current;

    const isSearchChanged = prev.search !== debouncedSearchValue;
    const isAppLangChanged = prev.appLanguage !== language;

    let isSomeFilterChanged = false;
    for (const key of filters) {
      if (prev.byKey[key] !== currentFilters[key]) {
        isSomeFilterChanged = true;
        break;
      }
    }

    if (isSearchChanged || isAppLangChanged || isSomeFilterChanged) {
      const newParams = new URLSearchParams(searchParams);

      if (isSearchChanged) {
        newParams.delete(SEARCH_KEY);
      }

      if (pageFromUrl !== 1) {
        newParams.set("page", "1");
        setSearchParams(newParams, { replace: true });
      } else {
        loadDataWithParams();
      }

      prevFilters.current = {
        search: debouncedSearchValue,
        appLanguage: language,
        byKey: { ...currentFilters },
      };
    }
  }, [
    debouncedSearchValue,
    language,
    ...filters.map((key) => currentFilters[key]),
  ]);

  useEffect(() => {
    loadDataWithParams();
  }, [pageFromUrl]);

  return (
    <div className={s.list_controller_container}>
      <div className={s.search_container}>
        {filters.length > 0 && (
          <FiltersPanel filters={filters} defaultSize={size} />
        )}
        <Search id={SEARCH_KEY} placeholder={`${type}.search`} />
        {!!total && (
          <p>
            <Trans i18nKey={`${type}.found`} values={{ count: total }} />
          </p>
        )}
      </div>

      {children}

      <Pagination totalPages={totalPages} />
    </div>
  );
};

export default ListController;
