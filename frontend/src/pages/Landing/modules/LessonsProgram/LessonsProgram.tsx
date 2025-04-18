import s from "./LessonsProgram.module.scss";
import SectionHeader from "../../../../components/ui/SectionHeader/SectionHeader.tsx";
import Lesson from "./modules/Lesson/Lesson.tsx";

const LessonsProgram = ({
  data: { lessons, old_price, new_price, renderBuyButton },
}: {
  data: any;
}) => {
  return (
    <div className={s.lessons_container}>
      <SectionHeader name={"landing.fullCourseProgram"} />
      <ul className={s.lessons}>
        {lessons.map((lesson: any, index: number) => (
          <Lesson
            key={index}
            old_price={old_price}
            new_price={new_price}
            renderBuyButton={renderBuyButton}
            lesson={lesson}
          />
        ))}
      </ul>
    </div>
  );
};

export default LessonsProgram;
