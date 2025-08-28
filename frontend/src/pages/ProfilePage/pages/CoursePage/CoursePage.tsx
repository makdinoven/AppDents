import s from "./CoursePage.module.scss";
import { Outlet, useNavigate, useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import { adminApi } from "../../../../api/adminApi/adminApi.ts";
import { normalizeCourse } from "../../../../common/helpers/helpers.ts";
import DetailHeader from "../../../Admin/modules/common/DetailHeader/DetailHeader.tsx";
import SectionHeader from "../../../../components/ui/SectionHeader/SectionHeader.tsx";
import { Path } from "../../../../routes/routes.ts";
import ModalWrapper from "../../../../components/Modals/ModalWrapper/ModalWrapper.tsx";
import PaymentModal from "../../../../components/Modals/PaymentModal/PaymentModal.tsx";
import { BASE_URL } from "../../../../common/helpers/commonConstants.ts";
import LessonCard from "./LessonCard/LessonCard.tsx";
import LessonSkeletons from "../../../../components/ui/Skeletons/LessonSkeletons/LessonSkeletons.tsx";

const CoursePage = () => {
  const { courseId, lessonId } = useParams();
  const [course, setCourse] = useState<any | null>(null);
  const [isPartial, setIsPartial] = useState<boolean>(false);
  const [isModalOpen, setModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const currentUrl = window.location.origin + location.pathname;
  const navigate = useNavigate();

  useEffect(() => {
    if (courseId) {
      fetchCourseData();
    }
  }, [courseId]);

  const fetchCourseData = async () => {
    try {
      const res = await adminApi.getCourse(courseId);
      setCourse(normalizeCourse(res.data));
      setIsPartial(
        ["partial", "special_offer"].includes(res.data.access_level)
      );
      if (res.data.access_level === "none") navigate(Path.profile);
      setLoading(false);
    } catch (error) {
      console.error(error);
    }
  };

  const handleOpenModal = () => {
    setModalOpen(true);
  };

  const handleCloseModal = () => {
    setModalOpen(false);
  };

  const paymentData = {
    landing_ids: [course?.landing?.id],
    course_ids: [course?.id],
    price_cents: Math.ceil(course?.landing?.new_price * 100),
    total_new_price: course?.landing?.new_price,
    total_old_price: course?.landing?.old_price,
    region: course?.landing?.region,
    success_url: `${BASE_URL}${Path.successPayment}`,
    cancel_url: currentUrl,
    source:
      course?.access_level === "special_offer"
        ? "SPECIAL_OFFER"
        : "CABINET_FREE",
    courses: [
      {
        name: course?.landing?.landing_name,
        new_price: course?.landing?.new_price,
        old_price: course?.landing?.old_price,
        lessons_count: course?.landing?.lessons_count,
      },
    ],
  };

  const renderModal = () => {
    if (isModalOpen) {
      return (
        <ModalWrapper
          variant="dark"
          title={"freeCourse.fullAccess"}
          cutoutPosition="none"
          isOpen={isModalOpen}
          onClose={handleCloseModal}
        >
          <PaymentModal
            paymentData={paymentData}
            handleCloseModal={handleCloseModal}
          />
        </ModalWrapper>
      );
    }
  };

  if (lessonId) {
    return (
      <>
        <Outlet context={{ course, handleOpenModal, isPartial }} />
        {renderModal()}
      </>
    );
  }

  return (
    <>
      <div className={s.course_page}>
        {loading ? (
          <>
            <div className={s.header}></div>
            <LessonSkeletons />
          </>
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
                        handleClick={handleOpenModal}
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
      {isPartial && renderModal()}
    </>
  );
};

export default CoursePage;
