import s from "./Books.module.scss";
import { useSelector } from "react-redux";
import { AppRootStateType } from "../../store/store.ts";
import { useState } from "react";
import DetailHeader from "../Admin/modules/common/DetailHeader/DetailHeader.tsx";
import ListController from "../../components/ui/ListController/ListController.tsx";
import CardsList from "../../components/ProductsSection/CardsList/CardsList.tsx";
import ProductsSection from "../../components/ProductsSection/ProductsSection.tsx";
import { ParamsType } from "../../api/adminApi/types.ts";
import { mainApi } from "../../api/mainApi/mainApi.ts";
import BookCardSkeletons from "../../components/ui/Skeletons/BookCardSkeletons/BookCardSkeletons.tsx";

const Books = () => {
  // const navigate = useNavigate();
  // const dispatch = useDispatch<AppDispatchType>();
  const {
    language,
    // , isLogged, role
  } = useSelector((state: AppRootStateType) => state.user);
  // const userBooks = useSelector(
  //   (state: AppRootStateType) => state.user.books,
  // );
  const [books, setBooks] = useState([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [loading, setLoading] = useState(false);
  const [isFirstLoad, setIsFirstLoad] = useState(true);
  // const isAdmin = role === "admin";

  // useEffect(() => {
  //   if (isLogged && !isAdmin) {
  //     dispatch(getBooks());
  //   }
  // }, [isLogged]);

  // useEffect(() => {
  //   if (userBooks.length > 0 && !isAdmin) {
  //     navigate(Path.books);
  //   }
  // }, [userBooks]);

  const loadBooks = async (params: ParamsType) => {
    setLoading(true);
    try {
      const paramsToSend = { ...params };
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
