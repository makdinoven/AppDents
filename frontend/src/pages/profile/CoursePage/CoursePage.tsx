import s from "./CoursePage.module.scss";
import { Outlet, useNavigate, useParams } from "react-router-dom";
import { memo, useEffect, useState } from "react";
import { adminApi } from "../../../shared/api/adminApi/adminApi.ts";
import { normalizeCourse } from "../../../shared/common/helpers/helpers.ts";
import DetailHeader from "../../Admin/pages/modules/common/DetailHeader/DetailHeader.tsx";
import SectionHeader from "../../../shared/components/ui/SectionHeader/SectionHeader.tsx";
import LessonCard from "./LessonCard/LessonCard.tsx";
import LessonSkeletons from "../../../shared/components/ui/Skeletons/LessonSkeletons/LessonSkeletons.tsx";
import { useDispatch } from "react-redux";
import { AppDispatchType } from "../../../shared/store/store.ts";
import { setPaymentData } from "../../../shared/store/slices/paymentSlice.ts";
import { PAGE_SOURCES } from "../../../shared/common/helpers/commonConstants.ts";
import { usePaymentPageHandler } from "../../../shared/common/hooks/usePaymentPageHandler.ts";
import DetailHeaderSkeleton from "../../../shared/components/ui/Skeletons/DetailHeaderSkeleton/DetailHeaderSkeleton.tsx";
import { LanguagesType } from "../../../shared/components/ui/LangLogo/LangLogo.tsx";
import { CartItemKind } from "../../../shared/api/cartApi/types.ts";
import { PATHS } from "../../../app/routes/routes.ts";

const CoursePage = memo(() => {
  const { openPaymentModal } = usePaymentPageHandler();
  const dispatch = useDispatch<AppDispatchType>();
  const { id, lessonId } = useParams();
  const [course, setCourse] = useState<any | null>(null);
  const [isPartial, setIsPartial] = useState<boolean>(false);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    if (id) {
      fetchCourseData();
    }
  }, [id]);

  useEffect(() => {
    if (course && course.landing) {
      dispatch(
        setPaymentData({
          data: {
            course_ids: [course.id],
            landing_ids: [course.landing.id],
            book_ids: [],
            book_landing_ids: [],
            price_cents: Math.ceil(course.landing.new_price * 100),
            new_price: course.landing.new_price,
            old_price: course.landing.old_price,
            from_ad: false,
            region: course.landing.region as LanguagesType,
            source:
              course.access_level === "special_offer"
                ? PAGE_SOURCES.specialOffer
                : PAGE_SOURCES.cabinetFree,
          },
          render: {
            new_price: course.landing.new_price,
            old_price: course.landing.new_price,
            items: [
              {
                item_type: "LANDING" as CartItemKind,
                data: {
                  id: course.id,
                  authors: [],
                  landing_name: course.landing.landing_name,
                  page_name: "",
                  new_price: course.landing.new_price,
                  old_price: course.landing.old_price,
                  lessons_count: course.landing.lessons_count,
                  course_ids: [course.id],
                  preview_photo: course.landing.preview_photo,
                },
              },
            ],
          },
        }),
      );
    }
  }, [course]);

  const fetchCourseData = async () => {
    try {
      const res = await adminApi.getCourse(id);
      setCourse(normalizeCourse(res.data));
      setIsPartial(
        ["partial", "special_offer"].includes(res.data.access_level),
      );
      if (res.data.access_level === "none") navigate(PATHS.PROFILE);
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
          <>
            <DetailHeaderSkeleton />
            <LessonSkeletons />
          </>
        ) : (
          <>
            <DetailHeader link={PATHS.PROFILE} title={course?.name} />
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
                        link={PATHS.PROFILE_COURSE_LESSON.build(
                          section.id,
                          lesson.id,
                        )}
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
});

export default CoursePage;
