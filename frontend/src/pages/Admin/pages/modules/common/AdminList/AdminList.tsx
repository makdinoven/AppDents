import s from "./AdminList.module.scss";
import PrettyButton from "../../../../../../shared/components/ui/PrettyButton/PrettyButton";
import { Trans } from "react-i18next";
import PanelItem from "../PanelItem/PanelItem";
import LoaderOverlay from "../../../../../../shared/components/ui/LoaderOverlay/LoaderOverlay";
import Loader from "../../../../../../shared/components/ui/Loader/Loader";
import ListController from "../../../../../../shared/components/list/ListController/ListController";
import Pagination from "../../../../../../shared/components/list/Pagination/Pagination";
import { Alert } from "../../../../../../shared/components/ui/Alert/Alert";
import { ErrorIcon } from "../../../../../../shared/assets/icons";
import { PATHS } from "../../../../../../app/routes/routes";
import { useEffect } from "react";
import { useListQueryParams } from "../../../../../../shared/components/list/model/useListQueryParams";
import { LANGUAGES_NAME } from "../../../../../../shared/common/helpers/commonConstants.ts";
import Search from "../../../../../../shared/components/ui/Search/Search.tsx";
import useDebounce from "../../../../../../shared/common/hooks/useDebounce.ts";
import { ParamsType } from "../../../../../../shared/api/adminApi/types.ts";
import MultiSelect from "../../../../../../shared/components/ui/MultiSelect/MultiSelect.tsx";

interface AdminListProps<T> {
  data: any;
  itemName: string;
  itemLink: (item: T) => string;
  onLoad: (params: any) => void;
  onSearch: (params: any) => void;
  onCreate: () => void;
  loading: boolean;
  showLanguageFilter?: boolean;
  handleToggle?: (value: number, isHidden: boolean) => void;
  showToggle?: boolean;
  transKey:
    | "landings"
    | "courses"
    | "books"
    | "bookLandings"
    | "authors"
    | "users";
}

const SIZE = 12;

const AdminList = <T extends { id: number; [key: string]: any }>({
  data,
  itemName,
  itemLink,
  onLoad,
  onSearch,
  onCreate,
  loading,
  handleToggle,
  showLanguageFilter = false,
  showToggle = false,
  transKey,
}: AdminListProps<T>) => {
  const { params, actions } = useListQueryParams({
    defaultPage: 1,
    defaultPageSize: SIZE,
  });
  const debouncedQ = useDebounce(params.q, 500);

  const itemsList = data.list as T[];
  const isBook = transKey.includes("bookL");

  const handleCreateItem = async () => {
    try {
      await onCreate();
      actions.resetAll();

      onLoad({
        page: 1,
        size: SIZE,
      });
    } catch (err: any) {
      Alert(
        `Error creating ${transKey?.slice(0, -1)}, message: ${err.message}`,
        <ErrorIcon />,
      );
    }
  };

  const loadData = (params: ParamsType, debQ: string) => {
    const hasSearch = params.q !== undefined && params.q !== "";
    if (hasSearch && params.q === debQ) {
      if (params.page !== 1) {
        actions.set({ page: 1 });
        return;
      }
      onSearch({ q: params.q });
    } else if (!hasSearch && !debQ) {
      onLoad({
        ...params,
        language: params.language === "all" ? undefined : params.language,
      });
    }
  };

  useEffect(() => {
    loadData(params, debouncedQ);
  }, [params, debouncedQ]);

  return (
    <div className={s.list_container}>
      <ListController
        filtersSlot={
          <div className={s.filters_container}>
            <div className={s.filters_top}>
              {showLanguageFilter && (
                <MultiSelect
                  isSearchable={false}
                  id={"language"}
                  options={LANGUAGES_NAME}
                  placeholder={"Choose a language"}
                  selectedValue={params.language}
                  isMultiple={false}
                  onChange={(e) => actions.set({ language: e.value })}
                  valueKey="value"
                  labelKey="name"
                />
              )}

              <PrettyButton
                variant="primary"
                text={`admin.${transKey}.create`}
                onClick={handleCreateItem}
              />
            </div>
            <Search placeholder={`admin.${transKey}.search`} id={"q"} />
          </div>
        }
        paginationSlot={
          <Pagination
            onPageChange={(p) => actions.set({ page: p })}
            onSizeChange={(s) => actions.set({ size: s })}
            pagination={{
              page: params.page,
              size: params.size,
              total: data.total,
              total_pages: data.total_pages,
            }}
          />
        }
      >
        <div className={s.list}>
          {loading && <LoaderOverlay />}

          {itemsList.length > 0 ? (
            itemsList.map((item) => (
              <PanelItem
                id={item.id}
                name={item[itemName]}
                landingPath={
                  item.page_name
                    ? isBook
                      ? PATHS.BOOK_LANDING_CLIENT.build(item.page_name)
                      : PATHS.LANDING_CLIENT.build(item.page_name)
                    : undefined
                }
                promoLandingPath={
                  item.page_name
                    ? isBook
                      ? PATHS.BOOK_LANDING.build(item.page_name)
                      : PATHS.LANDING.build(item.page_name)
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
            ))
          ) : !loading ? (
            <p className={s.not_found}>
              <Trans i18nKey={`admin.${transKey}.notFound`} />
            </p>
          ) : (
            <Loader />
          )}
        </div>
      </ListController>
    </div>
  );
};

export default AdminList;
