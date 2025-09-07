import s from "./DetailPage.module.scss";
import EditLanding from "../modules/EditLanding/EditLanding.tsx";
import DetailHeader from "../modules/common/DetailHeader/DetailHeader.tsx";
import DetailBottom from "../modules/common/DetailBottom/DetailBottom.tsx";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Trans } from "react-i18next";
import PrettyButton from "../../../components/ui/PrettyButton/PrettyButton.tsx";
import { t } from "i18next";
import EditLesson from "../modules/EditLesson/EditLesson.tsx";
import Loader from "../../../components/ui/Loader/Loader.tsx";
import { adminApi } from "../../../api/adminApi/adminApi.ts";
import { mainApi } from "../../../api/mainApi/mainApi.ts";
import {
  denormalizeLessons,
  normalizeLessons,
} from "../../../common/helpers/helpers.ts";
import { ErrorIcon } from "../../../assets/icons/index.ts";
import { Alert } from "../../../components/ui/Alert/Alert.tsx";

const LandingDetail = () => {
  const { landingId } = useParams();
  const [loading, setLoading] = useState(true);
  const [landing, setLanding] = useState<any | null>(null);
  const [authors, setAuthors] = useState<any | null>(null);
  const [tags, setTags] = useState<any | null>(null);
  const [courses, setCourses] = useState<any | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (landingId) {
      fetchAllData();
    }
  }, [landingId]);

  const fetchAllData = async () => {
    setLoading(true);
    try {
      const [landingRes, tagsRes, coursesRes, authorsRes] = await Promise.all([
        adminApi.getLanding(landingId),
        mainApi.getTags(),
        adminApi.getCoursesList({ size: 100000 }),
        adminApi.getAuthorsList({ size: 100000 }),
      ]);

      setLanding({
        ...landingRes.data,
        lessons_info: normalizeLessons(landingRes.data.lessons_info),
      });
      setTags(tagsRes.data);
      setCourses(coursesRes.data.items);
      setAuthors(authorsRes.data.items);
    } catch (error: any) {
      Alert(
        `Error fetching landing data, error message: ${error.message}`,
        <ErrorIcon />
      );
    } finally {
      setLoading(false);
    }
  };

  const handleAddLesson = () => {
    setLanding((prev: any) => {
      if (!prev) return prev;

      return {
        ...prev,
        lessons_info: [
          ...prev.lessons_info,
          {
            id: prev.lessons_info.length + 1,
            name: "New Lesson",
          },
        ],
      };
    });
  };

  const handleDeleteLanding = async () => {
    try {
      await adminApi.deleteLanding(landingId);
      navigate(-1);
    } catch (error) {
      console.error("Error deleting course:", error);
    }
  };

  const handleDeleteItem = (
    itemType: "landing" | "lesson",
    lessonId?: number
  ) => {
    if (!confirm(`Are you sure you want to delete this ${itemType}?`)) return;

    if (itemType === "landing") return handleDeleteLanding();
    else {
      setLanding((prev: any) => {
        if (!prev) return prev;

        return {
          ...prev,
          lessons_info: prev.lessons_info.filter((l: any) => l.id !== lessonId),
        };
      });
    }
  };

  const handleSave = async () => {
    const denormalizedLanding = {
      ...landing,
      lessons_info: denormalizeLessons(landing?.lessons_info),
    };
    try {
      await adminApi.updateLanding(landingId, denormalizedLanding);
      navigate(-1);
    } catch (error) {
      console.error("Error updating course:", error);
    }
  };

  const moveLessonUp = (lessonId: number) => {
    setLanding((prev: any) => {
      if (!prev) return prev;

      const idx = prev.lessons_info.findIndex((l: any) => l.id === lessonId);
      if (idx <= 0) return prev;

      const lessons_info = [...prev.lessons_info];
      [lessons_info[idx - 1], lessons_info[idx]] = [
        lessons_info[idx],
        lessons_info[idx - 1],
      ];

      return { ...prev, lessons_info };
    });
  };

  const moveLessonDown = (lessonId: number) => {
    setLanding((prev: any) => {
      if (!prev) return prev;

      const idx = prev.lessons_info.findIndex((l: any) => l.id === lessonId);
      if (idx === -1 || idx === prev.lessons_info.length - 1) return prev; // если последний — не двигаем

      const lessons_info = [...prev.lessons_info];
      [lessons_info[idx], lessons_info[idx + 1]] = [
        lessons_info[idx + 1],
        lessons_info[idx],
      ];

      return { ...prev, lessons_info };
    });
  };

  return (
    <div className={s.detail_container}>
      <DetailHeader title={"admin.landings.edit"} />
      {loading ? (
        <Loader />
      ) : (
        <>
          <EditLanding
            tags={tags}
            authors={authors}
            courses={courses}
            landing={landing}
            setLanding={setLanding}
          />
          <div className={s.list}>
            <div className={s.list_header}>
              <h2>
                <Trans i18nKey={"admin.lessons.lessons"} />
              </h2>
              <PrettyButton
                variant={"primary"}
                text={t("admin.lessons.add")}
                onClick={handleAddLesson}
              />
            </div>
            {landing?.lessons_info.length > 0 ? (
              landing.lessons_info.map((lesson: any, index: number) => (
                <EditLesson
                  moveLessonUp={() => moveLessonUp(lesson.id)}
                  moveLessonDown={() => moveLessonDown(lesson.id)}
                  type={"landing"}
                  key={index}
                  lesson={lesson}
                  setCourse={setLanding}
                  handleDelete={() => handleDeleteItem("lesson", lesson.id)}
                />
              ))
            ) : (
              <div>
                <Trans i18nKey={"admin.sections.noLessons"} />
              </div>
            )}
          </div>

          <DetailBottom
            deleteLabel={"admin.landings.delete"}
            handleSave={handleSave}
            handleDelete={() => handleDeleteItem("landing")}
          />
        </>
      )}
    </div>
  );
};
export default LandingDetail;
