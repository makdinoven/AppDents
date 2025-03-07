import s from "./LessonsProgram.module.scss";
import SectionHeader from "../../../../components/ui/SectionHeader/SectionHeader.tsx";

const LessonsProgram = ({ data }: { data: any }) => {
  console.log(data);

  return (
    <div className={s.lessons_container}>
      <SectionHeader name={"landing.fullCourseProgram"} />
      <ul className={s.lessons}></ul>
    </div>
  );
};

export default LessonsProgram;
