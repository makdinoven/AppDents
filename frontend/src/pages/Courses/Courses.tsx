import s from "./Courses.module.scss";
import { useDispatch, useSelector } from "react-redux";
import { AppDispatchType, AppRootStateType } from "../../store/store.ts";
import { useEffect, useState } from "react";
import { ParamsType } from "../../api/adminApi/types.ts";
import DetailHeader from "../Admin/pages/modules/common/DetailHeader/DetailHeader.tsx";
import ListController from "../../components/ui/ListController/ListController.tsx";
import CardsList from "../../components/ProductsSection/CardsList/CardsList.tsx";
import { mainApi } from "../../api/mainApi/mainApi.ts";
import { useNavigate } from "react-router-dom";
import { Path } from "../../routes/routes.ts";
import { getCourses } from "../../store/actions/userActions.ts";
import ProductsSection from "../../components/ProductsSection/ProductsSection.tsx";
import CourseCardSkeletons from "../../components/ui/Skeletons/CourseCardSkeletons/CourseCardSkeletons.tsx";

const Courses = ({ isFree }: { isFree: boolean }) => {
  const navigate = useNavigate();
  const dispatch = useDispatch<AppDispatchType>();
  const { language, isLogged, role } = useSelector(
    (state: AppRootStateType) => state.user,
  );
  const userCourses = useSelector(
    (state: AppRootStateType) => state.user.courses,
  );
  const [courses, setCourses] = useState([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [loading, setLoading] = useState(true);
  const [isFirstLoad, setIsFirstLoad] = useState(true);
  const isAdmin = role === "admin";

  useEffect(() => {
    if (isLogged && isFree && !isAdmin) {
      dispatch(getCourses());
    }
  }, [isLogged]);

  useEffect(() => {
    if (userCourses.length > 0 && isFree && !isAdmin) {
      navigate(Path.courses);
    }
  }, [userCourses]);

  const loadCourses = async (params: ParamsType) => {
    setLoading(true);
    try {
      const paramsToSend = { ...params, single_course: isFree };
      const res = await mainApi.getLandingCards(paramsToSend);

      setCourses(res.data.cards);
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
    <div lang={language.toLowerCase()} className={s.courses}>
      <DetailHeader title={"courses.title"} />
      <ListController
        language={language}
        size={10}
        type="courses"
        loadData={(params) => loadCourses(params)}
        total={total}
        totalPages={totalPages}
        filters={["tags", "sort", "size"]}
        SkeletonComponent={CourseCardSkeletons}
        skeletonProps={{ shape: true }}
        loading={loading}
      >
        <CardsList
          productCardFlags={{ isFree: isFree, isClient: true }}
          cardType={"course"}
          loading={loading}
          showSeeMore={false}
          showEndOfList={false}
          cards={courses}
        />
      </ListController>
      {!isFirstLoad && (
        <ProductsSection
          showSort={true}
          cardType={"course"}
          productCardFlags={{ isFree: isFree, isOffer: true, isClient: true }}
          sectionTitle={"other.otherCourses"}
          pageSize={4}
        />
      )}
    </div>
  );
};

export default Courses;
