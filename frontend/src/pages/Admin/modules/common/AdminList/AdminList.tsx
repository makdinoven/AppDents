import { useEffect, useRef, useState } from "react";
import s from "./AdminList.module.scss";
import Search from "../../../../../components/ui/Search/Search.tsx";
import PrettyButton from "../../../../../components/ui/PrettyButton/PrettyButton.tsx";
import { Trans } from "react-i18next";
import PanelItem from "../PanelItem/PanelItem.tsx";
import { Path } from "../../../../../routes/routes.ts";
import { useSearchParams } from "react-router-dom";
import LoaderOverlay from "../../../../../components/ui/LoaderOverlay/LoaderOverlay.tsx";
import Pagination from "../../../../../components/ui/Pagination/Pagination.tsx";
import { ParamsType } from "../../../../../api/adminApi/types.ts";
import useDebounce from "../../../../../common/hooks/useDebounce.ts";
import Loader from "../../../../../components/ui/Loader/Loader.tsx";

interface AdminListProps<T> {
  data: any;
  itemName: string;
  itemLink: (item: T) => string;
  onFetch: (params: ParamsType) => void;
  onCreate: () => void;
  onSearch: (params: ParamsType) => void;
  loading: boolean;
  handleToggle?: (value: number, isHidden: boolean) => void;
  showToggle?: boolean;
}

const AdminList = <T extends { id: number; [key: string]: any }>({
  data,
  itemName,
  itemLink,
  onFetch,
  onCreate,
  onSearch,
  loading,
  handleToggle,
  showToggle = false,
}: AdminListProps<T>) => {
  const [searchParams, setSearchParams] = useSearchParams();
  const tab = searchParams.get("tab");
  const pageFromUrl = parseInt(searchParams.get("page") || "1", 10);
  const [searchValue, setSearchValue] = useState("");
  const debouncedSearchValue = useDebounce(searchValue, 300);
  const itemsList = data.list as T[];
  const getParams = () => ({
    page: pageFromUrl,
    size: 10,
  });
  const isFirstRender = useRef(true);

  const setFirstPageSearchParams = () => {
    const newParams = new URLSearchParams(searchParams);
    newParams.set("page", "1");
    setSearchParams(newParams);
  };

  useEffect(() => {
    if (!debouncedSearchValue) {
      onFetch(getParams());
    }
  }, [pageFromUrl, tab]);

  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }

    if (debouncedSearchValue) {
      setFirstPageSearchParams();
      onSearch({
        page: 1,
        size: 10,
        q: debouncedSearchValue,
      });
    } else {
      onFetch(getParams());
    }
  }, [debouncedSearchValue]);

  const handleCreateItem = async () => {
    await onCreate();
    setFirstPageSearchParams();
  };

  return (
    <div className={s.list_container}>
      <div className={s.list_header}>
        <div className={s.list_header_inner}>
          <Search
            placeholder={`admin.${tab}.search`}
            value={searchValue}
            onChange={(e: any) => setSearchValue(e.target.value)}
          />
          <PrettyButton
            variant={"primary"}
            text={`admin.${tab}.create`}
            onClick={handleCreateItem}
          />
        </div>
      </div>
      <div className={s.list}>
        {loading && (
          <>
            <LoaderOverlay />
          </>
        )}
        {itemsList.length > 0 ? (
          <>
            <span className={s.total_count}>
              <Trans i18nKey={`admin.${tab}.found`} /> {data.total}
            </span>
            {itemsList.map((item) => (
              <PanelItem
                id={item.id}
                name={item[itemName]}
                landingPath={
                  item.page_name
                    ? `${Path.landing}/${item.page_name}`
                    : undefined
                }
                key={item.id}
                handleToggle={(value: number) =>
                  handleToggle && handleToggle(value, !item.is_hidden)
                }
                isHidden={item.is_hidden}
                showToggle={showToggle}
                link={itemLink(item)}
              />
            ))}
            <Pagination totalPages={data.total_pages} />
          </>
        ) : !loading ? (
          <Trans i18nKey={`admin.${tab}.notFound`} />
        ) : (
          <Loader />
        )}
      </div>
    </div>
  );
};

export default AdminList;
