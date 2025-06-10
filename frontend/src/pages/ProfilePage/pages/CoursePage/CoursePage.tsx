import s from "./CoursePage.module.scss";
import { Outlet, useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import { adminApi } from "../../../../api/adminApi/adminApi.ts";
import { normalizeCourse } from "../../../../common/helpers/helpers.ts";
import Loader from "../../../../components/ui/Loader/Loader.tsx";
import DetailHeader from "../../../Admin/modules/common/DetailHeader/DetailHeader.tsx";
import SectionHeader from "../../../../components/ui/SectionHeader/SectionHeader.tsx";
import ProfileCourseCard from "../../modules/ProfileCourseCard/ProfileCourseCard.tsx";
import { Path } from "../../../../routes/routes.ts";
import ModalWrapper from "../../../../components/Modals/ModalWrapper/ModalWrapper.tsx";
import PaymentModal from "../../../../components/Modals/PaymentModal/PaymentModal.tsx";
import { BASE_URL } from "../../../../common/helpers/commonConstants.ts";

const CoursePage = () => {
  const { courseId, lessonId } = useParams();
  const [course, setCourse] = useState<any | null>(null);
  const [isPartial, setIsPartial] = useState<boolean>(false);
  const [landing, setLanding] = useState<any>(undefined);
  const [isModalOpen, setModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const currentUrl = window.location.origin + location.pathname;

  useEffect(() => {
    if (courseId) {
      fetchCourseData();
    }
  }, [courseId]);

  useEffect(() => {
    if (isPartial) {
      fetchLandingData();
    }
  }, [isPartial]);

  const fetchCourseData = async () => {
    try {
      const res = await adminApi.getCourse(courseId);
      setCourse(normalizeCourse(res.data));
      setIsPartial(res.data.access_level === "partial");
      setLoading(false);
    } catch (error) {
      console.error(error);
    }
  };

  const fetchLandingData = async () => {
    try {
      const res = await adminApi.getLanding(course.cheapest_landing.id);
      setLanding(res.data);
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
    landing_ids: [landing?.id],
    course_ids: landing?.course_ids,
    price_cents: landing?.new_price * 100,
    total_new_price: landing?.new_price,
    total_old_price: landing?.old_price,
    region: landing?.language,
    success_url: `${BASE_URL}${Path.successPayment}`,
    cancel_url: currentUrl,
    courses: [
      {
        name: landing?.landing_name,
        new_price: landing?.new_price,
        old_price: landing?.old_price,
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
          <Loader />
        ) : (
          <>
            <DetailHeader link={Path.profile} title={course?.name} />
            <Outlet />
            <ul className={s.modules_list}>
              {course.sections.map((section: any) => (
                <li key={section.id}>
                  {course.sections.length > 1 && (
                    <SectionHeader name={section.section_name} />
                  )}
                  <ul>
                    {section.lessons.map((lesson: any, index: number) => (
                      <ProfileCourseCard
                        price={landing?.new_price}
                        isPartial={isPartial && !lesson.video_link}
                        isEven={index % 2 === 0}
                        key={lesson.id}
                        handleClick={handleOpenModal}
                        name={lesson.lesson_name}
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
      {renderModal()}
    </>
  );
};

export default CoursePage;
