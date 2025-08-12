import UniversalSlider from "../../../../../../components/ui/UniversalSlider/UniversalSlider.tsx";
import SuggestionLesson from "../SuggestionLesson/SuggestionLesson.tsx";

const SuggestionLessonsSlider = ({
  lessons,
  currentLesson,
  setCurrentLesson,
}: {
  lessons: any[];
  currentLesson: any;
  setCurrentLesson: (lesson: any) => void;
}) => {
  const slides = lessons.map((lesson: any, index: number) => (
    <SuggestionLesson
      key={index}
      onClick={() => handleLessonClick(lesson)}
      lesson={lesson}
      isActive={lesson.id === currentLesson.id}
    />
  ));

  const handleLessonClick = (lesson: any) => {
    setCurrentLesson(lesson);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <UniversalSlider
      slidesPerView={1.3}
      pagination
      navigation
      paginationType={"dots"}
      navigationPosition={"bottom"}
      slides={slides}
      isFullWidth
    />
  );
};

export default SuggestionLessonsSlider;
