import s from "./Courses.module.scss";
import { Trans } from "react-i18next";
import CourseCard from "../CourseCard/CourseCard.tsx";
import { useEffect, useState } from "react";
import FilterButton from "../../../../components/ui/FilterButton/FilterButton.tsx";
import SectionHeader from "../../../../components/ui/SectionHeader/SectionHeader.tsx";

const initialCourses = [
  {
    id: "1",
    name: "Damon 2.0 How to treat all common malocclusions",
    description: "By Bill Dischinger, Alfredo Rizzo, Trevor Nichols et. al.",
    tag: "Surgery",
    link: "string",
    photo:
      "https://dent-s.com/assets/img/preview_img/e9f108ecfe3343ed9cfac82f87f2da38.png",
  },
  {
    id: "2",
    name: "Damon 2.0 How to treat all common malocclusions",
    description: "By Bill Dischinger, Alfredo Rizzo, Trevor Nichols et. al.",
    tag: "Orthodontics",
    link: "string",
    photo:
      "https://dent-s.com/assets/img/preview_img/e9f108ecfe3343ed9cfac82f87f2da38.png",
  },
  {
    id: "3",
    name: "Damon 2.0 How to treat all common malocclusions",
    description: "By Bill Dischinger, Alfredo Rizzo, Trevor Nichols et. al.",
    tag: "Orthodontics",
    link: "string",
    photo:
      "https://dent-s.com/assets/img/preview_img/e9f108ecfe3343ed9cfac82f87f2da38.png",
  },
  {
    id: "4",
    name: "Damon 2.0 How to treat all common malocclusions",
    description: "By Bill Dischinger, Alfredo Rizzo, Trevor Nichols et. al.",
    tag: "Surgery",
    link: "string",
    photo:
      "https://dent-s.com/assets/img/preview_img/e9f108ecfe3343ed9cfac82f87f2da38.png",
  },
];

const initialFilters = {
  tags: [
    { name: "tag.allCourses", value: "all" },
    { name: "tag.surgery", value: "surgery" },
    { name: "tag.orthodontics", value: "orthodontics" },
  ],
  common: [
    { name: "tag.common.popular", value: "popular" },
    { name: "tag.common.bestPrices", value: "best_prices" },
    { name: "tag.common.new", value: "new" },
  ],
};
const Courses = () => {
  const [courses, setCourses] = useState<any>(initialCourses);
  const [activeFilter, setActiveFilter] = useState<any>("all");

  useEffect(() => {
    setCourses(initialCourses);
  }, []);

  const handleSetActiveFilter = (filter: string) => {
    setActiveFilter(filter);
  };

  useEffect(() => {
    console.log(activeFilter);
  }, [activeFilter]);

  return (
    <section className={s.courses}>
      <div className={s.courses_header}>
        <SectionHeader name={"main.ourCurses"} />
        <div className={s.filters}>
          {initialFilters.tags.map((filter) => (
            <FilterButton
              isActive={activeFilter === filter.value}
              onClick={() => handleSetActiveFilter(filter.value)}
              key={filter.value}
              text={filter.name}
            />
          ))}
        </div>
        <span className={s.line}></span>
        <div className={s.filters}>
          {initialFilters.common.map((filter) => (
            <FilterButton
              isActive={activeFilter === filter.value}
              onClick={() => handleSetActiveFilter(filter.value)}
              key={filter.value}
              text={filter.name}
            />
          ))}
        </div>
      </div>
      {courses.length > 0 ? (
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
      ) : (
        <div className={s.no_courses}>
          <Trans i18nKey={"main.noCourses"} />
        </div>
      )}
    </section>
  );
};
export default Courses;
