import s from "./Books.module.scss";
import { useDispatch, useSelector } from "react-redux";
import { AppDispatchType, AppRootStateType } from "../../store/store.ts";
import { useEffect } from "react";
import DetailHeader from "../Admin/modules/common/DetailHeader/DetailHeader.tsx";
import { useNavigate } from "react-router-dom";
import { Path } from "../../routes/routes.ts";
import { getCourses } from "../../store/actions/userActions.ts";

const Books = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch<AppDispatchType>();
  const { language, isLogged, role } = useSelector(
    (state: AppRootStateType) => state.user,
  );
  const userCourses = useSelector(
    (state: AppRootStateType) => state.user.courses,
  );
  // const [courses, setCourses] = useState([]);
  // const [total, setTotal] = useState(0);
  // const [totalPages, setTotalPages] = useState(0);
  // const [loading, setLoading] = useState(false);
  // const [isFirstLoad, setIsFirstLoad] = useState(true);
  const isAdmin = role === "admin";

  useEffect(() => {
    if (isLogged && !isAdmin) {
      dispatch(getCourses());
    }
  }, [isLogged]);

  useEffect(() => {
    if (userCourses.length > 0 && !isAdmin) {
      navigate(Path.courses);
    }
  }, [userCourses]);

  // const loadCourses = async (params: ParamsType) => {
  //   setLoading(true);
  //   try {
  //     const paramsToSend = { ...params };
  //     const res = await mainApi.getLandingCards(paramsToSend);
  //
  //     setCourses(res.data.cards);
  //     setTotal(res.data.total);
  //     setTotalPages(res.data.total_pages);
  //     setIsFirstLoad(false);
  //   } catch (error) {
  //     console.log(error);
  //   } finally {
  //     setLoading(false);
  //   }
  // };

  return (
    <div lang={language.toLowerCase()} className={s.courses}>
      <DetailHeader title={"books.title"} />
      {/*<ListController*/}
      {/*  language={language}*/}
      {/*  size={10}*/}
      {/*  type="books"*/}
      {/*  loadData={(params) => loadCourses(params)}*/}
      {/*  total={total}*/}
      {/*  totalPages={totalPages}*/}
      {/*  filters={["tags", "sort", "size"]}*/}
      {/*>*/}
      {/*<CardsList*/}
      {/*  isBook={true}*/}
      {/*  isClient={true}*/}
      {/*  loading={loading}*/}
      {/*  showSeeMore={false}*/}
      {/*  showEndOfList={false}*/}
      {/*  cards={courses}*/}
      {/*/>*/}
      {/*</ListController>*/}
      {/*{!isFirstLoad && (*/}
      {/*  <CoursesSection*/}
      {/*    isBook={true}*/}
      {/*    isOffer={true}*/}
      {/*    showSort={true}*/}
      {/*    sectionTitle={"other.otherBooks"}*/}
      {/*    pageSize={4}*/}
      {/*  />*/}
      {/*)}*/}
    </div>
  );
};

export default Books;
