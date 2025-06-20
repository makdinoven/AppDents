import s from "./MyCourses.module.scss";
import { Trans } from "react-i18next";
import SectionHeader from "../../../../components/ui/SectionHeader/SectionHeader.tsx";
import ProfileCourseCard from "../ProfileCourseCard/ProfileCourseCard.tsx";
import { Path } from "../../../../routes/routes.ts";

const MyCourses = ({ courses }: { courses: any }) => {
  return (
    <section className={s.courses}>
      <SectionHeader name={"profile.yourCourses"} />
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
    </section>
  );
};

export default MyCourses;
