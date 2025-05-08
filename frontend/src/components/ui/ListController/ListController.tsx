import s from "./ListController.module.scss";
import Search from "../Search/Search.tsx";
import { Trans } from "react-i18next";
import Pagination from "../Pagination/Pagination.tsx";
import { useSearchParams } from "react-router-dom";
import useDebounce from "../../../common/hooks/useDebounce.ts";
import { useEffect, useRef } from "react";
import { ParamsType } from "../../../api/adminApi/types.ts";

type ListControllerProps = {
  type: string;
  loadData: (params: ParamsType) => void;
  total: number;
  totalPages: number;
  size: number;
  language?: string;
  children: React.ReactNode;
};

const ListController = ({
  type,
  loadData,
  children,
  language,
  size,
  total,
  totalPages,
}: ListControllerProps) => {
  const SEARCH_KEY = `${type}_search`;
  const [searchParams, setSearchParams] = useSearchParams();
  const pageFromUrl = parseInt(searchParams.get("page") || "1");
  const searchValue = searchParams.get(SEARCH_KEY);
  const debouncedSearchValue = useDebounce(searchValue, 300);
  const prevLanguage = useRef<string | undefined>("");
  const prevSearch = useRef(debouncedSearchValue);

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

  return (
    <div className={s.list_controller_container}>
      <div className={s.search_container}>
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
