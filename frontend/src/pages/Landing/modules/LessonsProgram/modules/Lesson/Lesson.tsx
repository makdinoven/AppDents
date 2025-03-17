import s from "./Lesson.module.scss";
import { Trans } from "react-i18next";
import ArrowButton from "../../../../../../components/ui/ArrowButton/ArrowButton.tsx";
import ProgramContent from "../ProgramContent/ProgramContent.tsx";
import { isValidUrl } from "../../../../../../common/helpers/helpers.ts";

const Lesson = ({ lesson, old_price, new_price, scrollFunc }: any) => {
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
              {isValidUrl(lesson.link) && lesson.link.length > 0 ? (
                // <iframe src={lesson.link} frameBorder="0" />
                <video controls>
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
          <ArrowButton onClick={scrollFunc}>
            <Trans
              i18nKey="landing.buyFor"
              values={{
                new_price: new_price,
                old_price: old_price,
              }}
              components={{
                1: <span className="crossed" />,
                2: <span className="highlight" />,
              }}
            />
          </ArrowButton>
        </div>
      </div>
    </li>
  );
};

export default Lesson;
