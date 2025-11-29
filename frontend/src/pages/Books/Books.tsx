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
import { mapBackendFilters } from "../../shared/components/filters/mapBackendFilters.ts";
import { FiltersDataUI } from "../../shared/components/filters/types.ts";
import BookCardSkeletons from "../../shared/components/ui/Skeletons/BookCardSkeletons/BookCardSkeletons.tsx";

const Books = () => {
  const { language } = useSelector((state: AppRootStateType) => state.user);
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isFirstLoad, setIsFirstLoad] = useState(true);
  const [pagination, setPagination] = useState<PaginationType | null>(null);
  const [filters, setFilters] = useState<FiltersDataUI | null>(null);
  const { params, actions } = useListQueryParams();

  const loadBooks = async () => {
    setLoading(true);
    try {
      const res = await mainApi.getBookLandingCardsV2({
        ...params,
        include_filters: true,
      });
      setBooks(res.data.cards);
      setFilters(mapBackendFilters(res.data.filters));
      setPagination({
        total: res.data.total,
        total_pages: res.data.total_pages,
        page: res.data.page,
        size: res.data.size,
      });
      setIsFirstLoad(false);
    } catch (error) {
      console.log(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadBooks();
  }, [params]);

  return (
    <div lang={language.toLowerCase()} className={s.books}>
      <DetailHeader title={"books.title"} />
      <ListController
        filtersSlot={
          filters && (
            <FiltersPanel
              actions={actions}
              searchKey={"search"}
              searchPlaceholder={`books.search`}
              filtersData={filters}
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
        {loading ? (
          <BookCardSkeletons amount={Number(params.size)} />
        ) : (
          <CardsList
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
