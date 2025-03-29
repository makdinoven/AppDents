import s from "./CoursePage.module.scss";
import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import { adminApi } from "../../api/adminApi/adminApi.ts";
import { normalizeCourse } from "../../common/helpers/helpers.ts";
import Loader from "../../components/ui/Loader/Loader.tsx";
import DetailHeader from "../Admin/modules/common/DetailHeader/DetailHeader.tsx";
import { getMe } from "../../store/actions/userActions.ts";
import { useDispatch } from "react-redux";
import { AppDispatchType } from "../../store/store.ts";
import SectionHeader from "../../components/ui/SectionHeader/SectionHeader.tsx";
import CourseCard from "../ProfilePage/modules/CourseCard/CourseCard.tsx";

const CoursePage = () => {
  const dispatch = useDispatch<AppDispatchType>();
  const { courseId } = useParams();
  const [course, setCourse] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  // const changeLanguage = (lang: string) => {
  //   i18n.changeLanguage(lang);
  // };

  useEffect(() => {
    if (courseId) {
      fetchData();
    }
  }, [dispatch, courseId]);

  const fetchData = async () => {
    try {
      await dispatch(getMe());
      await fetchCourseData();
    } catch (error) {
      console.error(error);
    }
  };

  const fetchCourseData = async () => {
    try {
      const res = await adminApi.getCourse(courseId);
      setCourse(normalizeCourse(res.data));
      // changeLanguage(res.data.language.toLowerCase());
      setLoading(false);
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <>
      {loading ? (
        <Loader />
      ) : (
        <div className={s.course_page}>
          <DetailHeader title={course?.name} />
          <ul className={s.modules_list}>
            {course.sections.map((section: any) => (
              <li key={section.id}>
                <SectionHeader name={section.section_name} />
                <ul>
                  {section.lessons.map((lesson: any, index: number) => (
                    <CourseCard
                      isEven={index % 2 === 0}
                      key={lesson.id}
                      name={lesson.lesson_name}
                      link={lesson.video_link}
                      viewText={"watchLesson"}
                    />
                  ))}
                </ul>
              </li>
            ))}
          </ul>
        </div>
      )}
    </>
  );
};

export default CoursePage;
