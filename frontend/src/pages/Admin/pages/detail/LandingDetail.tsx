import s from "./DetailPage.module.scss";
import EditLanding from "../modules/EditLanding/EditLanding.tsx";
import DetailHeader from "../modules/common/DetailHeader/DetailHeader.tsx";
import DetailBottom from "../modules/common/DetailBottom/DetailBottom.tsx";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Trans } from "react-i18next";
import PrettyButton from "../../../../shared/components/ui/PrettyButton/PrettyButton.tsx";
import { t } from "i18next";
import EditLesson from "../modules/EditLesson/EditLesson.tsx";
import Loader from "../../../../shared/components/ui/Loader/Loader.tsx";
import { adminApi } from "../../../../shared/api/adminApi/adminApi.ts";
import { mainApi } from "../../../../shared/api/mainApi/mainApi.ts";
import {
  denormalizeLessons,
  normalizeLessons,
} from "../../../../shared/common/helpers/helpers.ts";
import { ErrorIcon } from "../../../../shared/assets/icons";
import { Alert } from "../../../../shared/components/ui/Alert/Alert.tsx";
import { CheckMark } from "../../../../shared/assets/icons";

const LandingDetail = () => {
  const { id } = useParams();
  const [loading, setLoading] = useState(true);
  const [landing, setLanding] = useState<any | null>(null);
  const [authors, setAuthors] = useState<any | null>(null);
  const [tags, setTags] = useState<any | null>(null);
  const [courses, setCourses] = useState<any | null>(null);
  const navigate = useNavigate();
  const [fixLoading, setFixLoading] = useState(false);
  const [fixTaskId, setFixTaskId] = useState<string | null>(null);
  const [fixTaskState, setFixTaskState] = useState<string | null>(null);
  const [fixResult, setFixResult] = useState<any | null>(null);
  const [fixMeta, setFixMeta] = useState<any | null>(null);

  useEffect(() => {
    if (id) {
      fetchAllData();
    }
  }, [id]);

  const fetchAllData = async () => {
    setLoading(true);
    try {
      const [landingRes, tagsRes, coursesRes, authorsRes] = await Promise.all([
        adminApi.getLanding(id),
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
        <ErrorIcon />,
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
      await adminApi.deleteLanding(id);
      navigate(-1);
    } catch (error) {
      console.error("Error deleting course:", error);
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

  const handleSave = async () => {
    const denormalizedLanding = {
      ...landing,
      lessons_info: denormalizeLessons(landing?.lessons_info),
      page_name: landing.page_name?.trim(),
    };
    try {
      await adminApi.updateLanding(id, denormalizedLanding);
      navigate(-1);
    } catch (error) {
      console.error("Error updating course:", error);
    }
  };

  const fixAllVideos = async () => {
    if (!id) return;
    try {
      setFixLoading(true);
      setFixResult(null);
      setFixTaskState(null);
      const res = await adminApi.runVideoMaintenanceForLanding({
        landing_id: Number(id),
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
    }, 10000);
    return () => clearInterval(interval);
  }, [fixTaskId]);

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
