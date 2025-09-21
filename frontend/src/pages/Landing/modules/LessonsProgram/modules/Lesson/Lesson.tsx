import s from "./Lesson.module.scss";
import { Trans } from "react-i18next";
import ProgramContent from "../ProgramContent/ProgramContent.tsx";

const Lesson = ({ lesson, renderBuyButton }: any) => {
  return (
    <li className={s.lesson}>
      <h5>{lesson.name}</h5>
      <span className={s.line}></span>
      <div className={s.lesson_body}>
        <ProgramContent
          programData={lesson.program}
          textClassName={s.text}
          listClassName={s.lessons_list}
        />
        <div className={s.lesson_content}>
          <div className={s.video_container}>
            <div className={s.video_wrapper}>
              {lesson.link?.length > 0 ? (
                // <iframe src={lesson.link} frameBorder="0" />
                <video poster={lesson.preview} controls>
                  <source src={lesson.link} type="video/mp4" />
                  <source
                    src={lesson.link.replace(".mp4", ".webm")}
                    type="video/webm"
                  />
                  <source
                    src={lesson.link.replace(".mp4", ".ogg")}
                    type="video/ogg"
                  />
                  <Trans i18nKey="landing.videoIsNotSupported" />
                </video>
              ) : (
                <p>
                  <Trans i18nKey={"landing.noVideoLink"} />
                </p>
              )}
            </div>
            <p>
              <Trans
                i18nKey={"landing.fiveMinuteFragment"}
                components={{
                  1: <span className="highlight" />,
                }}
              />
            </p>
            <span className={s.line}></span>
            {lesson.duration && (
              <p>
                <Trans i18nKey={"landing.durationOfLesson"} /> {lesson.duration}
              </p>
            )}
            {lesson.lecturer && <p className={s.lecturer}>{lesson.lecturer}</p>}
          </div>
          {renderBuyButton}
        </div>
      </div>
    </li>
  );
};

export default Lesson;
