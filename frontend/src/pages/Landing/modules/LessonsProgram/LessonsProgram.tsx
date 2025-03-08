import s from "./LessonsProgram.module.scss";
import SectionHeader from "../../../../components/ui/SectionHeader/SectionHeader.tsx";
import Lesson from "./modules/Lesson/Lesson.tsx";

const LessonsProgram = ({ data }: { data: any }) => {
  return (
    <div className={s.lessons_container}>
      <SectionHeader name={"landing.fullCourseProgram"} />
      <ul className={s.lessons}>
        {data.lessons.map((lesson: any, index: number) => (
          <Lesson
            key={index}
            old_price={data.old_price}
            new_price={data.new_price}
            lesson={lesson}
          />
        ))}
      </ul>
    </div>
  );
};

export default LessonsProgram;
