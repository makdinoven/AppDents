import s from "./LessonPage.module.scss";
import { useEffect, useState } from "react";
import { adminApi } from "../../api/adminApi/adminApi.ts";
import { isValidUrl, normalizeCourse } from "../../common/helpers/helpers.ts";
import { useParams } from "react-router-dom";
import Loader from "../../components/ui/Loader/Loader.tsx";
import DetailHeader from "../Admin/modules/common/DetailHeader/DetailHeader.tsx";
import { Trans } from "react-i18next";
import { t } from "i18next";

const LessonPage = () => {
  const { courseId, sectionId, lessonId } = useParams();
  const [lesson, setLesson] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (courseId && lessonId) {
      fetchCourseData();
    }
  }, [courseId, lessonId]);

  const fetchCourseData = async () => {
    try {
      const res = await adminApi.getCourse(courseId);
      const courseData = normalizeCourse(res.data);
      const section = courseData.sections.find(
        (section: any) => section.id === Number(sectionId),
      );
      const lesson = section?.lessons.find(
        (lesson: any) => lesson.id === Number(lessonId),
      );

      // console.log(lesson);

      setLesson(lesson);
      setLoading(false);
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <div className={s.lesson_container}>
      <DetailHeader title={lesson?.lesson_name} />
      {loading ? (
        <Loader />
      ) : (
        <div className={s.lesson_page}>
          <div className={s.video_container}>
            {isValidUrl(lesson.video_link) && lesson.video_link.length > 0 ? (
              <video controls width={"100%"}>
                <source src={lesson.video_link} type="video/mp4" />
                <source
                  src={lesson.video_link.replace(".mp4", ".webm")}
                  type="video/webm"
                />
                <source
                  src={lesson.video_link.replace(".mp4", ".ogg")}
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
      )}
    </div>
  );
};
export default LessonPage;
