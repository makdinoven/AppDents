import s from "./CoursesList.module.scss";
import { Trans } from "react-i18next";
import CourseCard from "../CourseCard/CourseCard.tsx";
import { useEffect, useState } from "react";

const initialCourses = [
  {
    id: "1",
    name: "Damon 2.0 How to treat all common malocclusions",
    description: "By Bill Dischinger, Alfredo Rizzo, Trevor Nichols et. al.",
    tag: "Surgery",
    link: "string",
    photo: "/src/assets/course-card.png",
  },
  {
    id: "2",
    name: "Damon 2.0 How to treat all common malocclusions",
    description: "By Bill Dischinger, Alfredo Rizzo, Trevor Nichols et. al.",
    tag: "Orthodontics",
    link: "string",
    photo: "/src/assets/course-card.png",
  },
  {
    id: "3",
    name: "Damon 2.0 How to treat all common malocclusions",
    description: "By Bill Dischinger, Alfredo Rizzo, Trevor Nichols et. al.",
    tag: "Orthodontics",
    link: "string",
    photo: "/src/assets/course-card.png",
  },
  {
    id: "4",
    name: "Damon 2.0 How to treat all common malocclusions",
    description: "By Bill Dischinger, Alfredo Rizzo, Trevor Nichols et. al.",
    tag: "Surgery",
    link: "string",
    photo: "/src/assets/course-card.png",
  },
];

const CoursesList = () => {
  const [courses, setCourses] = useState<any>(initialCourses);

  useEffect(() => {
    setCourses(initialCourses);
  }, []);

  return (
    <section className={s.courses}>
      <div className={s.courses_header}>
        <h3>
          <Trans i18nKey={"main.ourCurses"} />
        </h3>
      </div>
      <ul className={s.list}>
        {courses.map((course: any, index: number) => (
          <CourseCard
            key={index}
            index={index}
            name={course.name}
            description={course.description}
            tag={course.tag}
            link={course.link}
            photo={course.photo}
          />
        ))}
      </ul>
    </section>
  );
};
export default CoursesList;
