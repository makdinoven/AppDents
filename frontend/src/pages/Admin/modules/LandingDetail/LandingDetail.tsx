import s from "../CourseDetail/CourseDetail.module.scss";
import EditLanding from "../EditLanding/EditLanding.tsx";
import DetailHeader from "../common/DetailHeader/DetailHeader.tsx";
import DetailBottom from "../common/DetailBottom/DetailBottom.tsx";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Trans } from "react-i18next";
import PrettyButton from "../../../../components/ui/PrettyButton/PrettyButton.tsx";
import { t } from "i18next";
import EditLesson from "../EditLesson/EditLesson.tsx";
import Loader from "../../../../components/ui/Loader/Loader.tsx";
import { adminApi } from "../../../../api/adminApi/adminApi.ts";
import { mainApi } from "../../../../api/mainApi/mainApi.ts";

const languages = [
  { label: "English", value: "EN" },
  { label: "Russian", value: "RU" },
  { label: "Spanish", value: "ES" },
];

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

  useEffect(() => {
    console.log(landing);
  }, [landing]);

  const fetchAllData = async () => {
    setLoading(true);
    try {
      const [landingRes, tagsRes, coursesRes, authorsRes] = await Promise.all([
        adminApi.getLanding(landingId),
        mainApi.getTags(),
        adminApi.getCoursesList(),
        adminApi.getAuthors(),
      ]);

      setLanding({
        ...landingRes.data,
        lessons_info: normalizeLessons(landingRes.data.lessons_info),
      });

      setTags(tagsRes.data);
      setCourses(coursesRes.data);
      setAuthors(authorsRes.data);
    } catch (error) {
      console.error("Error fetching data", error);
    } finally {
      setLoading(false);
    }
  };

  function normalizeLessons(lessons: any[]): any[] {
    return lessons.map((lessonObj, index) => {
      const key = Object.keys(lessonObj)[0];
      const lesson = lessonObj[key];

      return {
        id: index + 1,
        program: lesson.program || "",
        link: lesson.link || "",
        duration: lesson.duration || "",
        name: lesson.name || "",
        lecturer: lesson.lecturer || "",
      };
    });
  }

  function denormalizeLessons(lessons: any) {
    return lessons.map((lesson: any, index: number) => {
      return {
        [`lesson${index + 1}`]: {
          link: lesson.link || "",
          name: lesson.name || "",
          program: lesson.program || "",
          duration: lesson.duration || "",
          lecturer: lesson.lecturer || "",
        },
      };
    });
  }

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

  const handleSave = async () => {
    const denormalizedLanding = {
      ...landing,
      lessons_info: denormalizeLessons(landing?.lessons_info),
    };
    console.log(denormalizedLanding);
    try {
      await adminApi.updateLanding(landingId, denormalizedLanding);
      navigate(-1);
    } catch (error) {
      console.error("Error updating course:", error);
    }
  };

  const handleDeleteItem = (
    itemType: "landing" | "lesson",
    lessonId?: number,
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
            languages={languages}
            landing={landing}
            setLanding={setLanding}
          />
          <div className={s.list}>
            <div className={s.list_header}>
              <h2>
                <Trans i18nKey={"admin.lessons"} />
              </h2>
              <PrettyButton
                variant={"primary"}
                text={t("admin.lessons.add")}
                onClick={handleAddLesson}
              />
            </div>
            {landing.lessons_info.length > 0 ? (
              landing.lessons_info.map((lesson: any, index: number) => (
                <EditLesson
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
