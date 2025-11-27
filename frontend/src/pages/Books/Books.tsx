import s from "./Books.module.scss";
import { useSelector } from "react-redux";
import { AppRootStateType } from "../../shared/store/store.ts";
import { useState } from "react";
import ListController from "../../shared/components/list/ListController/ListController.tsx";
import CardsList from "../../shared/components/ProductsSection/CardsList/CardsList.tsx";
import { mainApi } from "../../shared/api/mainApi/mainApi.ts";
import BookCardSkeletons from "../../shared/components/ui/Skeletons/BookCardSkeletons/BookCardSkeletons.tsx";
import DetailHeader from "../Admin/pages/modules/common/DetailHeader/DetailHeader.tsx";
import ProductsSection from "../../shared/components/ProductsSection/ProductsSection.tsx";
import CustomOrder from "../../shared/components/CustomOrder/CustomOrder.tsx";
import { BookCardsParams } from "../../shared/api/mainApi/types.ts";
import { PaginationType } from "../../shared/components/list/Pagination/Pagination.tsx";

const Books = () => {
  const { language } = useSelector((state: AppRootStateType) => state.user);
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isFirstLoad, setIsFirstLoad] = useState(true);
  const [pagination, setPagination] = useState<PaginationType | null>(null);
  const [filters, setFilters] = useState<any>(null);

  const loadBooks = async (params: BookCardsParams) => {
    setLoading(true);
    try {
      const res = await mainApi.getBookLandingCardsV2({
        ...params,
        include_filters: true,
      });
      setBooks(res.data.cards);
      setFilters(res.data.filters);
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

  return (
    <div lang={language.toLowerCase()} className={s.books}>
      <DetailHeader title={"books.title"} />
      <ListController
        language={language}
        type="books"
        loadData={(params) => loadBooks(params)}
        SkeletonComponent={BookCardSkeletons}
        loading={loading}
        pagination={pagination}
        filtersData={filters}
      >
        <CardsList
          loading={loading}
          showSeeMore={false}
          showEndOfList={false}
          cards={books}
          productCardFlags={{ isClient: true }}
          cardType={"book"}
        />
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
