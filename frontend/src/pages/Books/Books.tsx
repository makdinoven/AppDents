import s from "./Books.module.scss";
import { useSelector } from "react-redux";
import { AppRootStateType } from "../../store/store.ts";
import { useState } from "react";
import ListController from "../../components/ui/ListController/ListController.tsx";
import CardsList from "../../components/ProductsSection/CardsList/CardsList.tsx";
import { ParamsType } from "../../api/adminApi/types.ts";
import { mainApi } from "../../api/mainApi/mainApi.ts";
import BookCardSkeletons from "../../components/ui/Skeletons/BookCardSkeletons/BookCardSkeletons.tsx";
import DetailHeader from "../Admin/pages/modules/common/DetailHeader/DetailHeader.tsx";
import ProductsSection from "../../components/ProductsSection/ProductsSection.tsx";

const Books = () => {
  const { language } = useSelector((state: AppRootStateType) => state.user);
  const [books, setBooks] = useState([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [loading, setLoading] = useState(true);
  const [isFirstLoad, setIsFirstLoad] = useState(true);

  const loadBooks = async (params: ParamsType) => {
    setLoading(true);
    try {
      const paramsToSend = { ...params, mode: "page" };
      const res = await mainApi.getBookLandingCards(paramsToSend);

      setBooks(res.data.cards);
      setTotal(res.data.total);
      setTotalPages(res.data.total_pages);
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
        size={12}
        type="books"
        loadData={(params) => loadBooks(params)}
        total={total}
        totalPages={totalPages}
        SkeletonComponent={BookCardSkeletons}
        loading={loading}
        filters={["tags", "sort", "size"]}
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
        <ProductsSection
          showSort={true}
          sectionTitle={"other.otherBooks"}
          pageSize={4}
          productCardFlags={{ isClient: true, isOffer: true }}
          cardType={"book"}
        />
      )}
    </div>
  );
};

export default Books;
