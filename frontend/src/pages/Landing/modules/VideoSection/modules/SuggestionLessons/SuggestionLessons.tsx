import s from "./SuggestionLessons.module.scss";
import SuggestionLesson from "../SuggestionLesson/SuggestionLesson.tsx";

const SuggestionLessons = ({
  maxHeight,
  lessons,
  currentLesson,
  setCurrentLesson,
}: {
  maxHeight: number | undefined;
  lessons: any[];
  currentLesson: any;
  setCurrentLesson: (lesson: any) => void;
}) => {
  return (
    <ul
      style={{
        maxHeight: `${maxHeight}px`,
      }}
      className={s.suggestion_container}
    >
      {lessons.map((lesson: any, index: number) => (
        <SuggestionLesson
          key={index}
          onClick={() => setCurrentLesson(lesson)}
          lesson={lesson}
          isActive={lesson.id === currentLesson.id}
        />
      ))}
    </ul>
  );
};

export default SuggestionLessons;
