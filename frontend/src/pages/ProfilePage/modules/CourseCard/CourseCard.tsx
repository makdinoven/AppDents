import s from "./CourseCard.module.scss";
import ViewLink from "../../../../components/ui/ViewLink/ViewLink.tsx";

const CourseCard = ({ course, isEven }: { course: any; isEven: boolean }) => {
  return (
    <li className={`${s.card} ${isEven ? "" : s.blue}`}>
      <h3>{course.name}</h3>
      <ViewLink link={`/courses/${course.id}`} text={"viewCourse"} />
    </li>
  );
};

export default CourseCard;
