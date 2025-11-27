import s from "./AdminList.module.scss";
import PrettyButton from "../../../../../../shared/components/ui/PrettyButton/PrettyButton.tsx";
import { Trans } from "react-i18next";
import PanelItem from "../PanelItem/PanelItem.tsx";
import { useSearchParams } from "react-router-dom";
import LoaderOverlay from "../../../../../../shared/components/ui/LoaderOverlay/LoaderOverlay.tsx";
import { ParamsType } from "../../../../../../shared/api/adminApi/types.ts";
import Loader from "../../../../../../shared/components/ui/Loader/Loader.tsx";
import ListController from "../../../../../../shared/components/list/ListController/ListController.tsx";
import {
  FILTER_PARAM_KEYS,
  FilterKeys,
} from "../../../../../../shared/common/helpers/commonConstants.ts";
import { Alert } from "../../../../../../shared/components/ui/Alert/Alert.tsx";
import { ErrorIcon } from "../../../../../../shared/assets/icons";
import { PATHS } from "../../../../../../app/routes/routes.ts";
import { FiltersData } from "../../../../../../shared/components/filters/types.ts";

interface AdminListProps<T> {
  data: any;
  itemName: string;
  itemLink: (item: T) => string;
  onFetch: (params: ParamsType) => void;
  onCreate: () => void;
  loading: boolean;
  showLanguageFilter?: boolean;
  handleToggle?: (value: number, isHidden: boolean) => void;
  showToggle?: boolean;
  filtersData: FiltersData;
  transKey:
    | "landings"
    | "courses"
    | "books"
    | "bookLandings"
    | "authors"
    | "users";
}

const SIZE = 10;

const AdminList = <T extends { id: number; [key: string]: any }>({
  data,
  itemName,
  itemLink,
  onFetch,
  onCreate,
  loading,
  handleToggle,
  filtersData,
  showLanguageFilter = false,
  showToggle = false,
  transKey,
}: AdminListProps<T>) => {
  const [searchParams, setSearchParams] = useSearchParams();
  const SEARCH_KEY = `admin.${transKey}`;
  const itemsList = data.list as T[];
  const isBook = transKey.includes("bookL");

  const handleCreateItem = async () => {
    try {
      await onCreate();
      const newParams = new URLSearchParams(searchParams);
      newParams.set("page", "1");
      newParams.delete(FILTER_PARAM_KEYS.language);
      setSearchParams(newParams, { replace: true });
      onFetch({
        page: 1,
        size: SIZE,
      });
    } catch (err: any) {
      Alert(
        `Error creating ${transKey?.slice(0, -1)}, error message: ${err.message}`,
        <ErrorIcon />,
      );
    }
  };

  const filters: FilterKeys[] = ["size"];

  if (showLanguageFilter) {
    filters.unshift("language");
  }

  return (
    <div className={s.list_container}>
      <div className={s.list_header}>
        <PrettyButton
          variant={"primary"}
          text={`admin.${transKey}.create`}
          onClick={handleCreateItem}
        />
      </div>
      <ListController
        type={SEARCH_KEY}
        loadData={(params) => onFetch(params)}
        pagination={{
          total: data.total,
          total_pages: data.total_pages,
          page: data.page,
          size: data.size,
        }}
        filtersData={filtersData}
      >
        <div className={s.list}>
          {loading && (
            <>
              <LoaderOverlay />
            </>
          )}
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
