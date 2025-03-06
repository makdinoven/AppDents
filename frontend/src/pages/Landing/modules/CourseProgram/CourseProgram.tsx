import s from "./CourseProgram.module.scss";
import SectionHeader from "../../../../components/ui/SectionHeader/SectionHeader.tsx";

const CourseProgram = ({ data }: { data: any }) => {
  console.log(data);

  return (
    <div className={s.course_program}>
      <SectionHeader name={"landing.courseProgram"} />
    </div>
  );
};

export default CourseProgram;
