import { useEffect } from "react";
import s from "./AdminList.module.scss";
import Search from "../../../../../components/ui/Search/Search.tsx";
import Loader from "../../../../../components/ui/Loader/Loader.tsx";
import PrettyButton from "../../../../../components/ui/PrettyButton/PrettyButton.tsx";
import { useSearch } from "../../../../../common/hooks/useSearch.ts";
import { t } from "i18next";
import { Trans } from "react-i18next";
import PanelItem from "../PanelItem/PanelItem.tsx";
import { Path } from "../../../../../routes/routes.ts";

interface AdminListProps<T> {
  items: T[];
  searchField: keyof T;
  itemName: string;
  itemLink: (item: T) => string;
  onFetch: () => void;
  onCreate: () => void;
  searchPlaceholder: string;
  createButtonText: string;
  notFoundText: string;
  loading: boolean;
  handleToggle?: (value: number, isHidden: boolean) => void;
  showToggle?: boolean;
}

const AdminList = <T extends { id: number; [key: string]: any }>({
  items,
  searchField,
  itemName,
  itemLink,
  onFetch,
  onCreate,
  searchPlaceholder,
  createButtonText,
  notFoundText,
  loading,
  handleToggle,
  showToggle = false,
}: AdminListProps<T>) => {
  const { searchQuery, setSearchQuery, filteredItems } = useSearch(items, [
    searchField as string,
  ]);

  useEffect(() => {
    onFetch();
  }, []);

  return (
    <div className={s.list}>
      <div className={s.list_header}>
        <Search
          placeholder={searchPlaceholder}
          value={searchQuery}
          onChange={(e: any) => setSearchQuery(e.target.value)}
        />
        <PrettyButton
          variant={"primary"}
          text={t(createButtonText)}
          onClick={onCreate}
        />
      </div>
      {loading ? (
        <Loader />
      ) : filteredItems.length > 0 ? (
        filteredItems.map((item) => (
          <PanelItem
            id={item.id}
            name={item[itemName]}
            landingPath={
              item.page_name ? `${Path.landing}/${item.page_name}` : undefined
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
      ) : (
        <Trans i18nKey={notFoundText} />
      )}
    </div>
  );
};

export default AdminList;
