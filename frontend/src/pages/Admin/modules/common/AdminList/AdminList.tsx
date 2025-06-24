import s from "./AdminList.module.scss";
import PrettyButton from "../../../../../components/ui/PrettyButton/PrettyButton.tsx";
import { Trans } from "react-i18next";
import PanelItem from "../PanelItem/PanelItem.tsx";
import { Path } from "../../../../../routes/routes.ts";
import { useSearchParams } from "react-router-dom";
import LoaderOverlay from "../../../../../components/ui/LoaderOverlay/LoaderOverlay.tsx";
import { ParamsType } from "../../../../../api/adminApi/types.ts";
import Loader from "../../../../../components/ui/Loader/Loader.tsx";
import ListController from "../../../../../components/ui/ListController/ListController.tsx";
import {
  FILTER_PARAM_KEYS,
  FilterKeys,
} from "../../../../../common/helpers/commonConstants.ts";
import { getAlert } from "../../../../../common/helpers/helpers.tsx";
import ErrorIcon from "../../../../../assets/Icons/ErrorIcon.tsx";

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
  showLanguageFilter = false,
  showToggle = false,
}: AdminListProps<T>) => {
  const [searchParams, setSearchParams] = useSearchParams();
  const tab = searchParams.get("tab");
  const SEARCH_KEY = `admin.${tab}`;
  const itemsList = data.list as T[];

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
      getAlert(
        `Error creating ${tab?.slice(0, -1)}, error message: ${err.message}`,
        <ErrorIcon />
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
          text={`admin.${tab}.create`}
          onClick={handleCreateItem}
        />
      </div>
      <ListController
        type={SEARCH_KEY}
        loadData={(params) => onFetch(params)}
        total={data.total}
        totalPages={data.total_pages}
        size={SIZE}
        filters={filters}
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
                    ? `/${Path.landingClient}/${item.page_name}`
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
              <Trans i18nKey={`admin.${tab}.notFound`} />
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
