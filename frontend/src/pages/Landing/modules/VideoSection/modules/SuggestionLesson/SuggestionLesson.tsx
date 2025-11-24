import s from "./SuggestionLesson.module.scss";
import { PlayIcon } from "../../../../../../shared/assets/icons";

const SuggestionLesson = ({
  onClick,
  isActive,
  lesson,
}: {
  onClick: () => void;
  isActive: boolean;
  lesson: any;
}) => {
  return (
    <div
      onClick={onClick}
      className={`${s.lesson_suggestion} ${isActive ? s.active : ""}`}
    >
      <div className={s.lesson_image_wrapper}>
        <img src={lesson.preview} alt="" />
        <button className={s.play_button}>
          <PlayIcon />
        </button>
        <div className={s.lesson_duration}>{lesson.duration}</div>
      </div>
      <p>{lesson.name}</p>
    </div>
  );
};

export default SuggestionLesson;
