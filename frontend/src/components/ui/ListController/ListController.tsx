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
  const [limit, setLimit] = useState("10");
  const [sort, setSort] = useState("popular");
  const dispatch = useDispatch<AppDispatchType>();
  const tags = useSelector((state: any) => state.main.tags);
  const [tag, setTag] = useState("all");
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
          size,
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
      size,
    });
  }, [pageFromUrl]);

  const allFilters: { [key: string]: JSX.Element } = {
    tags: (
      <MultiSelect
        isWider={true}
        isSearchable={false}
        id={"tags"}
        options={tags}
        placeholder={""}
        selectedValue={tag}
        isMultiple={false}
        onChange={(e) => setTag(e.value as string)}
        valueKey="value"
        labelKey="name"
      />
    ),
    sort: (
      <MultiSelect
        isWider={true}
        isSearchable={false}
        id={"sort"}
        options={SORT_FILTERS}
        placeholder={""}
        selectedValue={sort}
        isMultiple={false}
        onChange={(e) => setSort(e.value as string)}
        valueKey="value"
        labelKey="name"
      />
    ),
    size: (
      <MultiSelect
        isWider={true}
        isSearchable={false}
        id={"limits"}
        options={PAGE_SIZES}
        placeholder={""}
        selectedValue={limit}
        isMultiple={false}
        onChange={(e) => setLimit(e.value as string)}
        valueKey="value"
        labelKey="name"
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
