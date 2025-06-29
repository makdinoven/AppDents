import s from "./DetailPage.module.scss";
import { useNavigate, useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import EditSection from "../modules/EditSection/EditSection.tsx";
import EditLesson from "../modules/EditLesson/EditLesson.tsx";
import PrettyButton from "../../../components/ui/PrettyButton/PrettyButton.tsx";
import Loader from "../../../components/ui/Loader/Loader.tsx";
import { Trans } from "react-i18next";
import { t } from "i18next";
import EditCourse from "../modules/EditCourse/EditCourse.tsx";
import { adminApi } from "../../../api/adminApi/adminApi.ts";
import DetailHeader from "../modules/common/DetailHeader/DetailHeader.tsx";
import DetailBottom from "../modules/common/DetailBottom/DetailBottom.tsx";
import {
  denormalizeCourse,
  normalizeCourse,
} from "../../../common/helpers/helpers.ts";
import ErrorIcon from "../../../assets/icons/ErrorIcon.tsx";
import { Alert } from "../../../components/ui/Alert/Alert.tsx";

const CourseDetail = () => {
  const { courseId } = useParams();
  const [course, setCourse] = useState<any | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (courseId) {
      fetchCourseData();
    }
  }, [courseId]);

  const fetchCourseData = async () => {
    try {
      const res = await adminApi.getCourse(courseId);
      setCourse(normalizeCourse(res.data));
    } catch (error: any) {
      Alert(
        `Error fetching course data, error message: ${error.message}`,
        <ErrorIcon />
      );
    }
  };

  const updateCourseState = (callback: (prev: any) => any) => {
    setCourse((prev: any) => (prev ? callback(prev) : prev));
  };

  const handleAddItem = (
    itemType: "section" | "lesson",
    sectionId?: number
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
              : section
          ),
        };
      }
      return prev;
    });
  };

  const handleDeleteItem = (
    itemType: "course" | "section" | "lesson",
    sectionId?: number,
    lessonId?: number
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
                    (l: any) => l.id !== lessonId
                  ),
                }
              : section
          ),
        };
      }
      return prev;
    });
  };

  const handleDeleteCourse = async () => {
    try {
      await adminApi.deleteCourse(courseId);
      navigate(-1);
    } catch (error) {
      console.error("Error deleting course:", error);
    }
  };

  const handleSave = async () => {
    try {
      await adminApi.updateCourse(courseId, denormalizeCourse(course));
      navigate(-1);
    } catch (error) {
      Alert(`Error updating course data`, <ErrorIcon />);
    }
  };

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
