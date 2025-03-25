import s from "./MyCourses.module.scss";
import { Trans } from "react-i18next";
import SectionHeader from "../../../../components/ui/SectionHeader/SectionHeader.tsx";
import CourseCard from "../CourseCard/CourseCard.tsx";
import { Path } from "../../../../routes/routes.ts";

const MyCourses = ({ courses }: { courses: any }) => {
  return (
    <section className={s.courses}>
      <SectionHeader name={"profile.yourCourses"} />
      <ul className={s.courses_list}>
        {courses.length > 0 ? (
          courses.map((course: any, index: number) => (
            <CourseCard
              viewText={"viewCourse"}
              key={course.id}
              isEven={index % 2 === 0}
              name={course.name}
              link={`${Path.myCourse}/${course.id}`}
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
