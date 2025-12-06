import s from "./Books.module.scss";
import { useSelector } from "react-redux";
import { AppRootStateType } from "../../shared/store/store.ts";
import { useEffect, useState } from "react";
import ListController from "../../shared/components/list/ListController/ListController.tsx";
import CardsList from "../../shared/components/ProductsSection/CardsList/CardsList.tsx";
import { mainApi } from "../../shared/api/mainApi/mainApi.ts";
import DetailHeader from "../Admin/pages/modules/common/DetailHeader/DetailHeader.tsx";
import ProductsSection from "../../shared/components/ProductsSection/ProductsSection.tsx";
import CustomOrder from "../../shared/components/CustomOrder/CustomOrder.tsx";
import Pagination, {
  PaginationType,
} from "../../shared/components/list/Pagination/Pagination.tsx";
import FiltersPanel from "../../shared/components/filters/FiltersPanel/FiltersPanel.tsx";
import { useListQueryParams } from "../../shared/components/list/model/useListQueryParams.ts";
import {
  mapBackendFilters,
  mapBackendSelected,
} from "../../shared/components/filters/model/mapBackendFilters.ts";
import {
  FiltersDataUI,
  SelectedUI,
} from "../../shared/components/filters/model/types.ts";
import BookCardSkeletons from "../../shared/components/ui/Skeletons/BookCardSkeletons/BookCardSkeletons.tsx";
import FiltersSkeleton from "../../shared/components/ui/Skeletons/FiltersSkeleton/FiltersSkeleton.tsx";

const Books = () => {
  const { language } = useSelector((state: AppRootStateType) => state.user);
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isFirstLoad, setIsFirstLoad] = useState(true);
  const [pagination, setPagination] = useState<PaginationType | null>(null);
  const [filters, setFilters] = useState<FiltersDataUI | null>(null);
  const [selectedFilters, setSelectedFilters] = useState<SelectedUI[] | null>(
    null,
  );
  const { params, actions } = useListQueryParams();

  const loadBooks = async () => {
    setLoading(true);
    try {
      const res = await mainApi.getBookLandingCardsV2({
        ...params,
        language: language,
        include_filters: true,
      });
      setBooks(res.data.cards);
      setFilters(mapBackendFilters(res.data.filters));
      setSelectedFilters(mapBackendSelected(res.data.filters.selected));
      setPagination({
        total: res.data.total,
        total_pages: res.data.total_pages,
        page: res.data.page,
        size: res.data.size,
      });
    } catch (error) {
      console.log(error);
    } finally {
      setIsFirstLoad(false);
      setLoading(false);
    }
  };

  useEffect(() => {
    loadBooks();
  }, [params, language]);

  useEffect(() => {
    if (params.page !== 1) {
      actions.set({ page: 1 });
    }
  }, [language]);

  return (
    <div lang={language.toLowerCase()} className={s.books}>
      <DetailHeader showBackButton={false} title={"books.title"} />
      <ListController
        filtersSlot={
          !filters && loading ? (
            <FiltersSkeleton />
          ) : (
            <FiltersPanel
              loading={loading}
              totalItems={pagination?.total ? pagination.total : 0}
              actions={actions}
              searchPlaceholder={`books.search`}
              filtersData={filters}
              selectedFilters={selectedFilters}
              params={params}
            />
          )
        }
        paginationSlot={
          pagination && (
            <Pagination
              onPageChange={(p) => actions.set({ page: p })}
              onSizeChange={(s) => actions.set({ size: s })}
              pagination={{
                page: params.page,
                size: params.size,
                total: pagination.total,
                total_pages: pagination.total_pages,
              }}
            />
          )
        }
      >
        {loading && !selectedFilters ? (
          <BookCardSkeletons amount={Number(params.size)} />
        ) : (
          <CardsList
            showLoaderOverlay={loading}
            loading={loading}
            showSeeMore={false}
            showEndOfList={false}
            cards={books}
            productCardFlags={{ isClient: true }}
            cardType={"book"}
          />
        )}
      </ListController>
      {!isFirstLoad && (
        <>
          <ProductsSection
            showSort={true}
            sectionTitle={"other.otherBooks"}
            pageSize={4}
            productCardFlags={{ isClient: true, isOffer: true }}
            cardType={"book"}
          />
          <CustomOrder />
        </>
      )}
    </div>
  );
};

export default Books;
