import s from "./Courses.module.scss";
import { useSelector } from "react-redux";
import { AppRootStateType } from "../../store/store.ts";
import { useState } from "react";
import { ParamsType } from "../../api/adminApi/types.ts";
import DetailHeader from "../Admin/modules/common/DetailHeader/DetailHeader.tsx";
import ListController from "../../components/ui/ListController/ListController.tsx";
import CoursesSection from "../../components/CommonComponents/CoursesSection/CoursesSection.tsx";
import CardsList from "../../components/CommonComponents/CoursesSection/CardsList/CardsList.tsx";
import { mainApi } from "../../api/mainApi/mainApi.ts";

const SIZE = 12;

const Courses = () => {
  const language = useSelector(
    (state: AppRootStateType) => state.user.language,
  );
  const [courses, setCourses] = useState([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [loading, setLoading] = useState(false);
  const [isFirstLoad, setIsFirstLoad] = useState(true);

  const loadCourses = async ({ page, language, q, size }: ParamsType) => {
    setLoading(true);
    try {
      const params = { language, page, size, q };
      const res = await mainApi.getCoursesPagination(params);

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
        size={SIZE}
        type="courses"
        loadData={(params) => loadCourses(params)}
        total={total}
        totalPages={totalPages}
        // filters={["tags", "sort", "size"]}
      >
        <CardsList
          isClient={true}
          loading={loading}
          showSeeMore={false}
          showEndOfList={false}
          cards={courses}
        />
      </ListController>
      {!isFirstLoad && (
        <CoursesSection
          isOffer={true}
          showSort={true}
          sectionTitle={"other.otherCourses"}
          pageSize={4}
        />
      )}
    </div>
  );
};

export default Courses;
