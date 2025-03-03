import s from "./CourseDetail.module.scss";
import { useNavigate, useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import EditSection from "../EditSection/EditSection.tsx";
import EditLesson from "../EditLesson/EditLesson.tsx";
import PrettyButton from "../../../../components/ui/PrettyButton/PrettyButton.tsx";
import Loader from "../../../../components/ui/Loader/Loader.tsx";
import { Trans } from "react-i18next";
import { t } from "i18next";
import EditCourse from "../EditCourse/EditCourse.tsx";
import { adminApi } from "../../../../api/adminApi/adminApi.ts";
import DetailHeader from "../common/DetailHeader/DetailHeader.tsx";
import DetailBottom from "../common/DetailBottom/DetailBottom.tsx";

const initialCourse = {
  course_name: "initialCourse",
  course_description: "",
  sections: [
    {
      1: {
        section_name: "Invisalign Online Mentoring Program by Doctor Paiva",
        lessons: [
          {
            video_link: "https://play.boomstream.com/2TVBV98F",
            lesson_name: "Introducing Invisalign® System",
          },
        ],
      },
    },
    {
      2: {
        section_name: "2 section",
        lessons: [
          {
            video_link: "https://play.boomstream.com/2TVBV98F",
            lesson_name: "Introducing Invisalign® System",
          },
        ],
      },
    },
  ],
};

const CourseDetail = () => {
  const { courseId } = useParams();
  const [course, setCourse] = useState<any | null>(null);
  // const [loading, setLoading] = useState<boolean>(false);
  const navigate = useNavigate();

  useEffect(() => {
    if (courseId) {
      // fetchCourseData();
      const normalizedCourse = normalizeCourse(initialCourse);
      setCourse(normalizedCourse);
      // setLoading(false);
    }
  }, [courseId]);

  const normalizeCourse = (course: any) => {
    return {
      ...course,
      sections: course.sections.map((sectionObj: any) => {
        const sectionId = Object.keys(sectionObj)[0];
        return {
          id: Number(sectionId),
          section_name: sectionObj[sectionId].section_name,
          lessons: sectionObj[sectionId].lessons.map(
            (lesson: any, index: number) => ({
              id: index + 1,
              lesson_name: lesson.lesson_name,
              video_link: lesson.video_link,
            }),
          ),
        };
      }),
    };
  };

  const denormalizeCourse = (course: any) => {
    return {
      ...course,
      sections: course.sections.map((section: any) => ({
        [section.id]: {
          section_name: section.section_name,
          lessons: section.lessons.map((lesson: any) => {
            const { id, ...rest } = lesson;
            return rest;
          }),
        },
      })),
    };
  };

  // const fetchCourseData = async () => {
  //   try {
  //     const res = await adminApi.getCourse(courseId);
  //     setCourse(res.data);
  //   } catch (error) {
  //     console.error("Error fetching course:", error);
  //   }
  // };

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
      await adminApi.deleteCourse(courseId);
      navigate(-1);
    } catch (error) {
      console.error("Error deleting course:", error);
    }
  };

  useEffect(() => {
    console.log(course);
  }, [course]);

  const handleSave = async () => {
    console.log("handleSave", denormalizeCourse(course));

    // try {
    //   await adminApi.updateCourse(courseId, course);
    //   navigateBack();
    // } catch (error) {
    //   console.error("Error updating course:", error);
    // }
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
                <Trans i18nKey={"admin.sections"} />
              </h2>
              <PrettyButton
                variant={"primary"}
                text={t("admin.sections.add")}
                onClick={() => handleAddItem("section")}
              />
            </div>
            {course.sections.length > 0 ? (
              course.sections.map((section: any) => (
                <EditSection
                  key={section.id}
                  section={section}
                  setCourse={setCourse}
                  handleDelete={() => handleDeleteItem("section", section.id)}
                >
                  <div className={s.inner_list}>
                    <div className={s.list_header}>
                      <h2>
                        <Trans i18nKey={"admin.lessons"} />
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
