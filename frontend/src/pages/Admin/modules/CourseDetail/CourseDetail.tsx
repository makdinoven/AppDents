import s from "./CourseDetail.module.scss";
import { useParams, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { adminApi } from "../../../../api/adminApi/adminApi.ts";
import EditSection from "../EditSection/EditSection.tsx";
import EditModule from "../EditModule/EditModule.tsx";
import { CourseType, ModuleType, SectionType } from "../../types.ts";
import PrettyButton from "../../../../components/ui/PrettyButton/PrettyButton.tsx";
import Loader from "../../../../components/ui/Loader/Loader.tsx";
import EditLanding from "../EditLanding/EditLanding.tsx";
import { Trans } from "react-i18next";
import { t } from "i18next";
import EditCourse from "../EditCourse/EditCourse.tsx";

const initialSection = {
  name: "New Section",
};

const initialModule = {
  title: "New Module",
  short_video_link: "",
  full_video_link: "",
  program_text: "",
  duration: "",
};

const CourseDetail = () => {
  const navigate = useNavigate();
  const navigateBack = () => navigate(-1);
  const { courseId } = useParams();
  const [course, setCourse] = useState<CourseType | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    if (courseId) {
      fetchCourseData();
    }
  }, [courseId]);

  const fetchCourseData = async () => {
    try {
      const res = await adminApi.getCourse(courseId);
      setCourse(res.data);
    } catch (error) {
      console.error("Error fetching course:", error);
    }
  };

  const deleteItem = (
    itemType: "course" | "section" | "module",
    sectionId?: number,
    moduleId?: number,
  ) => {
    const isConfirmed = confirm(
      `Are you sure you want to delete this ${itemType}?`,
    );

    if (isConfirmed) {
      if (itemType === "course") {
        handleDeleteCourse();
      } else if (itemType === "section") {
        handleDeleteSection(sectionId!);
      } else if (itemType === "module") {
        handleDeleteModule(sectionId!, moduleId!);
      }
    }
  };

  const handleAddSection = async () => {
    setLoading(true);
    try {
      const response = await adminApi.addCourseSection(
        courseId,
        initialSection,
      );
      updateStateWithNewItem("section", response.data);
      setLoading(false);
    } catch (error) {
      console.error("Error adding section:", error);
      setLoading(false);
    }
  };

  const handleAddModule = async (sectionId: number) => {
    try {
      const response = await adminApi.addCourseModule(
        courseId,
        sectionId,
        initialModule,
      );
      updateStateWithNewItem("module", response.data, sectionId);
    } catch (error) {
      console.error("Error adding module:", error);
    }
  };

  const handleDeleteCourse = async () => {
    try {
      await adminApi.deleteCourse(courseId);
      navigateBack();
    } catch (error) {
      console.error("Error deleting course:", error);
    }
  };

  const handleDeleteSection = async (sectionId: number) => {
    try {
      await adminApi.deleteCourseSection(courseId, sectionId);
      updateStateAfterDelete("section", sectionId);
    } catch (error) {
      console.error("Error deleting section:", error);
    }
  };

  const handleDeleteModule = async (sectionId: number, moduleId: number) => {
    try {
      await adminApi.deleteCourseModule(courseId, sectionId, moduleId);
      updateStateAfterDelete("module", sectionId, moduleId);
    } catch (error) {
      console.error("Error deleting module:", error);
    }
  };

  const updateStateAfterDelete = (
    itemType: "section" | "module",
    sectionId: number,
    moduleId?: number,
  ) => {
    setCourse((prev) => {
      if (!prev) return prev;

      if (itemType === "section") {
        return {
          ...prev,
          sections: prev.sections.filter((section) => section.id !== sectionId),
        };
      } else if (itemType === "module" && moduleId) {
        const updatedSections = prev.sections.map((section) =>
          section.id === sectionId
            ? {
                ...section,
                modules: section.modules.filter(
                  (module) => module.id !== moduleId,
                ),
              }
            : section,
        );
        return { ...prev, sections: updatedSections };
      }
      return prev;
    });
  };

  const updateStateWithNewItem = (
    itemType: "section" | "module",
    newItem: any,
    sectionId?: number,
  ) => {
    setCourse((prev) => {
      if (!prev) return prev;

      if (itemType === "section") {
        return { ...prev, sections: [...prev.sections, newItem] };
      } else if (itemType === "module" && sectionId) {
        const updatedSections = prev.sections.map((section) =>
          section.id === sectionId
            ? { ...section, modules: [...section.modules, newItem] }
            : section,
        );
        return { ...prev, sections: updatedSections };
      }
      return prev;
    });
  };

  const handleSave = async () => {
    try {
      await adminApi.updateCourse(courseId, course);
      navigateBack();
    } catch (error) {
      console.error("Error updating course:", error);
    }
  };

  useEffect(() => {
    console.log(course);
  }, [course]);

  return (
    <div className={s.course_detail}>
      <div className={s.course_detail_header}>
        <PrettyButton text={"back"} onClick={() => navigateBack()} />
      </div>
      {!course ? (
        <Loader />
      ) : (
        <>
          <EditCourse course={course} setCourse={setCourse} />
          <EditLanding landing={course.landing} setCourse={setCourse} />
          <div className={s.sections}>
            <div className={s.sections_header}>
              <h2>
                <Trans i18nKey={"admin.sections"} />
              </h2>
              <PrettyButton
                variant={"primary"}
                text={t("admin.sections.add")}
                loading={loading}
                onClick={() => handleAddSection()}
              />
            </div>
            {course.sections.length > 0 ? (
              course.sections.map((section: SectionType, index: number) => (
                <EditSection
                  key={section.id}
                  section={section}
                  index={index + 1}
                  setCourse={setCourse}
                  handleDelete={() => deleteItem("section", section.id)}
                >
                  <div className={s.modules}>
                    <div className={s.sections_header}>
                      <h2>
                        <Trans i18nKey={"admin.modules"} />
                      </h2>
                      <PrettyButton
                        variant={"primary"}
                        loading={loading}
                        text={t("admin.modules.add")}
                        onClick={() => handleAddModule(section.id)}
                      />
                    </div>
                    {section.modules.length > 0 ? (
                      section.modules.map(
                        (module: ModuleType, index: number) => (
                          <EditModule
                            key={module.id}
                            section={section}
                            module={module}
                            index={index + 1}
                            setCourse={setCourse}
                            handleDelete={() =>
                              deleteItem("module", section.id, module.id)
                            }
                          />
                        ),
                      )
                    ) : (
                      <div>
                        <Trans i18nKey={"admin.sections.noModules"} />
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
          <div className={s.course_detail_bottom}>
            <PrettyButton
              variant={"primary"}
              text={t("admin.save")}
              onClick={handleSave}
            />
            <PrettyButton
              variant={"danger"}
              text={t("admin.courses.delete")}
              onClick={() => deleteItem("course")}
            />
          </div>
        </>
      )}
    </div>
  );
};

export default CourseDetail;
