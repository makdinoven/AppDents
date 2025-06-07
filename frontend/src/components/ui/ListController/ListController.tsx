import s from "./ListController.module.scss";
import Search from "../Search/Search.tsx";
import { Trans } from "react-i18next";
import Pagination from "../Pagination/Pagination.tsx";
import { useSearchParams } from "react-router-dom";
import useDebounce from "../../../common/hooks/useDebounce.ts";
import { JSX, useEffect, useRef, useState } from "react";
import { ParamsType } from "../../../api/adminApi/types.ts";
import { getTags } from "../../../store/actions/mainActions.ts";
import { useDispatch, useSelector } from "react-redux";
import { AppDispatchType } from "../../../store/store.ts";
import MultiSelect from "../../CommonComponents/MultiSelect/MultiSelect.tsx";
import {
  PAGE_SIZES,
  SORT_FILTERS,
} from "../../../common/helpers/commonConstants.ts";

type ListControllerProps = {
  type: string;
  loadData: (params: ParamsType) => void;
  total: number;
  totalPages: number;
  size: number;
  language?: string;
  children: React.ReactNode;
  filters?: string[];
};

const ListController = ({
  type,
  loadData,
  children,
  language,
  size,
  total,
  totalPages,
  filters,
}: ListControllerProps) => {
  const SEARCH_KEY = `${type}_search`;
  const [searchParams, setSearchParams] = useSearchParams();
  const pageFromUrl = parseInt(searchParams.get("page") || "1");
  const searchValue = searchParams.get(SEARCH_KEY);
  const debouncedSearchValue = useDebounce(searchValue, 300);
  const prevLanguage = useRef<string | undefined>("");
  const prevSearch = useRef(debouncedSearchValue);
  const dispatch = useDispatch<AppDispatchType>();
  const tags = useSelector((state: any) => state.main.tags);
  const [tag, setTag] = useState("all");
  const [pageSize, setPageSize] = useState<string | number>(size);
  const [sort, setSort] = useState("popular");

  useEffect(() => {
    if (tags.length < 1) {
      dispatch(getTags());
    }
  }, []);

  useEffect(() => {
    const isLanguageChanged = prevLanguage.current !== language;
    const isSearchChanged = prevSearch.current !== debouncedSearchValue;

    if (isLanguageChanged || isSearchChanged) {
      const newParams = new URLSearchParams(searchParams);

      if (isLanguageChanged) {
        newParams.delete(`${type}_search`);
      }
      if (newParams.get("page") !== "1") {
        newParams.set("page", "1");
      } else {
        loadData({
          page: pageFromUrl,
          language,
          q: debouncedSearchValue ?? undefined,
          size: Number(pageSize),
        });
      }

      setSearchParams(newParams, { replace: true });
    }

    prevLanguage.current = language;
    prevSearch.current = debouncedSearchValue;
  }, [debouncedSearchValue, language]);

  useEffect(() => {
    loadData({
      page: pageFromUrl,
      language,
      q: debouncedSearchValue ?? undefined,
      size: Number(pageSize),
    });
  }, [pageFromUrl]);

  const commonFilterProps = {
    isWider: true,
    isSearchable: false,
    placeholder: "",
    isMultiple: false,
    valueKey: "value" as const,
    labelKey: "name" as const,
  };

  const allFilters: { [key: string]: JSX.Element } = {
    tags: (
      <MultiSelect
        {...commonFilterProps}
        options={tags}
        id={"tags"}
        selectedValue={tag}
        onChange={(e) => setTag(e.value as string)}
      />
    ),
    sort: (
      <MultiSelect
        {...commonFilterProps}
        options={SORT_FILTERS}
        id={"sort"}
        selectedValue={sort}
        onChange={(e) => setSort(e.value as string)}
      />
    ),
    size: (
      <MultiSelect
        {...commonFilterProps}
        options={PAGE_SIZES}
        id={"size"}
        selectedValue={pageSize}
        onChange={(e) => setPageSize(e.value as string)}
      />
    ),
  };

  return (
    <div className={s.list_controller_container}>
      <div className={s.search_container}>
        {filters && (
          <div className={s.filters}>
            {filters?.map((key) => allFilters[key])}
          </div>
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
