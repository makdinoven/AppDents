import s from "./DetailPage.module.scss";
import { useNavigate, useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import EditSection from "../modules/EditSection/EditSection.tsx";
import EditLesson from "../modules/EditLesson/EditLesson.tsx";
import PrettyButton from "../../../../shared/components/ui/PrettyButton/PrettyButton.tsx";
import Loader from "../../../../shared/components/ui/Loader/Loader.tsx";
import { Trans } from "react-i18next";
import { t } from "i18next";
import EditCourse from "../modules/EditCourse/EditCourse.tsx";
import { adminApi } from "../../../../shared/api/adminApi/adminApi.ts";
import DetailHeader from "../modules/common/DetailHeader/DetailHeader.tsx";
import DetailBottom from "../modules/common/DetailBottom/DetailBottom.tsx";
import {
  denormalizeCourse,
  normalizeCourse,
} from "../../../../shared/common/helpers/helpers.ts";
import { ErrorIcon } from "../../../../shared/assets/icons";
import { Alert } from "../../../../shared/components/ui/Alert/Alert.tsx";
import { CheckMark } from "../../../../shared/assets/icons";

const CourseDetail = () => {
  const { id } = useParams();
  const [course, setCourse] = useState<any | null>(null);
  const navigate = useNavigate();
  const [fixLoading, setFixLoading] = useState(false);
  const [fixTaskId, setFixTaskId] = useState<string | null>(null);
  const [fixTaskState, setFixTaskState] = useState<string | null>(null);
  const [fixResult, setFixResult] = useState<any | null>(null);
  const [fixMeta, setFixMeta] = useState<any | null>(null);

  useEffect(() => {
    if (id) {
      fetchCourseData();
    }
  }, [id]);

  const fetchCourseData = async () => {
    try {
      const res = await adminApi.getCourse(id);
      setCourse(normalizeCourse(res.data));
    } catch (error: any) {
      Alert(
        `Error fetching course data, error message: ${error.message}`,
        <ErrorIcon />,
      );
    }
  };

  const updateCourseState = (callback: (prev: any) => any) => {
    setCourse((prev: any) => (prev ? callback(prev) : prev));
  };

  const handleAddItem = (
    itemType: "section" | "lesson",
    sectionId?: number,
  ) => {
    updateCourseState((prev) => {
      if (itemType === "section") {
        return {
          ...prev,
          sections: [
            ...prev.sections,
            {
              id: prev.sections.length + 1,
              section_name: "New Section",
              lessons: [],
            },
          ],
        };
      } else if (itemType === "lesson" && sectionId) {
        return {
          ...prev,
          sections: prev.sections.map((section: any) =>
            section.id === sectionId
              ? {
                  ...section,
                  lessons: [
                    ...section.lessons,
                    {
                      id: section.lessons.length + 1,
                      lesson_name: "New Lesson",
                      video_link: "",
                    },
                  ],
                }
              : section,
          ),
        };
      }
      return prev;
    });
  };

  const handleDeleteItem = (
    itemType: "course" | "section" | "lesson",
    sectionId?: number,
    lessonId?: number,
  ) => {
    if (!confirm(`Are you sure you want to delete this ${itemType}?`)) return;

    if (itemType === "course") return handleDeleteCourse();

    updateCourseState((prev) => {
      if (itemType === "section") {
        return {
          ...prev,
          sections: prev.sections.filter((s: any) => s.id !== sectionId),
        };
      } else if (itemType === "lesson" && sectionId) {
        return {
          ...prev,
          sections: prev.sections.map((section: any) =>
            section.id === sectionId
              ? {
                  ...section,
                  lessons: section.lessons.filter(
                    (l: any) => l.id !== lessonId,
                  ),
                }
              : section,
          ),
        };
      }
      return prev;
    });
  };

  const handleDeleteCourse = async () => {
    try {
      await adminApi.deleteCourse(id);
      navigate(-1);
    } catch (error) {
      console.error("Error deleting course:", error);
    }
  };

  const handleSave = async () => {
    try {
      await adminApi.updateCourse(id, denormalizeCourse(course));
      navigate(-1);
    } catch (error) {
      Alert(`Error updating course data`, <ErrorIcon />);
    }
  };

  const fixAllVideos = async () => {
    if (!id) return;
    try {
      setFixLoading(true);
      setFixResult(null);
      setFixTaskState(null);
      const res = await adminApi.runVideoMaintenanceForCourse({
        course_id: Number(id),
        dry_run: false,
        delete_old_key: true,
      });
      Alert(`Video maintenance started. Task: ${res.data.task_id}`, <CheckMark />);
      setFixTaskId(res.data.task_id);
    } catch (e) {
      console.error(e);
      Alert("Failed to start FIX ALL VIDEOS", <ErrorIcon />);
      setFixLoading(false);
      setFixTaskId(null);
    }
  };

  useEffect(() => {
    if (!fixTaskId) return;
    const interval = setInterval(async () => {
      try {
        const res = await adminApi.getVideoMaintenanceStatus(fixTaskId);
        setFixTaskState(res.data.state);
        setFixMeta(res.data.meta ?? null);
        const st = String(res.data.state || "").toLowerCase();
        if (st === "success" || st === "failure") {
          setFixResult(res.data.result);
          setFixLoading(false);
          setFixTaskId(null);
          setFixTaskState(null);
          setFixMeta(null);
          clearInterval(interval);
        }
      } catch (e) {
        console.error(e);
        Alert("Error checking status", <ErrorIcon />);
        setFixLoading(false);
        setFixTaskId(null);
        setFixTaskState(null);
        setFixMeta(null);
        clearInterval(interval);
      }
    }, 5000);
    return () => clearInterval(interval);
  }, [fixTaskId]);

  const moveSectionUp = (sectionId: number) => {
    updateCourseState((prev) => {
      const idx = prev.sections.findIndex((s: any) => s.id === sectionId);
      if (idx <= 0) return prev;

      const sections = [...prev.sections];
      [sections[idx - 1], sections[idx]] = [sections[idx], sections[idx - 1]];

      return { ...prev, sections };
    });
  };

  const moveSectionDown = (sectionId: number) => {
    updateCourseState((prev) => {
      const idx = prev.sections.findIndex((s: any) => s.id === sectionId);
      if (idx === -1 || idx === prev.sections.length - 1) return prev;

      const sections = [...prev.sections];
      [sections[idx], sections[idx + 1]] = [sections[idx + 1], sections[idx]];

      return { ...prev, sections };
    });
  };

  const moveLessonUp = (sectionId: number, lessonId: number) => {
    updateCourseState((prev) => {
      const sections = prev.sections.map((section: any) => {
        if (section.id !== sectionId) return section;

        const idx = section.lessons.findIndex((l: any) => l.id === lessonId);
        if (idx <= 0) return section;

        const lessons = [...section.lessons];
        [lessons[idx - 1], lessons[idx]] = [lessons[idx], lessons[idx - 1]];

        return { ...section, lessons };
      });

      return { ...prev, sections };
    });
  };

  const moveLessonDown = (sectionId: number, lessonId: number) => {
    updateCourseState((prev) => {
      const sections = prev.sections.map((section: any) => {
        if (section.id !== sectionId) return section;

        const idx = section.lessons.findIndex((l: any) => l.id === lessonId);
        if (idx === -1 || idx === section.lessons.length - 1) return section;

        const lessons = [...section.lessons];
        [lessons[idx], lessons[idx + 1]] = [lessons[idx + 1], lessons[idx]];

        return { ...section, lessons };
      });

      return { ...prev, sections };
    });
  };

  return (
    <div className={s.detail_container}>
      <DetailHeader title={"admin.courses.update"} />
      {!course ? (
        <Loader />
      ) : (
        <>
          <EditCourse course={course} setCourse={setCourse} />
          <div style={{ marginTop: 12, marginBottom: 12 }}>
            <PrettyButton
              text={"FIX ALL VIDEOS"}
              variant={"default"}
              onClick={!fixLoading ? fixAllVideos : undefined}
              loading={fixLoading}
            />
            {fixTaskId && (
              <div style={{ marginTop: 8, fontSize: 14 }}>
                <div><strong>Task:</strong> {fixTaskId}</div>
                <div><strong>Status:</strong> {fixTaskState || "..."}</div>
                {fixMeta?.phase && (
                  <div><strong>Phase:</strong> {String(fixMeta.phase)}</div>
                )}
                {fixMeta && (
                  <>
                    <div>
                      <strong>Progress:</strong>{" "}
                      {typeof fixMeta.done === "number" && typeof fixMeta.total === "number"
                        ? `${fixMeta.done}/${fixMeta.total}`
                        : ""}
                    </div>
                    {fixMeta.current && (
                      <div style={{ wordBreak: "break-word" }}>
                        <strong>Current:</strong> {String(fixMeta.current)}
                      </div>
                    )}
                    {fixMeta.last_error && (
                      <div style={{ marginTop: 6, color: "#b91c1c", wordBreak: "break-word" }}>
                        <strong>Error:</strong> {String(fixMeta.last_error)}
                      </div>
                    )}
                    {fixMeta.last && (
                      <div style={{ marginTop: 6, wordBreak: "break-word" }}>
                        <strong>Last:</strong>{" "}
                        <pre style={{ marginTop: 4, whiteSpace: "pre-wrap" }}>
                          {JSON.stringify(fixMeta.last, null, 2)}
                        </pre>
                      </div>
                    )}
                    {typeof fixMeta.done === "number" &&
                      typeof fixMeta.total === "number" &&
                      fixMeta.total > 0 && (
                        <div style={{ marginTop: 6, height: 8, background: "#e5e7eb", borderRadius: 6 }}>
                          <div
                            style={{
                              height: 8,
                              width: `${Math.min(100, Math.max(0, Math.round((fixMeta.done / fixMeta.total) * 100)))}%`,
                              background: "#7FDFD5",
                              borderRadius: 6,
                            }}
                          />
                        </div>
                      )}
                  </>
                )}
              </div>
            )}
          </div>
          {fixResult && (
            <details style={{ marginBottom: 12 }}>
              <summary>FIX ALL VIDEOS: Full JSON</summary>
              <pre style={{ whiteSpace: "pre-wrap" }}>
                {JSON.stringify(fixResult, null, 2)}
              </pre>
            </details>
          )}
          <div className={s.list}>
            <div className={s.list_header}>
              <h2>
                <Trans i18nKey={"admin.sections.sections"} />
              </h2>
              <PrettyButton
                variant={"primary"}
                text={t("admin.sections.add")}
                onClick={() => handleAddItem("section")}
              />
            </div>
            {course?.sections.length > 0 ? (
              course.sections.map((section: any) => (
                <EditSection
                  key={section.id}
                  section={section}
                  moveSectionUp={() => moveSectionUp(section.id)}
                  moveSectionDown={() => moveSectionDown(section.id)}
                  setCourse={setCourse}
                  handleDelete={() => handleDeleteItem("section", section.id)}
                >
                  <div className={s.inner_list}>
                    <div className={s.list_header}>
                      <h2>
                        <Trans i18nKey={"admin.lessons.lessons"} />
                      </h2>
                      <PrettyButton
                        variant={"primary"}
                        text={t("admin.lessons.add")}
                        onClick={() => handleAddItem("lesson", section.id)}
                      />
                    </div>
                    {section.lessons.length > 0 ? (
                      section.lessons.map((lesson: any, index: number) => (
                        <EditLesson
                          moveLessonUp={() =>
                            moveLessonUp(section.id, lesson.id)
                          }
                          moveLessonDown={() =>
                            moveLessonDown(section.id, lesson.id)
                          }
                          key={index}
                          section={section}
                          lesson={lesson}
                          setCourse={setCourse}
                          handleDelete={() =>
                            handleDeleteItem("lesson", section.id, lesson.id)
                          }
                        />
                      ))
                    ) : (
                      <div>
                        <Trans i18nKey={"admin.sections.noLessons"} />
                      </div>
                    )}
                  </div>
                </EditSection>
              ))
            ) : (
              <div>
                <Trans i18nKey={"admin.courses.noSections"} />
              </div>
            )}
          </div>
          <DetailBottom
            deleteLabel={"admin.courses.delete"}
            handleSave={handleSave}
            handleDelete={() => handleDeleteItem("course")}
          />
        </>
      )}
    </div>
  );
};

export default CourseDetail;
