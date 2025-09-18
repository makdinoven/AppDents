import s from "./MyCourses.module.scss";
import { Trans } from "react-i18next";
import SectionHeader from "../../../../components/ui/SectionHeader/SectionHeader.tsx";
import ProfileCourseCard from "../ProfileCourseCard/ProfileCourseCard.tsx";
import { Path } from "../../../../routes/routes.ts";
import { useSelector } from "react-redux";
import { AppRootStateType } from "../../../../store/store.ts";
import CourseCardSkeletons from "../../../../components/ui/Skeletons/CourseCardSkeletons/CourseCardSkeletons.tsx";

const MyCourses = ({ courses }: { courses: any }) => {
  const loading = useSelector(
    (state: AppRootStateType) => state.user.loadingCourses,
  );
  return (
    <section className={s.courses}>
      <SectionHeader name={"profile.yourCourses"} />
      {loading ? (
        <CourseCardSkeletons amount={6} columns={3} />
      ) : (
        <ul className={s.courses_list}>
          {courses.length > 0 ? (
            courses.map((course: any, index: number) => (
              <ProfileCourseCard
                index={index}
                isPartial={course.access_level === "partial"}
                isOffer={course.access_level === "special_offer"}
                viewText={"viewCourse"}
                key={course.id}
                name={course.name}
                previewPhoto={course.preview}
                link={`${Path.myCourse}/${course.id}`}
                expires_at={course.expires_at && course.expires_at}
              />
            ))
          ) : (
            <p className={s.no_courses}>
              <Trans i18nKey="profile.noCourses" />
            </p>
          )}
        </ul>
      )}
    </section>
  );
};

export default MyCourses;
