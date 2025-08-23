import s from "./CoursePage.module.scss";
import { Outlet, useNavigate, useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import { adminApi } from "../../../../api/adminApi/adminApi.ts";
import { normalizeCourse } from "../../../../common/helpers/helpers.ts";
import Loader from "../../../../components/ui/Loader/Loader.tsx";
import DetailHeader from "../../../Admin/modules/common/DetailHeader/DetailHeader.tsx";
import SectionHeader from "../../../../components/ui/SectionHeader/SectionHeader.tsx";
import { Path } from "../../../../routes/routes.ts";
import LessonCard from "./LessonCard/LessonCard.tsx";
import { useDispatch } from "react-redux";
import { AppDispatchType } from "../../../../store/store.ts";
import { setPaymentData } from "../../../../store/slices/paymentSlice.ts";
import { PAGE_SOURCES } from "../../../../common/helpers/commonConstants.ts";
import { usePaymentPageHandler } from "../../../../common/hooks/usePaymentPageHandler.ts";

const CoursePage = () => {
  const { openPaymentModal } = usePaymentPageHandler();
  const dispatch = useDispatch<AppDispatchType>();
  const { courseId, lessonId } = useParams();
  const [course, setCourse] = useState<any | null>(null);
  const [isPartial, setIsPartial] = useState<boolean>(false);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    if (courseId) {
      fetchCourseData();
    }
  }, [courseId]);

  useEffect(() => {
    if (course) {
      const paymentData = {
        landingIds: [course?.landing?.id],
        courseIds: [course?.id],
        priceCents: Math.ceil(course?.landing?.new_price * 100),
        newPrice: course?.landing?.new_price,
        oldPrice: course?.landing?.old_price,
        region: course?.landing?.region,
        fromAd: false,
        source:
          course?.access_level === "special_offer"
            ? PAGE_SOURCES.specialOffer
            : PAGE_SOURCES.cabinetFree,
        courses: [
          {
            name: course?.landing?.landing_name,
            newPrice: course?.landing?.new_price,
            oldPrice: course?.landing?.old_price,
            lessonsCount: course?.landing?.lessons_count,
            img: course?.landing?.preview_photo,
          },
        ],
      };

      dispatch(setPaymentData(paymentData));
    }
  }, [course]);

  const fetchCourseData = async () => {
    try {
      const res = await adminApi.getCourse(courseId);
      setCourse(normalizeCourse(res.data));
      setIsPartial(
        ["partial", "special_offer"].includes(res.data.access_level),
      );
      if (res.data.access_level === "none") navigate(Path.profile);
      setLoading(false);
    } catch (error) {
      console.error(error);
    }
  };

  if (lessonId) {
    return (
      <>
        <Outlet context={{ course, isPartial }} />
      </>
    );
  }

  return (
    <>
      <div className={s.course_page}>
        {loading ? (
          <Loader />
        ) : (
          <>
            <DetailHeader
              link={`${Path.profile}?content=your_courses`}
              title={course?.name}
            />
            <Outlet />
            <ul className={s.modules_list}>
              {course.sections.map((section: any) => (
                <li key={section.id}>
                  {course.sections.length > 1 && (
                    <SectionHeader name={section.section_name} />
                  )}
                  <ul>
                    {section.lessons.map((lesson: any, index: number) => (
                      <LessonCard
                        type="lesson"
                        price={course?.landing?.new_price}
                        isPartial={isPartial && !lesson.video_link}
                        index={index}
                        key={lesson.id}
                        handleClick={() => openPaymentModal()}
                        name={lesson.lesson_name}
                        previewPhoto={lesson.preview}
                        link={`${Path.lesson}/${section.id}/${lesson.id}`}
                        viewText={"watchLesson"}
                      />
                    ))}
                  </ul>
                </li>
              ))}
            </ul>
          </>
        )}
      </div>
    </>
  );
};

export default CoursePage;
