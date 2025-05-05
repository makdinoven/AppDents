import s from "./LessonPage.module.scss";
import { useEffect, useState } from "react";
import { Link, useOutletContext, useParams } from "react-router-dom";
import { Trans } from "react-i18next";
import { t } from "i18next";
import { Path } from "../../../../routes/routes.ts";
import BackButton from "../../../../components/ui/BackButton/BackButton.tsx";
import Arrow from "../../../../assets/Icons/Arrow.tsx";

type OutletContextType = {
  course: any;
};

const LessonPage = () => {
  const { course } = useOutletContext<OutletContextType>();
  const { sectionId, lessonId } = useParams();
  const [lesson, setLesson] = useState<any | null>(null);
  const [prevLesson, setPrevLesson] = useState<any | null>(null);
  const [nextLesson, setNextLesson] = useState<any | null>(null);

  useEffect(() => {
    if (course && sectionId && lessonId) {
      prepareLesson();
    }
  }, [course, sectionId, lessonId]);

  const prepareLesson = () => {
    const sectionIndex = course.sections.findIndex(
      (section: any) => section.id === Number(sectionId),
    );

    if (sectionIndex === -1) return;

    const section = course.sections[sectionIndex];
    const lessons = section.lessons;
    const lessonIndex = lessons.findIndex(
      (lesson: any) => lesson.id === Number(lessonId),
    );

    if (lessonIndex === -1) return;

    const currentLesson = lessons[lessonIndex];
    const prev =
      lessonIndex > 0
        ? { lesson: lessons[lessonIndex - 1], sectionId: section.id }
        : sectionIndex > 0
          ? {
              lesson: course.sections[sectionIndex - 1].lessons.slice(-1)[0],
              sectionId: course.sections[sectionIndex - 1].id,
            }
          : null;
    const next =
      lessonIndex < lessons.length - 1
        ? { lesson: lessons[lessonIndex + 1], sectionId: section.id }
        : sectionIndex < course.sections.length - 1
          ? {
              lesson: course.sections[sectionIndex + 1].lessons[0],
              sectionId: course.sections[sectionIndex + 1].id,
            }
          : null;

    setLesson(currentLesson);
    setPrevLesson(prev);
    setNextLesson(next);
  };
  if (lesson)
    return (
      <>
        <BackButton link={`${Path.profile}/${Path.myCourse}/${course.id}`} />
        <div className={s.lesson_page}>
          <h3>{lesson.lesson_name}</h3>
          <div className={s.video_container}>
            {lesson.video_link?.length > 0 ? (
              <iframe
                src={lesson.video_link}
                width="100%"
                height="100%"
                frameBorder="0"
                allow="autoplay; fullscreen"
                allowFullScreen
              />
            ) : (
              <p>
                <Trans i18nKey={"landing.noVideoLink"} />
              </p>
            )}
          </div>
          <div className={s.navigation_links}>
            {prevLesson && (
              <Link
                to={`${Path.profile}/${Path.myCourse}/${course.id}/${Path.lesson}/${prevLesson.sectionId}/${prevLesson.lesson.id}`}
                className={s.prev_link}
              >
                <Arrow />
                <Trans i18nKey={"profile.prevLesson"} />
              </Link>
            )}
            {nextLesson && (
              <Link
                to={`${Path.profile}/${Path.myCourse}/${course.id}/${Path.lesson}/${nextLesson.sectionId}/${nextLesson.lesson.id}`}
                className={s.next_link}
              >
                <Trans i18nKey={"profile.nextLesson"} />
                <Arrow />
              </Link>
            )}
          </div>

          <p className={s.failed_to_load}>
            {t("videoFailedToLoad")}{" "}
            <a
              href={lesson.video_link}
              target="_blank"
              className="highlight"
              rel="noopener noreferrer"
            >
              {t("watchHere")}
            </a>
          </p>
        </div>
      </>
    );
};
export default LessonPage;
